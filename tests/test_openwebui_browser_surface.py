from __future__ import annotations

from datetime import UTC, datetime
from urllib.request import urlopen
from uuid import uuid4

from riverview.operator.openwebui import OpenWebUIConfig, RiverviewOpenWebUIService
from riverview.reasoning import ReasoningResponse


def test_browser_operator_surface_is_real_html_and_artifact_aware() -> None:
    def provider(model, request):
        return ReasoningResponse(uuid4(), request.request_id, request.correlation_id, "test-provider", "advice", "bounded", ("test://evidence",), "operational", datetime.now(UTC))

    service = RiverviewOpenWebUIService(OpenWebUIConfig(port=18083, bearer_token="synthetic-token"), provider)
    service.start()
    try:
        with urlopen("http://127.0.0.1:18083/") as response:
            page = response.read().decode()
        assert "Riverview Operator" in page
        assert 'type="file"' in page
        assert "crypto.subtle.digest" in page
        assert "/api/chat" in page
        assert "Use local Riverview credential" in page
    finally:
        service.stop()
