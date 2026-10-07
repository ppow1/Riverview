from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .store import DurableStore, utcnow


class EnvironmentObserver(Protocol):
    def observe(self) -> dict[str, Any]: ...


class OperationAdapter(Protocol):
    def execute(self, action: dict[str, Any]) -> dict[str, Any]: ...

    def verify(self, action: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class StewardEnvironmentObserver:
    """Reads the existing Steward/Octo2 monitor and video1 projections."""

    monitor_state: Path
    latest_frame: Path
    infrastructure: dict[str, Any] | None = None

    @staticmethod
    def _ports_ready(host: str, ports: list[int], timeout: float) -> tuple[int, int]:
        ready = 0
        for port in ports:
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    ready += 1
            except OSError:
                pass
        return ready, len(ports)

    def observe(self) -> dict[str, Any]:
        worker: dict[str, Any] = {"state": "UNKNOWN", "boot_id": None, "pid": None}
        if self.monitor_state.exists():
            raw = json.loads(self.monitor_state.read_text(encoding="utf-8-sig"))
            worker = {
                "state": raw.get("state", "UNKNOWN"),
                "boot_id": raw.get("boot_id") or None,
                "pid": raw.get("llama_pid") or None,
                "observed_at": raw.get("timestamp"),
            }
        frame = {"available": self.latest_frame.exists(), "path": str(self.latest_frame)}
        if self.latest_frame.exists():
            frame.update({"mtime_ns": self.latest_frame.stat().st_mtime_ns, "size": self.latest_frame.stat().st_size})
        health = {
            "dev": {"status": "READY", "color": "green", "detail": "SNAIL coordinator running"},
            "octo2": {
                "status": "READY" if worker["state"] == "80B_READY" else worker["state"],
                "color": "green" if worker["state"] == "80B_READY" else "yellow",
                "detail": "existing Octo2 Monitor V2 projection",
            },
        }
        for name, node in (self.infrastructure or {}).items():
            ready, total = self._ports_ready(node["host"], node["ports"], float(node.get("timeout", 0.75)))
            status = "READY" if ready == total else "DEGRADED" if ready else "DOWN"
            health[name] = {"status": status, "color": "green" if ready == total else "yellow" if ready else "red", "detail": f"{ready}/{total} management ports reachable"}
        target_state = health.get("octo1", {}).get("status", "UNKNOWN")
        return {"observed_at": utcnow(), "worker": worker, "target": {"identity": "OCTO1", "state": target_state}, "frame": frame, "infrastructure": health}


class LocalPlanningAdapter:
    """Production adapter for the only current autonomous write: a review-only proposal."""

    def __init__(self, store: DurableStore):
        self.store = store
        self.artifacts = store.root / "artifacts"
        self.artifacts.mkdir(parents=True, exist_ok=True)

    def _target(self, action: dict[str, Any]) -> Path:
        operation = action["operation_type"]
        if operation == "planning_proposal":
            return self.artifacts / "C1_PLANNING_PROPOSAL.md"
        if operation == "write_harmless_marker":
            return self.artifacts / "qualification-marker.txt"
        raise ValueError(f"no production adapter for {operation}")

    def execute(self, action: dict[str, Any]) -> dict[str, Any]:
        target = self._target(action)
        content = str(action["command"])
        if target.exists() and target.read_text(encoding="utf-8") == content:
            return {"status": "ALREADY_APPLIED", "path": str(target)}
        fd, temporary = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return {"status": "EXECUTED", "path": str(target)}

    def verify(self, action: dict[str, Any]) -> dict[str, Any]:
        target = self._target(action)
        expected = str(action["command"]).encode()
        if not target.exists():
            return {"verified": False, "reason": "expected artifact absent", "evidence_ids": []}
        actual = target.read_bytes()
        if actual != expected:
            return {"verified": False, "reason": "artifact differs from proposed content", "evidence_ids": []}
        evidence = self.store.preserve(target, {"kind": "operation_effect", "operation_id": action["operation_id"]})
        return {
            "verified": True,
            "reason": "independent read-back matched expected bytes",
            "sha256": hashlib.sha256(actual).hexdigest(),
            "evidence_ids": [evidence["evidence_id"]],
        }


class SubprocessRunner:
    """Bounded local process runner used by deterministic hardware adapters."""

    def run(self, argv: list[str], *, timeout: float) -> dict[str, Any]:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }


class Octo1HardwareAdapter:
    """Deterministic OCTO1 campaign adapter.

    This adapter intentionally accepts structured commands only. The reasoning worker
    selects an allowlisted operation, but cannot inject an arbitrary shell command.
    """

    def __init__(self, store: DurableStore, config: dict[str, Any], runner: SubprocessRunner | None = None):
        self.store = store
        self.config = config
        self.runner = runner or SubprocessRunner()
        self.artifacts = store.root / "artifacts"
        self.artifacts.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _command(action: dict[str, Any]) -> dict[str, Any]:
        raw = action["command"]
        if isinstance(raw, dict):
            return raw
        try:
            parsed = json.loads(str(raw))
        except json.JSONDecodeError as exc:
            raise ValueError("hardware operations require a JSON object command") from exc
        if not isinstance(parsed, dict):
            raise ValueError("hardware operation command must decode to an object")
        return parsed

    def _candidate(self) -> dict[str, Any]:
        candidate = self.config.get("current_candidate")
        if not isinstance(candidate, dict):
            raise ValueError("current_candidate missing from campaign config")
        return candidate

    def _candidate_path(self, command: dict[str, Any]) -> Path:
        path = command.get("path")
        if not path:
            raise ValueError("candidate path required")
        return Path(path)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _validate_candidate(self, path: Path) -> dict[str, Any]:
        candidate = self._candidate()
        if not path.exists():
            raise FileNotFoundError(path)
        actual_size = path.stat().st_size
        actual_sha = self._sha256(path)
        expected_sha = str(candidate["full_image_sha256"]).lower()
        if actual_size != 8388608:
            raise ValueError(f"candidate size mismatch: {actual_size}")
        if actual_sha.lower() != expected_sha:
            raise ValueError(f"candidate hash mismatch: {actual_sha}")
        return {"path": str(path), "size": actual_size, "sha256": actual_sha}

    def execute(self, action: dict[str, Any]) -> dict[str, Any]:
        operation = action["operation_type"]
        command = self._command(action)

        if operation == "candidate_stage":
            identity = self._validate_candidate(self._candidate_path(command))
            manifest = self.artifacts / "C1_CANDIDATE_STAGED.json"
            manifest.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
            return {"status": "EXECUTED", **identity, "manifest": str(manifest)}

        if operation == "octo1_diagnostic":
            name = command.get("name")
            commands = {
                "identity": ["ssh", "octo1", "hostname; uname -a"],
                "pci": ["ssh", "octo1", "lspci -nn"],
                "gpu": ["ssh", "octo1", "nvidia-smi -L"],
                "boot_id": ["ssh", "octo1", "cat /proc/sys/kernel/random/boot_id"],
            }
            if name not in commands:
                raise ValueError("unsupported octo1 diagnostic")
            return self.runner.run(commands[name], timeout=float(command.get("timeout", 30)))

        if operation == "video_capture":
            source = Path(command.get("path", ""))
            if not source.exists():
                raise FileNotFoundError(source)
            record = self.store.preserve(source, {"kind": "video1_frame", "operation_id": action["operation_id"]})
            return {"status": "EXECUTED", "evidence_id": record["evidence_id"], "path": str(source)}

        if operation == "pikvm_hid":
            text_value = command.get("text")
            if not isinstance(text_value, str) or not text_value:
                raise ValueError("pikvm_hid requires non-empty text")
            remote = (
                "curl --silent --show-error --fail --unix-socket /run/kvmd/kvmd.sock "
                "--data-urlencode text=" + __import__("shlex").quote(text_value) + " "
                "http://localhost/api/hid/print"
            )
            return self.runner.run(["ssh", "pikvm", remote], timeout=float(command.get("timeout", 15)))

        if operation in {"bios_region_write", "bios_readback_verify", "reboot_octo1"}:
            raise RuntimeError(
                f"{operation} is campaign-authorized but its deterministic transport is not yet qualified; "
                "do not substitute arbitrary shell execution"
            )

        if operation in {"workload_test", "stability_test"}:
            raise RuntimeError(f"{operation} requires a named, versioned test definition")

        if operation in {"request_physical_work", "stock_recovery"}:
            raise RuntimeError(f"{operation} is Steward-gated and is not executed by the hardware adapter")

        raise ValueError(f"no hardware adapter for {operation}")

    def verify(self, action: dict[str, Any]) -> dict[str, Any]:
        operation = action["operation_type"]
        command = self._command(action)

        if operation == "candidate_stage":
            identity = self._validate_candidate(self._candidate_path(command))
            return {"verified": True, "reason": "candidate size and SHA-256 match campaign manifest", **identity}

        if operation == "octo1_diagnostic":
            result = self.execute(action)
            return {
                "verified": result.get("returncode") == 0,
                "reason": "diagnostic command completed successfully" if result.get("returncode") == 0 else "diagnostic command failed",
                "result": result,
            }

        if operation == "video_capture":
            source = Path(command.get("path", ""))
            return {"verified": source.exists() and source.stat().st_size > 0, "reason": "frame exists and is non-empty"}

        if operation == "pikvm_hid":
            return {
                "verified": False,
                "reason": "KVMD API acceptance is not independent physical HID verification; verify target effect through video1",
            }

        return {"verified": False, "reason": "independent verifier not implemented for operation"}
