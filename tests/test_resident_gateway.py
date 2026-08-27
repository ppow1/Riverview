import json
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


def test_grace_is_addressable_but_prose_work_request_is_not_authorized() -> None:
    _, _, metadata = gateway().chat("Grace", "Grace, please explain the current objective.", provider=provider, interface_id="browser")
    assert metadata["grace_addressed"]
    assert not metadata["execution_intent_detected"]
    _, _, authorized = gateway().chat("Grace", "Grace, authorize and create work for this objective.", provider=provider, interface_id="browser")
    assert authorized["execution_intent_candidate"]
    assert not authorized["execution_intent_detected"]
    assert authorized["execution_requires_seed_promotion"]
    assert not authorized["role_authority_expanded"]


def test_grace_session_accepts_both_allowed_boundary_classifications() -> None:
    service = gateway()
    first, _, _ = service.chat("Grace", "Hello.", provider=provider, interface_id="browser", classification="internal")
    second, _, _ = service.chat("Grace", "Good evening.", provider=provider, interface_id="browser", classification="operational", session_id=first.session_id)
    assert second.session_id == first.session_id
    assert len(second.history) == 4


def test_grace_structured_provider_response_is_validated_and_rendered_for_pending_approval() -> None:
    contract = {
        "repository_identity": "ppow1/Riverview",
        "repository_root": "A:/Riverview/repo",
        "expected_base_sha": "a" * 40,
        "bounded_instruction": "Inspect the repository read-only and return evidence.",
        "allowed_paths": ["AI_HINTS.md"],
        "acceptance_criteria": ["change zero files"],
        "evidence_requirements": ["return the exact Git HEAD"],
        "capability_name": "codex.engineering.v1",
        "action_type": "codex.engineering.v1",
        "timeout_seconds": 300,
        "write_policy": "read_only",
    }

    def structured_provider(request: ReasoningRequest) -> ReasoningResponse:
        assert request.response_format is not None
        return ReasoningResponse(
            uuid4(), request.request_id, request.correlation_id, "ollama:test", "advice",
            json.dumps({"response_text": "Bounded proposal ready for Steward review.", "proposal": {
                "content": "Inspect Riverview read-only.", "summary": "Read-only inspection",
                "seed_text": "Create one bounded inspection objective.", "formation_contract": contract,
            }}), ("provider://ollama/test",), request.classification, datetime.now(UTC),
        )

    _, response, metadata = gateway().chat(
        "Grace", "Grace, prepare a bounded read-only inspection proposal.",
        provider=structured_provider, interface_id="browser",
    )
    assert "Bounded proposal ready" in response.summary
    assert "<RIVERVIEW_SPECIFICATION_V1>" in response.summary
    assert metadata["execution_intent_detected"] is False


def test_grace_marker_only_ollama_response_fails_closed() -> None:
    def marker_provider(request: ReasoningRequest) -> ReasoningResponse:
        return ReasoningResponse(
            uuid4(), request.request_id, request.correlation_id, "ollama:test", "advice",
            "<REDACTED>", ("provider://ollama/test",), request.classification, datetime.now(UTC),
        )

    with pytest.raises(RuntimeError, match="structured Grace JSON"):
        gateway().chat("Grace", "Grace, prepare a bounded proposal.", provider=marker_provider, interface_id="browser")


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
