import json
from datetime import UTC, datetime
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

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


def test_neutral_new_and_derived_room_execution_preserve_source_and_context() -> None:
    def provider(model, request):
        return ReasoningResponse(uuid4(), request.request_id, request.correlation_id, "local:test", "advice", "bounded room response", ("room-evidence",), "operational", datetime.now(UTC))

    service = RiverviewOpenWebUIService(OpenWebUIConfig(port=18087, bearer_token="room-continuity-test-token"), provider)
    service.start()
    try:
        with urlopen(Request("http://127.0.0.1:18087/session", method="POST")) as response:
            cookie = response.headers["Set-Cookie"].split(";", 1)[0]
        headers = {"Cookie": cookie, "Content-Type": "application/json"}

        neutral_request = Request("http://127.0.0.1:18087/api/conversations", data=json.dumps({"resident_id": "", "title": "New Conversation"}).encode(), method="POST", headers=headers)
        with urlopen(neutral_request) as response:
            neutral = json.load(response)
        assert neutral["resident_id"] == ""
        assert neutral["kind"] == "conversation"

        source = service.projection.create(resident_id="grace", title="Grace Source")
        source_id = UUID(source["id"])
        service.projection.append(source_id, role="steward", text="Quarterly coffee budget is the distinctive topic.", speaker_id=None, speaker="Steward", details={})
        service.projection.append(source_id, role="resident", text="Grace discussed the quarterly coffee budget.", speaker_id="grace", speaker="Grace", details={})

        room_payload = {"participants": ["grace", "RES-000001"], "source_conversation_id": source["id"], "context_window": "last_20"}
        room_request = Request("http://127.0.0.1:18087/api/rooms", data=json.dumps(room_payload).encode(), method="POST", headers=headers)
        with urlopen(room_request) as response:
            room = json.load(response)
        derived = room["operator_conversation"]
        assert derived["source_conversation_id"] == source["id"]
        assert derived["inherited_context_window"] == "last_20"
        assert derived["inherited_message_count"] == 2
        assert {profile["name"] for profile in room["participant_profiles"]} == {"Grace", "Alfred"}

        chat_payload = {"message": "What was the distinctive topic?", "correlation_id": str(uuid4()), "model": "approved"}
        chat_request = Request(f"http://127.0.0.1:18087/api/rooms/{room['room_id']}/chat", data=json.dumps(chat_payload).encode(), method="POST", headers=headers)
        with urlopen(chat_request) as response:
            chat = json.load(response)
        assert len(chat["responses"]) == 2
        assert chat["persisted_message_count"] >= 5

        history_request = Request(f"http://127.0.0.1:18087/api/conversations/{derived['id']}?archived=true", headers={"Cookie": cookie})
        with urlopen(history_request) as response:
            history = json.load(response)
        assert len(history["messages"]) >= 5
        source_after = service.projection.refresh(source_id, include_archived=True)
        assert source_after is not None and len(source_after["messages"]) == 2

        html_request = Request("http://127.0.0.1:18087/", headers={"Cookie": cookie})
        with urlopen(html_request) as response:
            html = response.read().decode()
        assert "New Conversation" in html
        assert "No previous context (from this point forward)" in html
        assert "neutralComposerStyle" in html
        assert "$('mic-state').className='sr-only'" in html
    finally:
        service.stop()
