import json
from datetime import UTC, datetime
from urllib.request import Request, urlopen
from uuid import uuid4

from riverview.operator.openwebui import OpenWebUIConfig, RiverviewOpenWebUIService
from riverview.reasoning import ReasoningResponse


def test_browser_operator_exposes_authoritative_residents_and_bound_session() -> None:
    def provider(model, request):
        return ReasoningResponse(uuid4(), request.request_id, request.correlation_id, "local:test", "advice", f"identity reference {request.context_refs[0]}", (request.context_refs[0],), "operational", datetime.now(UTC))

    service = RiverviewOpenWebUIService(OpenWebUIConfig(port=18086, bearer_token="resident-test-token"), provider)
    service.start()
    try:
        with urlopen(Request("http://127.0.0.1:18086/session", method="POST")) as response:
            cookie = response.headers["Set-Cookie"].split(";", 1)[0]
        residents_request = Request("http://127.0.0.1:18086/api/residents", headers={"Cookie": cookie})
        with urlopen(residents_request) as response:
            residents = json.load(response)["residents"]
        names = {resident["name"] for resident in residents}
        assert {"Grace", "Alfred", "Ingrid", "Helen"} <= names
        body = json.dumps({"request_id": str(uuid4()), "correlation_id": str(uuid4()), "resident_id": "RES-000003", "message": "Good evening, Helen.", "classification": "operational"}).encode()
        chat_request = Request("http://127.0.0.1:18086/api/chat", data=body, method="POST", headers={"Cookie": cookie, "Content-Type": "application/json"})
        with urlopen(chat_request) as response:
            result = json.load(response)
        assert result["resident"]["resident_name"] == "Helen"
        assert result["resident"]["resident_id"] == "RES-000003"
        assert result["resident"]["role_authority_expanded"] is False
        room_body = json.dumps({"participants": ["RES-000001", "RES-000002", "RES-000003"]}).encode()
        room_request = Request("http://127.0.0.1:18086/api/rooms", data=room_body, method="POST", headers={"Cookie": cookie, "Content-Type": "application/json"})
        with urlopen(room_request) as response:
            room = json.load(response)
        assert set(room["participants"]) == {"RES-000001", "RES-000002", "RES-000003"}
        turn_body = json.dumps({"speaker": "RES-000002", "text": "Security context remains bounded."}).encode()
        turn_request = Request(f"http://127.0.0.1:18086/api/rooms/{room['room_id']}/turn", data=turn_body, method="POST", headers={"Cookie": cookie, "Content-Type": "application/json"})
        with urlopen(turn_request) as response:
            turn = json.load(response)
        assert turn["speaker_id"] == "RES-000002"
    finally:
        service.stop()
