"""External recovery boundary for the persistent CME runtime.

The CME process is intentionally supervised outside its own heartbeat loop.
This prevents a dead process or an unhandled listener failure from remaining
stale indefinitely, while preserving River cursor and business authority in
PostgreSQL.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import psycopg

from riverview.autonomy.runtime import HEARTBEAT_FRESHNESS_SECONDS, CMEStatusStore
from riverview.diagnostics import DiagnosticEvent, DiagnosticStore, RecoveryState, Severity


class CMESupervisor:
    """Keep one CME child alive and recover it from exit or stale heartbeat."""

    def __init__(
        self,
        *,
        repository: Path | None = None,
        poll_seconds: float = 1.0,
        stale_grace_seconds: float = 10.0,
        max_backoff_seconds: float = 30.0,
        process_factory: Callable[[list[str], Path, dict[str, str]], Any] | None = None,
        status: CMEStatusStore | None = None,
        diagnostics: DiagnosticStore | None = None,
    ) -> None:
        if poll_seconds <= 0 or stale_grace_seconds <= HEARTBEAT_FRESHNESS_SECONDS:
            raise ValueError("RIV-GRC-0008: supervisor timing bounds are invalid.")
        self.repository = (repository or Path.cwd()).resolve()
        self.poll_seconds = poll_seconds
        self.stale_grace_seconds = stale_grace_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.process_factory = process_factory or self._spawn
        self.status = status or CMEStatusStore()
        self.diagnostics = diagnostics or DiagnosticStore()
        self.stop_requested = False

    @staticmethod
    def _spawn(command: list[str], cwd: Path, environment: dict[str, str]) -> subprocess.Popen[bytes]:
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        return subprocess.Popen(command, cwd=cwd, env=environment, creationflags=flags)

    def _record(self, failure_class: str, summary: str) -> None:
        self.diagnostics.emit(DiagnosticEvent(
            checkpoint_id="RIV-GRC-0008", component="riverview.autonomy.supervisor",
            operation="cme_recovery", severity=Severity.ERROR, failure_class=failure_class,
            summary=summary[:500], cookbook_entry="CB-RIV-GRC-0008",
            evidence_refs=("cme://runtime-status",), recovery_state=RecoveryState.UNVERIFIED,
        ))

    def _command(self) -> list[str]:
        return [sys.executable, "-m", "riverview.autonomy.live_service"]

    def _environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        source = str(self.repository / "src")
        environment["PYTHONPATH"] = source + os.pathsep + environment.get("PYTHONPATH", "")
        return environment

    def run(self) -> None:
        lock_path = self.repository / "runtime" / "cme_supervisor.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_handle = lock_path.open("a+")
        try:
            if os.name == "nt":
                import msvcrt

                lock_handle.seek(0)
                lock_handle.write("0")
                lock_handle.flush()
                try:
                    msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError:
                    return
            child: Any = None
            backoff = 1.0
            child_started_at = 0.0
            while not self.stop_requested:
                if child is None or child.poll() is not None:
                    if child is not None:
                        self._record("consumer-exited", f"CME child exited with code {child.returncode}; recovering.")
                    time.sleep(backoff if child is not None else 0)
                    if self.stop_requested:
                        break
                    try:
                        child = self.process_factory(self._command(), self.repository, self._environment())
                    except (OSError, RuntimeError, psycopg.Error) as exc:
                        self._record("supervisor-spawn-failure", f"CME child spawn failed: {type(exc).__name__}: {exc}")
                        child = None
                        time.sleep(backoff)
                        backoff = min(self.max_backoff_seconds, backoff * 2)
                        continue
                    child_started_at = time.monotonic()
                    backoff = min(self.max_backoff_seconds, backoff * 2)
                    continue
                try:
                    snapshot = self.status.read()
                except (OSError, RuntimeError, psycopg.Error) as exc:
                    self._record("status-read-failure", f"CME status probe failed: {type(exc).__name__}: {exc}")
                    time.sleep(self.poll_seconds)
                    continue
                within_startup_grace = time.monotonic() - child_started_at < self.stale_grace_seconds
                if snapshot is not None and not within_startup_grace and snapshot["heartbeat_age_seconds"] > self.stale_grace_seconds:
                    self._record("heartbeat-stale", "CME heartbeat exceeded the external recovery threshold.")
                    child.terminate()
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        child.kill()
                    child = None
                    continue
                if snapshot is not None and snapshot["heartbeat_health"] == "HEALTHY":
                    backoff = 1.0
                time.sleep(self.poll_seconds)
        finally:
            if os.name == "nt":
                try:
                    import msvcrt

                    lock_handle.seek(0)
                    msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            lock_handle.close()

    def stop(self) -> None:
        self.stop_requested = True


def main() -> None:
    supervisor = CMESupervisor()
    try:
        supervisor.run()
    except KeyboardInterrupt:
        supervisor.stop()


if __name__ == "__main__":
    main()
