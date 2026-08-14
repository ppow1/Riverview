"""Narrow Riverview client for the Estate-owned doorbell operation.

Version: 1.0.0

The Estate owns browser authentication, target resolution, CDP, and the fixed
wake action.  This module sends only request/correlation metadata to the named
bridge process and never imports or invokes the Estate mailbox worker.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contract import DoorbellRequest, DoorbellResult

DEFAULT_BRIDGE = Path(r"A:\theestate\tools\riverview_doorbell_bridge.cjs")
DESIGNATED_SELECTOR = "estate-riverview-designated"
MAILBOX_RESOURCE = "riverview://mailbox"


@dataclass(frozen=True, slots=True)
class EstateBridgeRunner:
    """Run the single Estate bridge operation through a fixed Node entrypoint."""

    bridge_path: Path = DEFAULT_BRIDGE
    node_executable: str = "node"
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None

    def ring(self, request: DoorbellRequest) -> DoorbellResult:
        if request.conversation_selector != DESIGNATED_SELECTOR:
            raise ValueError("RIV-PLY-0002: only the Estate designated target is permitted.")
        if request.mailbox_resource != MAILBOX_RESOURCE:
            raise ValueError("RIV-PLY-0002: only the Riverview mailbox resource is permitted.")
        payload = {
            "operation": "ring_riverview_doorbell",
            "request_id": str(request.request_id),
            "correlation_id": str(request.correlation_id),
            "timeout_seconds": request.timeout_seconds,
        }
        command = [self.node_executable, str(self.bridge_path), "--ring"]
        run = self.runner or subprocess.run
        try:
            completed = run(
                command,
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds + 5,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return DoorbellResult(
                request.request_id, request.correlation_id, "failed", request_observed(), None,
                "RIV-PLY-0009",
            )
        try:
            result: Any = json.loads(completed.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            result = {"failure_class": "RIV-PLY-0003"}
        failure = result.get("failure_class")
        state = "succeeded" if result.get("status") in {"succeeded", "already_succeeded"} else "failed"
        return DoorbellResult(
            request.request_id,
            request.correlation_id,
            state,
            request_observed(),
            result.get("evidence_ref"),
            failure,
        )


def request_observed():
    from datetime import UTC, datetime

    return datetime.now(UTC)


def configured_estate_bridge() -> EstateBridgeRunner:
    return EstateBridgeRunner(Path(os.environ.get("RIVERVIEW_ESTATE_DOORBELL_BRIDGE", DEFAULT_BRIDGE)))
