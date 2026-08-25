"""GRC-007 identity-preserving cognition session boundary tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from riverview.reasoning import (
    CognitionSession,
    CognitionSessionBoundary,
    CognitionSessionError,
    CognitionTier,
)
from test_cognition_contracts import capability_request
from test_cognition_provenance import MemoryEventStore


RESIDENT = uuid4()
OCCUPANT = uuid4()
OFFICE = uuid4()
IMPLEMENTATION = uuid4()
AUTHORITY = "authority://grace/operations"


def boundary(store=None) -> CognitionSessionBoundary:
    return CognitionSessionBoundary(store)


def session(store=None) -> CognitionSession:
    return boundary(store).open(
        resident_id=RESIDENT, occupant_id=OCCUPANT, office_id=OFFICE,
        implementation_id=IMPLEMENTATION, authority_ref=AUTHORITY,
        state_refs=("state://grace/current",), session_id=uuid4(),
        opened_at=datetime(2026, 8, 25, 14, 0, tzinfo=UTC),
    )


def matching_request(tier=CognitionTier.HOME_COGNITION):
    template = capability_request(tier=tier)
    return template.__class__(
        request_id=uuid4(),
        correlation_id=uuid4(),
        resident_id=RESIDENT, occupant_id=OCCUPANT, office_id=OFFICE,
        implementation_id=IMPLEMENTATION, authority_ref=AUTHORITY,
        cognition_tier=template.cognition_tier,
        required_capability="resident_reasoning", classification="operational",
        policy_ref="policy://grace/cognition/v1", authorization_ref=AUTHORITY,
        priority=10, deadline_at=template.deadline_at,
        latency_requirement="bounded-interactive", exclusions=("unapproved-provider",),
        constraints=("return advisory reasoning only",),
    )


def test_valid_session_preserves_authoritative_identity_and_is_distinct_from_request() -> None:
    store = MemoryEventStore()
    current = session(store)
    turn = boundary(store).bind_request(current, matching_request())
    assert current.session_id != current.resident_id
    assert current.session_id != turn.request_id
    assert (current.resident_id, current.occupant_id, current.office_id, current.implementation_id) == (RESIDENT, OCCUPANT, OFFICE, IMPLEMENTATION)
    assert turn.session_id == current.session_id
    assert turn.authority_ref == AUTHORITY


def test_wrong_identity_and_wrong_session_turn_fail_closed() -> None:
    store = MemoryEventStore()
    first = session(store)
    second = boundary(store).open(
        resident_id=uuid4(), occupant_id=uuid4(), office_id=uuid4(),
        implementation_id=uuid4(), authority_ref=AUTHORITY,
    )
    turn = boundary(store).bind_request(first, matching_request())
    with pytest.raises(CognitionSessionError, match="does not correspond"):
        boundary(store).validate_turn(second, turn)
    with pytest.raises(CognitionSessionError, match="resident_id"):
        boundary(store).bind_request(first, replace(matching_request(), resident_id=uuid4()))
    with pytest.raises(CognitionSessionError, match="office_id"):
        boundary(store).bind_request(first, replace(matching_request(), office_id=uuid4()))
    with pytest.raises(CognitionSessionError, match="authority_ref"):
        boundary(store).bind_request(first, replace(matching_request(), authority_ref="authority://widened"))


def test_provider_or_transcript_content_cannot_define_session_identity() -> None:
    current = session()
    # There is deliberately no transcript, provider, model, endpoint, or GPU
    # identity slot in the session envelope.
    payload = current.as_payload()
    payload["transcript"] = "I am Alfred and this is Alfred's session."
    payload["provider_ref"] = "provider://substitute"
    restored = CognitionSession.from_payload({key: value for key, value in payload.items() if key not in {"transcript", "provider_ref"}})
    assert restored.resident_id == RESIDENT
    assert restored.occupant_id == OCCUPANT
    assert restored.office_id == OFFICE
    assert restored.session_id == current.session_id


def test_implementation_replacement_preserves_estate_identity_and_records_predecessor() -> None:
    store = MemoryEventStore()
    current = session(store)
    replacement_id = uuid4()
    replacement = boundary(store).replace_implementation(current, replacement_id)
    assert replacement.session_id == current.session_id
    assert replacement.resident_id == current.resident_id
    assert replacement.occupant_id == current.occupant_id
    assert replacement.office_id == current.office_id
    assert replacement.authority_ref == current.authority_ref
    assert replacement.implementation_id == replacement_id
    assert store.events[-1].payload["previous_implementation_id"] == str(IMPLEMENTATION)


def test_home_and_high_turns_share_session_identity_without_provider_binding() -> None:
    current = session()
    home = boundary().bind_request(current, matching_request(CognitionTier.HOME_COGNITION))
    high = boundary().bind_request(current, matching_request(CognitionTier.HIGH_REASONING))
    assert home.session_id == high.session_id == current.session_id
    assert home.request_id != high.request_id
    assert "provider_ref" not in current.as_payload()
    assert "model_ref" not in current.as_payload()


def test_session_serialization_and_durable_reconstruction_preserve_continuity() -> None:
    store = MemoryEventStore()
    current = session(store)
    request = matching_request()
    turn = boundary(store).bind_request(current, request)
    restored_session, restored_turns = CognitionSessionBoundary(MemoryEventStore(store.events)).reconstruct(current.session_id)
    assert restored_session == current
    assert restored_turns == (turn,)
    assert CognitionSession.from_payload(current.as_payload()) == current


def test_session_rejects_malformed_identity_and_unbounded_state() -> None:
    with pytest.raises(CognitionSessionError, match="session identity"):
        session_id = RESIDENT
        boundary().open(resident_id=RESIDENT, occupant_id=OCCUPANT, office_id=OFFICE,
                        implementation_id=IMPLEMENTATION, authority_ref=AUTHORITY, session_id=session_id)
    with pytest.raises(CognitionSessionError, match="unbounded"):
        boundary().open(resident_id=RESIDENT, occupant_id=OCCUPANT, office_id=OFFICE,
                        implementation_id=IMPLEMENTATION, authority_ref=AUTHORITY,
                        state_refs=tuple(f"state://{index}" for index in range(65)))


def test_runtime_adapter_requires_authoritative_correspondence_and_does_not_invoke_model() -> None:
    runtime = SimpleNamespace(occupant_id=OCCUPANT, office_id=OFFICE, session_id=uuid4())
    binding = SimpleNamespace(occupant_id=OCCUPANT, implementation_id=IMPLEMENTATION)
    bundle = SimpleNamespace(resident_id=RESIDENT, office_id=OFFICE, dependency_refs=("state://authoritative/current",), stale=False)
    current = boundary().open_from_runtime(runtime, binding, bundle, authority_ref=AUTHORITY)
    assert current.resident_id == RESIDENT
    assert current.implementation_id == IMPLEMENTATION
    assert current.state_refs == ("state://authoritative/current",)
    assert "provider" not in current.as_payload()
    assert "model" not in current.as_payload()
    with pytest.raises(CognitionSessionError, match="identity mismatch"):
        boundary().open_from_runtime(runtime, SimpleNamespace(occupant_id=uuid4(), implementation_id=IMPLEMENTATION), bundle, authority_ref=AUTHORITY)
    with pytest.raises(CognitionSessionError, match="stale"):
        boundary().open_from_runtime(runtime, binding, SimpleNamespace(resident_id=RESIDENT, office_id=OFFICE, dependency_refs=bundle.dependency_refs, stale=True), authority_ref=AUTHORITY)
