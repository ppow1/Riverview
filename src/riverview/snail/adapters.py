from __future__ import annotations

import hashlib
import json
import os
import socket
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
