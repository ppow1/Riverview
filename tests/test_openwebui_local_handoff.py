from __future__ import annotations

import json
from datetime import UTC, datetime
from urllib.request import Request, urlopen
from uuid import uuid4

from riverview.operator.openwebui import OpenWebUIConfig, RiverviewOpenWebUIService
from riverview.reasoning import ReasoningResponse


def test_local_credential_handoff_authenticates_without_exposing_bearer() -> None:
    def provider(model, request):
        return ReasoningResponse(uuid4(), request.request_id, request.correlation_id, "local:test", "advice", "hello", ("test://evidence",), "operational", datetime.now(UTC))

    service = RiverviewOpenWebUIService(OpenWebUIConfig(port=18084, bearer_token="hidden-token"), provider)
    service.start()
    try:
        session_request = Request("http://127.0.0.1:18084/session", method="POST")
        with urlopen(session_request) as response:
            cookie = response.headers["Set-Cookie"].split(";", 1)[0]
            assert "hidden-token" not in response.headers.get("Set-Cookie", "")
        body = json.dumps({"request_id": str(uuid4()), "correlation_id": str(uuid4()), "message": "say hello", "context_refs": ["browser-artifact:test:hash"]}).encode()
        request = Request("http://127.0.0.1:18084/api/chat", data=body, method="POST", headers={"Cookie": cookie, "Content-Type": "application/json"})
        with urlopen(request) as response:
            payload = json.load(response)
        assert payload["response"]["provider_id"] == "local:test"
    finally:
        service.stop()
