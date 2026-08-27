"""Unified Riverview runtime lifecycle supervisor.

Version: 1.0.0

The supervisor owns service identity, dependency order, duplicate prevention,
bounded recovery, and safe status evidence. Component supervisors (notably the
CME supervisor) remain separate children and retain their internal authority.
Secrets are loaded only into a child environment and are never written to
status, logs, command lines, or River.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class ServiceSpec:
    service_id: str
    command: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    port: int | None = None
    health_url: str | None = None
    process_match: str = ""
    secret_file: str | None = None
    secret_env: str | None = None
    environment: dict[str, str] = field(default_factory=dict)
    restart: bool = True
    startup_timeout: float = 8.0


@dataclass(slots=True)
class ServiceState:
    spec: ServiceSpec
    status: str = "stopped"
    pid: int | None = None
    adopted: bool = False
    restart_count: int = 0
    last_failure: str | None = None
    last_change: str = field(default_factory=_now)
    backoff_until: float = 0.0
    process: subprocess.Popen[bytes] | None = None
    stdout_handle: Any | None = None
    stderr_handle: Any | None = None
    started_monotonic: float = 0.0
    enabled: bool = True


class ServiceRegistry:
    """Load the single declarative service registry used by the supervisor."""

    def __init__(self, specs: tuple[ServiceSpec, ...]) -> None:
        self.specs = {spec.service_id: spec for spec in specs}
        if len(self.specs) != len(specs):
            raise ValueError("RIV-RUN-0001: duplicate service identity.")
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        for spec in self.specs.values():
            missing = set(spec.dependencies) - self.specs.keys()
            if missing:
                raise ValueError(f"RIV-RUN-0001: {spec.service_id} has missing dependencies.")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(service_id: str) -> None:
            if service_id in visiting:
                raise ValueError("RIV-RUN-0001: service dependency cycle.")
            if service_id in visited:
                return
            visiting.add(service_id)
            for dependency in self.specs[service_id].dependencies:
                visit(dependency)
            visiting.remove(service_id)
            visited.add(service_id)

        for service_id in self.specs:
            visit(service_id)

    def ordered(self) -> tuple[ServiceSpec, ...]:
        result: list[ServiceSpec] = []
        visited: set[str] = set()

        def visit(spec: ServiceSpec) -> None:
            if spec.service_id in visited:
                return
            for dependency in spec.dependencies:
                visit(self.specs[dependency])
            visited.add(spec.service_id)
            result.append(spec)

        for spec in self.specs.values():
            visit(spec)
        return tuple(result)

    @classmethod
    def from_file(cls, path: Path) -> ServiceRegistry:
        data = json.loads(path.read_text(encoding="utf-8"))
        specs = tuple(
            ServiceSpec(
                **{
                    **item,
                    "command": tuple(item["command"]),
                    "dependencies": tuple(item.get("dependencies", ())),
                }
            )
            for item in data["services"]
        )
        return cls(specs)


class RuntimeSupervisor:
    """Own the top-level Riverview service lifecycle without merging services."""

    def __init__(
        self,
        repository: Path,
        registry_path: Path,
        *,
        status_path: Path | None = None,
        poll_seconds: float = 1.0,
        process_factory: Any | None = None,
    ) -> None:
        if poll_seconds <= 0:
            raise ValueError("RIV-RUN-0001: poll_seconds must be positive.")
        self.repository = repository.resolve()
        self.registry = ServiceRegistry.from_file(registry_path)
        self.status_path = (
            status_path or self.repository / "runtime" / "riverview-supervisor" / "status.json"
        )
        self.poll_seconds = poll_seconds
        self.process_factory = process_factory or subprocess.Popen
        self.states = {spec.service_id: ServiceState(spec) for spec in self.registry.ordered()}
        self.stop_requested = False
        self.started_at = _now()

    def _processes(self) -> list[dict[str, Any]]:
        try:
            import psutil  # type: ignore[import-not-found]
        except ImportError:
            if os.name != "nt":
                return []
            try:
                command = [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress",
                ]
                output = subprocess.run(
                    command, capture_output=True, text=True, timeout=3, check=True
                ).stdout
                rows = json.loads(output) if output.strip() else []
                if isinstance(rows, dict):
                    rows = [rows]
                return [
                    {
                        "pid": row.get("ProcessId"),
                        "ppid": row.get("ParentProcessId"),
                        "executable": row.get("ExecutablePath") or "",
                        "cwd": "",
                        "cmdline": row.get("CommandLine") or "",
                    }
                    for row in rows
                ]
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
                return []
        result = []
        for process in psutil.process_iter(["pid", "ppid", "cmdline", "exe"]):
            try:
                result.append(
                    {
                        "pid": process.info["pid"],
                        "ppid": process.info["ppid"],
                        "executable": process.info.get("exe") or "",
                        "cmdline": " ".join(process.info["cmdline"] or []),
                        "cwd": process.info.get("cwd") or "",
                    }
                )
            except (psutil.Error, TypeError):
                continue
        return result

    def _adopt(self, state: ServiceState) -> bool:
        if state.spec.port is not None and state.spec.service_id != "spatial" and self._healthy(state.spec):
            listener_pids = self._listener_pids(state.spec.port)
            process_by_pid = {
                int(process["pid"]): process
                for process in self._processes()
                if process.get("pid") is not None
            }
            foreign_pids = [
                pid
                for pid in listener_pids
                if pid in process_by_pid and not self._process_belongs_to_repository(process_by_pid[pid])
            ]
            owned_pids = [pid for pid in listener_pids if pid not in foreign_pids]
            if foreign_pids:
                state.status = "failed"
                state.last_failure = "foreign-root-listener"
                state.last_change = _now()
                return True
            if len(owned_pids) > 1:
                state.status = "failed"
                state.last_failure = "duplicate-listener"
                state.last_change = _now()
                return True
            state.pid = owned_pids[0] if owned_pids else None
            state.adopted = True
            state.status = "running" if self._healthy(state.spec) else "starting"
            state.last_change = _now()
            return True
        if not state.spec.process_match:
            return False
        matches = [
            process
            for process in self._processes()
            if self._process_matches(state.spec, process)
            and self._process_belongs_to_repository(process)
        ]
        match_pids = {int(process["pid"]) for process in matches}
        roots = [process for process in matches if int(process.get("ppid") or 0) not in match_pids]
        if len(roots) > 1:
            state.status = "failed"
            state.last_failure = "duplicate-process"
            state.last_change = _now()
            return True
        if roots:
            state.pid = int(roots[0]["pid"])
            state.adopted = True
            state.status = "running" if self._healthy(state.spec) else "starting"
            state.last_change = _now()
            return True
        return False

    @staticmethod
    def _terminate_process_tree(pid: int) -> None:
        if pid <= 0 or pid == os.getpid():
            return
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False, capture_output=True, text=True)
        else:
            try:
                os.kill(pid, 15)
            except OSError:
                pass

    def _recycle_service(self, service_id: str) -> dict[str, Any]:
        state = self.states.get(service_id)
        if state is None:
            raise ValueError("RIV-RUN-0001: unknown managed service.")
        if service_id not in self.states:
            raise ValueError("RIV-RUN-0001: only registered production service recycle is enabled.")
        matches = [p for p in self._processes() if self._process_matches(state.spec, p) and self._process_belongs_to_repository(p)]
        match_pids = {int(process["pid"]) for process in matches}
        roots = [process for process in matches if int(process.get("ppid") or 0) not in match_pids]
        if len(roots) != 1:
            raise RuntimeError("RIV-RUN-0001: service ownership is ambiguous; refusing recycle.")
        owner = int(roots[0]["pid"])
        self._terminate_process_tree(int(owner))
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if not [p for p in self._processes() if self._process_matches(state.spec, p)]:
                break
            time.sleep(0.2)
        if [p for p in self._processes() if self._process_matches(state.spec, p)]:
            raise RuntimeError("RIV-RUN-0001: service descendants remained after bounded recycle.")
        state.process = None
        state.pid = None
        state.adopted = False
        state.status = "stopped"
        state.last_failure = None
        state.backoff_until = 0.0
        return {"service_id": service_id, "status": "stopped", "old_owner_pid": owner}

    def _set_service_enabled(self, service_id: str, enabled: bool) -> dict[str, Any]:
        state = self.states.get(service_id)
        if state is None:
            raise ValueError("RIV-RUN-0001: unknown managed service.")
        if not enabled:
            self._recycle_service(service_id)
        state.enabled = enabled
        state.status = "stopped" if not enabled else "stopped"
        state.backoff_until = 0.0
        return {"service_id": service_id, "status": state.status, "enabled": enabled}

    def _process_control_requests(self) -> None:
        request_dir = self.repository / "runtime" / "riverview-supervisor" / "requests"
        result_dir = request_dir / "results"
        request_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)
        for request in sorted(request_dir.glob("*.json")):
            try:
                # Windows PowerShell 5 emits UTF-8 JSON with a BOM.  Accept
                # that encoding marker while keeping the operation allow-list
                # and service identity checks below authoritative.
                payload = json.loads(request.read_text(encoding="utf-8-sig"))
                if payload.get("operation") not in {"reload_service", "start_service", "stop_service"}:
                    raise ValueError("RIV-RUN-0001: unsupported supervisor operation.")
                service_id = str(payload.get("service_id", ""))
                if payload["operation"] == "reload_service":
                    response = {"ok": True, **self._recycle_service(service_id)}
                else:
                    response = {"ok": True, **self._set_service_enabled(service_id, payload["operation"] == "start_service")}
            except (OSError, TypeError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
                response = {"ok": False, "error": str(exc)[:500]}
            (result_dir / request.name).write_text(json.dumps(response), encoding="utf-8")
            request.unlink(missing_ok=True)

    @staticmethod
    def _process_matches(spec: ServiceSpec, process: dict[str, Any]) -> bool:
        """Match an owned service command, not arbitrary diagnostic command text."""
        command_line = str(process.get("cmdline") or "")
        marker = spec.process_match
        if marker.startswith("riverview."):
            return bool(re.search(rf"(?<![A-Za-z0-9_.-])-m\s+{re.escape(marker)}(?:\s|$)", command_line))
        return marker in command_line

    def _process_belongs_to_repository(self, process: dict[str, Any]) -> bool:
        """Do not adopt a same-command service from another checkout."""
        cwd = str(process.get("cwd") or "")
        return not cwd or Path(cwd).resolve() == self.repository

    @staticmethod
    def _listener_pids(port: int) -> list[int]:
        if os.name != "nt":
            return []
        try:
            command = [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                f"$x=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort {port} -State Listen -ErrorAction SilentlyContinue; if($x){{($x | Select-Object -ExpandProperty OwningProcess)}}",
            ]
            output = subprocess.run(
                command, capture_output=True, text=True, timeout=3, check=True
            ).stdout.strip()
            return [int(item) for item in output.splitlines() if item.strip()]
        except (OSError, subprocess.SubprocessError, ValueError):
            return []

    def _healthy(self, spec: ServiceSpec) -> bool:
        if spec.service_id == "cme-supervisor":
            try:
                from riverview.autonomy.runtime import CMEStatusStore

                status = CMEStatusStore().read()
                return bool(status and status.get("heartbeat_health") == "HEALTHY")
            except (OSError, RuntimeError, TypeError, ValueError):
                return False
        if spec.port is not None:
            import socket

            with socket.socket() as sock:
                sock.settimeout(0.5)
                host = "192.168.1.88" if spec.service_id == "spatial" else "127.0.0.1"
                try:
                    sock.connect((host, spec.port))
                except OSError:
                    return False
        if spec.health_url:
            try:
                with urllib.request.urlopen(spec.health_url, timeout=15) as response:
                    return response.status == 200
            except (OSError, urllib.error.URLError):
                return False
        return True

    @staticmethod
    def _cme_recovering() -> bool:
        try:
            from riverview.autonomy.runtime import CMEStatusStore
            status = CMEStatusStore().read()
            return bool(status and status.get("current_state") in {"STARTING", "EVALUATING"})
        except (OSError, RuntimeError, TypeError, ValueError):
            return False

    def _environment(self, spec: ServiceSpec) -> dict[str, str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = (
            str(self.repository / "src") + os.pathsep + environment.get("PYTHONPATH", "")
        )
        if spec.secret_file and spec.secret_env:
            secret_path = Path(spec.secret_file)
            if not secret_path.is_file():
                raise RuntimeError(
                    f"RIV-RUN-0003: credential source unavailable for {spec.service_id}."
                )
            secret = secret_path.read_text(encoding="utf-8").strip()
            if not secret:
                raise RuntimeError(f"RIV-RUN-0003: credential source empty for {spec.service_id}.")
            environment[spec.secret_env] = secret
        environment.update(spec.environment)
        return environment

    def _spawn(self, state: ServiceState) -> None:
        spec = state.spec
        if self._adopt(state):
            return
        if not spec.restart and state.restart_count:
            state.status = "disabled"
            return
        try:
            log_dir = self.repository / "runtime" / "riverview-supervisor" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            stdout_handle = (log_dir / f"{spec.service_id}.stdout.log").open("ab")
            stderr_handle = (log_dir / f"{spec.service_id}.stderr.log").open("ab")
            command = [self._expand_command_item(item) for item in spec.command]
            process = self.process_factory(
                command,
                cwd=self.repository,
                env=self._environment(spec),
                stdout=stdout_handle,
                stderr=stderr_handle,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        except (OSError, RuntimeError) as exc:
            for handle in locals().get("stdout_handle"), locals().get("stderr_handle"):
                if handle is not None:
                    handle.close()
            state.status = "failed"
            state.last_failure = type(exc).__name__
            state.last_change = _now()
            state.restart_count += 1
            state.backoff_until = time.monotonic() + min(30.0, 2.0 ** min(state.restart_count, 4))
            return
        state.process = process
        state.stdout_handle = stdout_handle
        state.stderr_handle = stderr_handle
        state.pid = process.pid
        state.adopted = False
        state.status = "starting"
        state.last_change = _now()
        state.started_monotonic = time.monotonic()

    @staticmethod
    def _expand_command_item(item: str) -> str:
        expanded = os.path.expandvars(item)
        return re.sub(
            r"\$\{([^}]+)\}",
            lambda match: os.environ.get(match.group(1), match.group(0)),
            expanded,
        )

    def _refresh(self, state: ServiceState) -> None:
        if state.process is not None and state.process.poll() is not None:
            returncode = state.process.returncode
            state.process = None
            for handle in (state.stdout_handle, state.stderr_handle):
                if handle is not None:
                    handle.close()
            state.stdout_handle = None
            state.stderr_handle = None
            if self._adopt(state):
                state.restart_count = 0
                return
            state.status = "failed"
            state.last_failure = f"exit:{returncode}"
            state.last_change = _now()
            state.pid = None
            state.restart_count += 1
            state.backoff_until = time.monotonic() + min(30.0, 2.0 ** min(state.restart_count, 4))
            return
        if state.process is not None and state.status == "running" and not self._healthy(state.spec):
            if state.spec.service_id == "cme-supervisor" and self._cme_recovering():
                state.status = "starting"
                return
            if state.process.poll() is None:
                state.process.terminate()
            state.status = "failed"
            state.last_failure = "health-failed"
            state.last_change = _now()
            state.process = None
            state.pid = None
            state.restart_count += 1
            state.backoff_until = time.monotonic() + min(30.0, 2.0 ** min(state.restart_count, 4))
            return
        if state.adopted and state.status == "running":
            healthy = self._healthy(state.spec)
            if state.spec.process_match and state.spec.port is None:
                healthy = any(
                    self._process_matches(state.spec, process)
                    and int(process["pid"]) == state.pid
                    for process in self._processes()
                )
            if not healthy:
                if state.spec.service_id == "cme-supervisor" and self._cme_recovering():
                    state.status = "starting"
                    return
                state.status = "failed"
                state.last_failure = "adopted-process-unhealthy"
                state.last_change = _now()
                state.pid = None
                state.adopted = False
                state.restart_count += 1
                state.backoff_until = time.monotonic() + min(
                    30.0, 2.0 ** min(state.restart_count, 4)
                )
                return
        if (
            state.status == "starting"
            and state.started_monotonic
            and time.monotonic() - state.started_monotonic > state.spec.startup_timeout
            and not self._healthy(state.spec)
        ):
            if state.spec.service_id == "cme-supervisor" and self._cme_recovering():
                return
            if state.process is not None and state.process.poll() is None:
                state.process.terminate()
            state.status = "failed"
            state.last_failure = "startup-timeout"
            state.last_change = _now()
            state.process = None
            state.pid = None
            state.restart_count += 1
            state.backoff_until = time.monotonic() + min(30.0, 2.0 ** min(state.restart_count, 4))
            return
        if state.status in {"starting", "running"} and self._healthy(state.spec):
            state.status = "running"
            state.last_change = _now()
            state.last_failure = None
            if state.process is not None:
                state.restart_count = 0

    def reconcile_once(self) -> None:
        self._process_control_requests()
        for state in self.states.values():
            self._refresh(state)
        for state in self.states.values():
            if any(self.states[item].status != "running" for item in state.spec.dependencies):
                state.status = "waiting_dependency"
                continue
            if state.enabled and (
                state.status in {"stopped", "failed", "waiting_dependency"}
                and time.monotonic() >= state.backoff_until
            ):
                self._spawn(state)
        self.write_status()

    def write_status(self) -> None:
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "riverview-runtime-status-v1",
            "supervisor": "riverview.runtime.supervisor",
            "supervisor_pid": os.getpid(),
            "repository_root": str(self.repository),
            "git_branch": self._git_branch(),
            "python_executable": os.environ.get("PYTHON", os.sys.executable),
            "launch_mechanism": os.environ.get("RIVERVIEW_LAUNCH_MECHANISM", "unknown"),
            "lock_path": str(self.repository / "runtime" / "riverview-supervisor.lock.d"),
            "started_at": self.started_at,
            "updated_at": _now(),
            "git_sha": self._git_sha(),
            "services": {
                service_id: {
                    "status": state.status,
                    "enabled": state.enabled,
                    "pid": state.pid,
                    "adopted": state.adopted,
                    "restart_count": state.restart_count,
                    "last_failure": state.last_failure,
                    "last_change": state.last_change,
                    "port": state.spec.port,
                    "health_url": state.spec.health_url,
                    "dependencies": list(state.spec.dependencies),
                    "credential_available": bool(
                        state.spec.secret_file and Path(state.spec.secret_file).is_file()
                    ),
                }
                for service_id, state in self.states.items()
            },
        }
        temporary = self.status_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.status_path)

    def _git_sha(self) -> str:
        try:
            return subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repository,
                capture_output=True,
                text=True,
                timeout=2,
                check=True,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return "unknown"

    def _git_branch(self) -> str:
        try:
            return subprocess.run(
                ["git", "symbolic-ref", "--short", "-q", "HEAD"],
                cwd=self.repository,
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            ).stdout.strip() or "DETACHED"
        except (OSError, subprocess.SubprocessError):
            return "unknown"

    def run(self) -> None:
        lock = self.repository / "runtime" / "riverview-supervisor.lock.d"
        lock.parent.mkdir(parents=True, exist_ok=True)
        process_lock = self._acquire_process_lock(self.repository / "runtime" / "riverview-supervisor.lock")
        if process_lock is None:
            return
        try:
            shutil.rmtree(lock, ignore_errors=True)
            lock.mkdir()
            (lock / "owner.json").write_text(
                json.dumps({"pid": os.getpid(), "started_at": self.started_at}), encoding="utf-8"
            )
            while not self.stop_requested:
                self.reconcile_once()
                time.sleep(self.poll_seconds)
        finally:
            self.stop_all()
            self.write_status()
            try:
                (lock / "owner.json").unlink(missing_ok=True)
                lock.rmdir()
            except OSError:
                pass
            self._release_process_lock(process_lock)

    @staticmethod
    def _pid_exists(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except (OSError, ProcessLookupError):
            return False
        return True

    @staticmethod
    def _acquire_process_lock(path: Path) -> Any | None:
        """Acquire an OS-held singleton lock; return None when held."""
        path.parent.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            import ctypes
            name = "Local\\RiverviewRuntimeSupervisor-" + hashlib.sha256(str(path.resolve()).encode()).hexdigest()
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.CreateMutexW(None, True, name)
            if not handle:
                raise OSError("RIV-RUN-0001: unable to create Supervisor mutex.")
            if kernel32.GetLastError() == 183:
                kernel32.CloseHandle(handle)
                return None
            return ("windows", handle)
        handle = path.open("a+b")
        import fcntl
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            return None
        return ("posix", handle)

    @staticmethod
    def _release_process_lock(lock: Any) -> None:
        kind, value = lock
        if kind == "windows":
            import ctypes
            ctypes.windll.kernel32.ReleaseMutex(value)
            ctypes.windll.kernel32.CloseHandle(value)
        else:
            import fcntl
            fcntl.flock(value.fileno(), fcntl.LOCK_UN)
            value.close()

    def stop_all(self) -> None:
        self.stop_requested = True
        for state in self.states.values():
            if state.process is not None and state.process.poll() is None:
                state.process.terminate()
                try:
                    state.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    state.process.kill()
            for handle in (state.stdout_handle, state.stderr_handle):
                if handle is not None:
                    handle.close()
            state.stdout_handle = None
            state.stderr_handle = None
            state.status = "stopped"


def main() -> None:
    repository = Path(os.environ.get("RIVERVIEW_REPOSITORY", Path.cwd()))
    registry = Path(
        os.environ.get(
            "RIVERVIEW_RUNTIME_REGISTRY",
            repository / "config/runtime/riverview-runtime-services.json",
        )
    )
    supervisor = RuntimeSupervisor(repository, registry)
    try:
        supervisor.run()
    except KeyboardInterrupt:
        supervisor.stop_all()


if __name__ == "__main__":
    main()
