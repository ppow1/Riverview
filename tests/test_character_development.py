from pathlib import Path

import pytest

from riverview.characters import CharacterDesignerWorkflow, CharacterStore, ContinuityStore
from riverview.residents.gateway import ResidentConversationGateway, ResidentProfile


def profiles():
    return (ResidentProfile("RES-000003", "Helen", "Manager", "estate://helen", "estate://source/helen"),)


def test_character_proposal_review_publish_preserves_canon_and_rejected_path(tmp_path: Path):
    store = CharacterStore.from_profiles(profiles(), tmp_path / "characters.json")
    workflow = CharacterDesignerWorkflow(store)
    original = workflow.inspect("RES-000003")
    rejected = workflow.propose("RES-000003", {"traits": {"temperament": "calm"}}, author="Character Designer", sources=["estate://design/helen"], rationale="bounded proposal")
    workflow.review(rejected["proposal_id"], decision="rejected", reviewer="Steward", rationale="not accepted")
    assert store.current("RES-000003")["version"] == original["version"]
    accepted = workflow.propose("RES-000003", {"traits": {"temperament": "warm"}}, author="Character Designer", sources=["estate://design/helen"], rationale="harmless development round")
    workflow.review(accepted["proposal_id"], decision="accepted", reviewer="Steward", rationale="approved")
    published = workflow.publish(accepted["proposal_id"])
    assert published["version"] == "v2"
    assert store.current("RES-000003")["traits"]["temperament"] == "warm"
    assert len(store.data["versions"]) == 2


def test_continuity_candidate_is_not_runtime_truth_until_published(tmp_path: Path):
    store = ContinuityStore(tmp_path / "continuity.json")
    candidate = store.propose("RES-000003", "session-a", "Helen prefers a bounded review ritual.", source_evidence=["session:session-a"])
    assert store.accepted("RES-000003") == []
    published = store.publish(candidate["continuity_id"], reviewer="Steward", rationale="bounded continuity")
    assert [x["continuity_id"] for x in store.accepted("RES-000003")] == [published["continuity_id"]]


def test_room_chat_produces_identity_preserving_provider_turns():
    from datetime import UTC, datetime
    from uuid import uuid4

    from riverview.reasoning import ReasoningResponse
    service = ResidentConversationGateway(tuple(profiles()) + (
        ResidentProfile("RES-000001", "Alfred", "Manager", "estate://alfred", "estate://source/alfred"),
        ResidentProfile("RES-000002", "Ingrid", "Manager", "estate://ingrid", "estate://source/ingrid"),
    ))
    room = service.create_room(("Helen", "Alfred", "Ingrid"))
    def provider(request):
        return ReasoningResponse(uuid4(), request.request_id, request.correlation_id, "local:test", "advice", request.context_refs[0], (request.context_refs[0],), request.classification, datetime.now(UTC))
    turns = service.room_chat(room, "Give one bounded greeting.", provider=provider, interface_id="test")
    assert [turn["speaker_name"] for turn in turns] == ["Helen", "Alfred", "Ingrid"]
    assert all(turn["no_authority_expansion"] for turn in turns)


def test_room_chat_preserves_completed_turns_when_later_participant_fails():
    from datetime import UTC, datetime
    from uuid import uuid4

    from riverview.reasoning import ReasoningResponse
    from riverview.residents.gateway import RoomTurnPartialFailure

    service = ResidentConversationGateway(tuple(profiles()) + (ResidentProfile("RES-000001", "Alfred", "Manager", "estate://alfred", "estate://source/alfred"),))
    room = service.create_room(("Helen", "Alfred"))
    calls = 0
    def provider(request):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("bounded provider fixture failure")
        return ReasoningResponse(uuid4(), request.request_id, request.correlation_id, "local:test", "advice", "completed", ("room-evidence",), request.classification, datetime.now(UTC))
    with pytest.raises(RoomTurnPartialFailure) as failure:
        service.room_chat(room, "bounded question", provider=provider, interface_id="test")
    assert [item["speaker_id"] for item in failure.value.completed] == ["RES-000003"]
    assert failure.value.failed_resident_id == "RES-000001"
