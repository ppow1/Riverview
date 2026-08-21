"""Bounded request/response evidence for Comms5 transport investigations.

Version: 1.0.0

This records metadata only when explicitly enabled. It never records request
headers, bodies, authorization values, or MCP payloads.
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_LOCK = threading.Lock()
_MAX_BYTES = 10 * 1024 * 1024
_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_PATH = _ROOT / "runtime" / "diagnostics" / "comms5-transport" / "http-events.jsonl"


def _enabled() -> bool:
    return os.environ.get("RIVERVIEW_COMMS5_TRANSPORT_DIAGNOSTICS", "0") == "1"


def _path() -> Path:
    return Path(os.environ.get("RIVERVIEW_COMMS5_TRANSPORT_DIAGNOSTICS_PATH", str(_DEFAULT_PATH)))


def record(event: str, request_id: str, *, started: float | None = None, **fields: Any) -> None:
    """Append one bounded transport event without sensitive request data."""

    if not _enabled():
        return
    safe_id = request_id[:128] if request_id else f"generated-{uuid4()}"
    payload = {
        "version": "1.0.0",
        "event": event,
        "request_id": safe_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if started is not None:
        payload["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
    payload.update({key: value for key, value in fields.items() if key in {
        "method", "path", "status", "content_type", "session_id", "error",
        "probe_id", "operation", "phase",
    }})
    line = json.dumps(payload, separators=(",", ":"), ensure_ascii=True) + "\n"
    destination = _path()
    with _LOCK:
        try:
            if destination.exists() and destination.stat().st_size >= _MAX_BYTES:
                return
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("a", encoding="utf-8") as handle:
                handle.write(line)
        except OSError:
            # Diagnostics must never make the transport unavailable.
            return


class TransportDiagnosticsMiddleware:
    """ASGI boundary events for request receipt and response completion."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        headers = {key.decode("latin-1").lower(): value.decode("latin-1") for key, value in scope.get("headers", [])}
        request_id = headers.get("x-riverview-request-id", "") or f"http-{uuid4()}"
        scope["riverview_request_id"] = request_id
        started = time.perf_counter()
        record("http.received", request_id, started=started, method=scope.get("method"), path=scope.get("path"))
        response_started = False

        async def diagnostic_send(message: dict[str, Any]) -> None:
            nonlocal response_started
            if message.get("type") == "http.response.start":
                response_started = True
                response_headers = {key.decode("latin-1").lower(): value.decode("latin-1") for key, value in message.get("headers", [])}
                record("http.response.start", request_id, started=started, status=message.get("status"), content_type=response_headers.get("content-type"), session_id=response_headers.get("mcp-session-id"))
            await send(message)
            if message.get("type") == "http.response.body" and not message.get("more_body", False):
                record("http.sent", request_id, started=started, status="started" if response_started else "unknown")

        try:
            await self.app(scope, receive, diagnostic_send)
        except Exception as exc:  # pragma: no cover - exercised by live boundary
            record("http.exception", request_id, started=started, error=type(exc).__name__)
            raise
