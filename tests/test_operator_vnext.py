import json
from urllib.error import HTTPError
from datetime import UTC, datetime
from urllib.request import Request, urlopen
from uuid import uuid4

from riverview.operator.openwebui import OpenWebUIConfig, RiverviewOpenWebUIService
from riverview.operator.vnext import ConversationTransition
from riverview.operator.vnext_projection import build_resource_topology, build_vnext_projection
from riverview.reasoning import ReasoningResponse
from riverview.reasoning.epistemic import EpistemicSpan, ProvenanceRecord, VERIFIED, build_epistemic_metadata


def test_transition_keeps_active_until_success_and_fails_closed() -> None:
    state = ConversationTransition(active_id="A")
    generation = state.request("B")
    assert state.status == "loading"
    assert state.active_id == "A"
    assert state.can_send("A") is False
    assert state.payload("B", "hello") is None
    assert state.succeed("B", generation) is True
    assert state.active_id == "B"
    assert state.can_send("B") is True
    assert state.payload("B", "hello")["conversation_id"] == "B"


def test_transition_ignores_stale_success_and_failure() -> None:
    state = ConversationTransition(active_id="A")
    old = state.request("B")
    current = state.request("C")
    assert state.succeed("B", old) is False
    assert state.active_id == "A"
    assert state.fail("B", old) is False
    assert state.succeed("C", current) is True
    assert state.active_id == "C"


def test_vnext_projection_is_bounded_and_honest() -> None:
    projection = build_vnext_projection(cme=None, runtime=None, conversations=[{"id": str(i)} for i in range(20)])
    assert projection["pulse"]["state"] == "UNREACHABLE"
    assert len(projection["conversations"]) == 8
    assert build_resource_topology()["chassis"][0]["independent"] is True


def test_vnext_real_route_exposes_compact_picker_and_create_contract() -> None:
    service = RiverviewOpenWebUIService(OpenWebUIConfig(port=18084, bearer_token="synthetic-token"), lambda model, request: None)
    service.start()
    try:
        with urlopen("http://127.0.0.1:18084/vnext") as response:
            page = response.read().decode()
        assert response.status == 200
        for label in ("Converse", "New Conversation", "Settings", "Snapshot", "CME", "System Pulse"):
            assert label in page
        assert "conversation" in page.lower()
        assert "Conversation unavailable" in page
        assert "Loading" in page
        assert "resident" in page.lower()
        assert "if(!id||id===state.activeId)return" not in page
        assert "requestConversation(id,force=false)" in page
        assert "!force&&id===state.activeId&&state.active&&state.loadState==='active'" in page
        request = Request("http://127.0.0.1:18084/api/vnext/projection", headers={"Authorization": "Bearer synthetic-token"})
        with urlopen(request) as response:
            projection = json.load(response)
        assert projection["schema_version"] == "riverview-operator-vnext-projection-v1"
    finally:
        service.stop()


def test_vnext_create_assign_send_and_history_are_authoritative() -> None:
    def provider(model, request):
        epistemic = build_epistemic_metadata([EpistemicSpan("greeting", 0, 7, VERIFIED, (ProvenanceRecord("institutional", "river://test"),))], response_text="Bounded resident response")
        return ReasoningResponse(
            uuid4(), request.request_id, request.correlation_id, "local:vnext-test",
            "advice", "Bounded resident response", ("test://evidence",),
            "operational", datetime.now(UTC), epistemic=epistemic,
        )

    service = RiverviewOpenWebUIService(OpenWebUIConfig(port=18095, bearer_token="vnext-contract"), provider)
    service.start()
    try:
        with urlopen(Request("http://127.0.0.1:18095/session", method="POST")) as response:
            cookie = response.headers["Set-Cookie"].split(";", 1)[0]
        headers = {"Cookie": cookie, "Content-Type": "application/json"}
        create = Request(
            "http://127.0.0.1:18095/api/conversations",
            data=json.dumps({"resident_id": "", "title": "New Conversation"}).encode(),
            method="POST", headers=headers,
        )
        with urlopen(create) as response:
            created = json.load(response)
        assign = Request(
            f"http://127.0.0.1:18095/api/conversations/{created['id']}",
            data=json.dumps({"resident_id": "RES-000001", "title": "Alfred Conversation"}).encode(),
            method="PUT", headers=headers,
        )
        with urlopen(assign) as response:
            assigned = json.load(response)
        assert assigned["id"] == created["id"]
        assert assigned["resident_id"] == "RES-000001"

        chat = Request(
            "http://127.0.0.1:18095/api/chat",
            data=json.dumps({
                "request_id": str(uuid4()), "correlation_id": str(uuid4()),
                "conversation_id": assigned["id"], "resident_id": assigned["resident_id"],
                "message": "Give a bounded greeting.",
            }).encode(),
            method="POST", headers=headers,
        )
        with urlopen(chat) as response:
            result = json.load(response)
        assert result["response"]["summary"] == "Bounded resident response"
        assert result["response"]["epistemic"]["summary_mask"] == VERIFIED

        history = Request(
            f"http://127.0.0.1:18095/api/conversations/{assigned['id']}?archived=true",
            headers={"Cookie": cookie},
        )
        with urlopen(history) as response:
            messages = json.load(response)["messages"]
        assert [(item["speaker"], item["text"]) for item in messages[-2:]] == [
            ("Steward", "Give a bounded greeting."),
            ("Alfred", "Bounded resident response"),
        ]
        assert messages[-1]["details"]["epistemic"]["spans"][0]["provenance"][0]["evidence_ref"] == "river://test"
    finally:
        service.stop()


def test_resident_boundary_failure_is_controlled_and_service_survives() -> None:
    service = RiverviewOpenWebUIService(OpenWebUIConfig(port=18096, bearer_token="vnext-survival"), lambda model, request: None)
    service.start()
    try:
        with urlopen(Request("http://127.0.0.1:18096/session", method="POST")) as response:
            cookie = response.headers["Set-Cookie"].split(";", 1)[0]
        request = Request(
            "http://127.0.0.1:18096/api/chat",
            data=json.dumps({
                "request_id": str(uuid4()), "correlation_id": str(uuid4()),
                "resident_id": "not-an-authoritative-resident", "message": "bounded failure probe",
            }).encode(),
            method="POST", headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        try:
            urlopen(request)
        except HTTPError as error:
            assert error.code == 400
            assert json.loads(error.read())["error"] == "bounded_request_rejected"
        else:
            raise AssertionError("resident boundary failure unexpectedly returned success")
        with urlopen("http://127.0.0.1:18096/health") as response:
            assert response.status == 200
    finally:
        service.stop()
