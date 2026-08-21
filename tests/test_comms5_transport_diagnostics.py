from __future__ import annotations

import json
from pathlib import Path

import pytest

from riverview.mcp.transport_diagnostics import TransportDiagnosticsMiddleware


@pytest.mark.anyio
async def test_transport_diagnostics_records_bounded_request_response_events(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "events.jsonl"
    monkeypatch.setenv("RIVERVIEW_COMMS5_TRANSPORT_DIAGNOSTICS", "1")
    monkeypatch.setenv("RIVERVIEW_COMMS5_TRANSPORT_DIAGNOSTICS_PATH", str(destination))
    sent: list[dict[str, object]] = []

    async def app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/event-stream"), (b"mcp-session-id", b"session-1")],
            }
        )
        await send({"type": "http.response.body", "body": b"secret payload", "more_body": False})

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/mcp",
        "headers": [
            (b"x-riverview-request-id", b"diag-123"),
            (b"authorization", b"Bearer must-not-be-recorded"),
        ],
    }
    await TransportDiagnosticsMiddleware(app)(scope, None, send)

    events = [json.loads(line) for line in destination.read_text(encoding="utf-8").splitlines()]
    assert [event["event"] for event in events] == [
        "http.received",
        "http.response.start",
        "http.sent",
    ]
    assert {event["request_id"] for event in events} == {"diag-123"}
    serialized = destination.read_text(encoding="utf-8")
    assert "authorization" not in serialized.lower()
    assert "secret payload" not in serialized
    assert sent[-1]["type"] == "http.response.body"


@pytest.mark.anyio
async def test_transport_diagnostics_is_disabled_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    destination = tmp_path / "events.jsonl"
    monkeypatch.delenv("RIVERVIEW_COMMS5_TRANSPORT_DIAGNOSTICS", raising=False)
    monkeypatch.setenv("RIVERVIEW_COMMS5_TRANSPORT_DIAGNOSTICS_PATH", str(destination))

    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    async def send(message):
        return None

    await TransportDiagnosticsMiddleware(
        app
    )(
        {"type": "http", "method": "GET", "path": "/mcp", "headers": []},
        None,
        send,
    )
    assert not destination.exists()
