"""Riverview-owned bounded browser bridge for RV-008.3."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from riverview.comms.bindings import DESIGNATED_ROLE, BindingRegistry
from riverview.doorbell.config import load_config

from .contract import DoorbellRequest, DoorbellResult

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BRIDGE = REPOSITORY_ROOT / "tools" / "riverview_doorbell_bridge.cjs"
DESIGNATED_SELECTOR = "riverview-designated"
MAILBOX_RESOURCE = "riverview://mailbox"


@dataclass(frozen=True, slots=True)
class BrowserBridgeRunner:
    """Invoke only Riverview's named browser operation."""

    bridge_path: Path = DEFAULT_BRIDGE
    node_executable: str = "node"
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None
    binding_registry: BindingRegistry | None = None

    def ring(self, request: DoorbellRequest) -> DoorbellResult:
        if request.conversation_selector != DESIGNATED_SELECTOR:
            raise ValueError("RIV-PLY-0002: only the Riverview designated target is permitted.")
        if request.mailbox_resource != MAILBOX_RESOURCE:
            raise ValueError("RIV-PLY-0002: only the Riverview mailbox resource is permitted.")
        binding = (self.binding_registry or BindingRegistry()).resolve_active(DESIGNATED_ROLE)
        local_config = load_config()
        if local_config.conversation_id != str(binding["conversation_id"]):
            raise ValueError("RIV-COMMS-0004: local doorbell target differs from active authoritative binding.")
        payload = {"operation": "ring_riverview_doorbell", "request_id": str(request.request_id),
                   "correlation_id": str(request.correlation_id), "timeout_seconds": request.timeout_seconds}
        run = self.runner or subprocess.run
        try:
            completed = run([self.node_executable, str(self.bridge_path), "--ring"],
                            input=json.dumps(payload), capture_output=True, text=True,
                            timeout=request.timeout_seconds + 5, check=False)
        except subprocess.TimeoutExpired:
            return DoorbellResult(request.request_id, request.correlation_id, "failed", _now(), None, "RIV-PLY-0009")
        try:
            result: Any = json.loads(completed.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            result = {"failure_class": "RIV-PLY-0003"}
        state = "succeeded" if result.get("status") in {"succeeded", "already_succeeded"} else "failed"
        return DoorbellResult(request.request_id, request.correlation_id, state, _now(),
                              result.get("evidence_ref"), result.get("failure_class"))


def _now():
    from datetime import UTC, datetime
    return datetime.now(UTC)
