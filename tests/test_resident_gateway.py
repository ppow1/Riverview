from datetime import UTC, datetime
from uuid import uuid4

import pytest

from riverview.reasoning import ReasoningRequest, ReasoningResponse
from riverview.residents.gateway import ResidentConversationGateway, ResidentProfile


def gateway() -> ResidentConversationGateway:
    return ResidentConversationGateway(
        (
            ResidentProfile("RES-000001", "Alfred", "Manager of Administration", "estate://residents/res-000001", "estate://source/1"),
            ResidentProfile("RES-000002", "Ingrid", "Manager of Security", "estate://residents/res-000002", "estate://source/2"),
            ResidentProfile("RES-000003", "Helen", "Manager of Human Resources", "estate://residents/res-000003", "estate://source/3"),
            ResidentProfile("grace", "Grace", "bounded operational intake", "riverview://grace", "riverview://grace", is_grace=True),
        )
    )


def provider(request: ReasoningRequest) -> ReasoningResponse:
    return ReasoningResponse(uuid4(), request.request_id, request.correlation_id, "local:test", "advice", f"response for {request.context_refs[0]}", (request.context_refs[0],), request.classification, datetime.now(UTC))


def test_named_sessions_preserve_identity_and_switch_without_bleed() -> None:
    service = gateway()
    alfred, _, alfred_meta = service.chat("Alfred", "Good evening, Alfred.", provider=provider, interface_id="browser")
    helen, _, helen_meta = service.chat("Helen", "Good evening, Helen.", provider=provider, interface_id="browser")
    assert alfred.session_id != helen.session_id
    assert alfred_meta["resident_id"] == "RES-000001"
    assert helen_meta["resident_id"] == "RES-000003"
    assert alfred_meta["canonical_reference"] != helen_meta["canonical_reference"]


def test_grace_is_addressable_but_work_requires_explicit_seed_promotion() -> None:
    _, _, metadata = gateway().chat("Grace", "Grace, please explain the current objective.", provider=provider, interface_id="browser")
    assert metadata["grace_addressed"]
    assert not metadata["execution_intent_detected"]
    _, _, authorized = gateway().chat("Grace", "Grace, authorize and create work for this objective.", provider=provider, interface_id="browser")
    assert authorized["execution_intent_detected"]
    assert authorized["execution_requires_seed_promotion"]
    assert not authorized["role_authority_expanded"]


def test_room_preserves_participants_and_denies_unknown_speakers() -> None:
    service = gateway()
    room_id = service.create_room(("Alfred", "Ingrid", "Helen"))
    turn = service.add_room_turn(room_id, speaker="Ingrid", text="Security context remains bounded.")
    snapshot = service.room_snapshot(room_id)
    assert snapshot["participants"] == ["RES-000001", "RES-000002", "RES-000003"]
    assert turn["speaker_id"] == "RES-000002"
    assert snapshot["no_authority_expansion"] is True
    with pytest.raises(PermissionError, match="not an admitted resident"):
        service.add_room_turn(room_id, speaker="Grace", text="Attempted authority transfer.")
