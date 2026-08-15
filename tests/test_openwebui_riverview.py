import json
from datetime import UTC, datetime
from urllib.request import Request, urlopen
from uuid import uuid4

from riverview.operator.openwebui import OpenWebUIConfig, RiverviewOpenWebUIService
from riverview.reasoning import ReasoningResponse


def test_riverview_openwebui_isolated_and_correlated() -> None:
    correlation = uuid4()
    def provider(model, request):
        return ReasoningResponse(uuid4(), request.request_id, request.correlation_id, "test-provider", "advice", "bounded", ("test://evidence",), "operational", datetime.now(UTC))
    service = RiverviewOpenWebUIService(OpenWebUIConfig(port=18081, bearer_token="synthetic-token"), provider)
    service.start()
    try:
        with urlopen("http://127.0.0.1:18081/health") as response:
            assert response.status == 200
        request_id = uuid4()
        body = json.dumps({"request_id": str(request_id), "correlation_id": str(correlation), "message": "bounded"}).encode()
        request = Request("http://127.0.0.1:18081/api/chat", data=body, headers={"Authorization": "Bearer synthetic-token", "Content-Type": "application/json"})
        with urlopen(request) as response:
            payload = json.load(response)
        assert payload["response"]["correlation_id"] == str(correlation)
    finally:
        service.stop()
