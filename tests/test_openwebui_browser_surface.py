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
        assert "directGraceProposalMarkup" in page
        assert "data-approve-proposal" in page
        assert "direct_grace_approval" in page
        assert "Yes — approve this exact specification" in page
        assert "Use local Riverview credential" in page
        assert "reference-only" in page
        assert "Enter an instruction describing what you want Riverview to do with this artifact." in page
        assert "Capture bounded local microphone transcription" in page
        with urlopen("http://127.0.0.1:18083/spatial") as response:
            spatial = response.read().decode()
        assert "immersive-vr" in spatial
    finally:
        service.stop()
