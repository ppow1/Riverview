"""Fixed-policy local runner for Riverview Relay.

Version: 0.5.2
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.relay import ClaimedWork, RelayStore


@dataclass(frozen=True, slots=True)
class ActionDefinition:
    action_type: str
    action_version: str
    command_path: str
    command_sha256: str
    hard_timeout_seconds: int


class RestrictedRunner:
    """Execute only explicitly implemented actions whose source hash matches policy."""

    def __init__(self, repository: Path, worker_id: str, heartbeat_seconds: float = 0.5) -> None:
        self.repository = repository.resolve()
        self.worker_id = worker_id
        self.heartbeat_seconds = heartbeat_seconds
        self.store = RelayStore()

    def run_once(self) -> dict[str, Any] | None:
        work = self.store.claim(self.worker_id, 10)
        if work is None:
            return None
        try:
            definition = self._definition(work)
            command = self._command(work, definition)
            return self._execute(work, command)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            self._fail(work.work_order_id, "RIV-RUN-0001", str(exc), timed_out=False)
            return {"status": "failed", "checkpoint_id": "RIV-RUN-0001"}

    def _definition(self, work: ClaimedWork) -> ActionDefinition:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT action_type,action_version,command_path,command_sha256,hard_timeout_seconds FROM approved_actions WHERE action_type=%s AND action_version=%s AND enabled=true",(work.action_type,work.action_version))
            row = cursor.fetchone()
        if not row or not row[3]:
            raise RuntimeError("RIV-RUN-0001: Action definition is absent, disabled, unversioned, or unhashed.")
        return ActionDefinition(*row)

    def _command(self, work: ClaimedWork, definition: ActionDefinition) -> list[str]:
        path = (self.repository / definition.command_path).resolve()
        tools_root = (self.repository / "tools" / "powershell").resolve()
        if tools_root not in path.parents or not path.is_file():
            raise RuntimeError("RIV-RUN-0002: Registered command escaped the repository tools boundary.")
        if hashlib.sha256(path.read_bytes()).hexdigest() != definition.command_sha256:
            raise RuntimeError("RIV-RUN-0003: Registered command hash mismatch.")
        delay = work.parameters.get("delay_seconds")
        if work.action_type not in {"relay.noop", "relay.timeout_probe"} or not isinstance(delay, int) or isinstance(delay, bool) or not 1 <= delay <= 5:
            raise ValueError("RIV-RUN-0004: Action parameters failed the fixed runner adapter.")
        executable = shutil.which("pwsh")
        if executable is None:
            raise RuntimeError("RIV-RUN-0001: pwsh executable was not found.")
        return [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(path), "-DelaySeconds", str(delay)]

    def _execute(self, work: ClaimedWork, command: list[str]) -> dict[str, Any]:
        process = subprocess.Popen(
            command, cwd=self.repository, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stopped = threading.Event()
        heartbeat_error: list[str] = []

        def heartbeat() -> None:
            while not stopped.wait(self.heartbeat_seconds):
                try:
                    self.store.heartbeat(work.work_order_id, self.worker_id, 10)
                except RuntimeError as exc:
                    heartbeat_error.append(str(exc))
                    return

        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        try:
            stdout, stderr = process.communicate(timeout=work.hard_timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            self._fail(work.work_order_id, "RIV-RUN-0005", "Hard timeout exceeded.", timed_out=True)
            return {"status": "timed_out", "checkpoint_id": "RIV-RUN-0005", "stdout": stdout[-4000:], "stderr": stderr[-4000:]}
        finally:
            stopped.set()
            thread.join(timeout=2)
        if heartbeat_error:
            raise RuntimeError(f"RIV-RUN-0006: Heartbeat failed: {heartbeat_error[-1]}")
        if process.returncode != 0:
            self._fail(work.work_order_id, "RIV-RUN-0007", f"Process exit code {process.returncode}.", timed_out=False)
            return {"status": "failed", "checkpoint_id": "RIV-RUN-0007", "stdout": stdout[-4000:], "stderr": stderr[-4000:]}
        report = {"status": "succeeded", "exit_code": process.returncode, "stdout": stdout[-4000:], "stderr": stderr[-4000:]}
        self.store.complete(work.work_order_id, self.worker_id, report)
        return report

    def _fail(self, order_id: UUID, checkpoint: str, reason: str, timed_out: bool) -> None:
        state = "timed_out" if timed_out else "failed"
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE work_orders SET status=%s,error_checkpoint=%s,result_report=%s::jsonb,finished_at=now(),lease_expires_at=NULL,updated_at=now() WHERE work_order_id=%s AND lease_owner=%s AND status IN('claimed','running')",(state,checkpoint,json.dumps({"status":state,"reason":reason}),order_id,self.worker_id))
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-RUN-0008: Runner could not record terminal state.")
            cursor.execute("UPDATE work_order_attempts SET finished_at=now(),exit_code=%s WHERE work_order_id=%s AND worker_id=%s AND finished_at IS NULL",(124 if timed_out else 1,order_id,self.worker_id))
            cursor.execute("INSERT INTO steward_escalations(escalation_id,work_order_id,checkpoint_id,reason,state)VALUES(%s,%s,%s,%s,'open')",(uuid4(),order_id,checkpoint,reason))