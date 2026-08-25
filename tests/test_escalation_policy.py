"""GRC-003-P1 deterministic escalation policy tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID, uuid4

import pytest

from riverview.reasoning import (
    CognitionProvenance,
    CognitionProvenanceWriter,
    CognitionTier,
    EscalationDecision,
    ResidentReasoningPacket,
)
from riverview.reasoning.escalation_policy import (
    POLICY_EVENT_TYPE,
    CapacitySnapshot,
    ConsequenceClass,
    EscalationPolicy,
    PolicyDecisionRecorder,
    PolicyInputError,
)


RESIDENT = UUID("11111111-1111-1111-1111-111111111111")
OCCUPANT = UUID("22222222-2222-2222-2222-222222222222")
OFFICE = UUID("33333333-3333-3333-3333-333333333333")
IMPLEMENTATION = UUID("44444444-4444-4444-4444-444444444444")
EVENT = UUID("55555555-5555-5555-5555-555555555555")
OBJECTIVE = UUID("66666666-6666-6666-6666-666666666666")
CORRELATION = UUID("77777777-7777-7777-7777-777777777777")


def packet(*, classification: str = "operational") -> ResidentReasoningPacket:
    return ResidentReasoningPacket(
        packet_id=uuid4(), resident_id=RESIDENT, occupant_id=OCCUPANT, office_id=OFFICE,
        implementation_id=IMPLEMENTATION, source_cognition_event_id=EVENT, objective_id=OBJECTIVE,
        authority_ref="authority://grace/operations", cognition_tier=CognitionTier.HOME_COGNITION,
        request_class="routine_operational_cognition", objective="Bounded objective",
        question="What is the next safe decision?", operational_state_refs=("state://1",),
        evidence_refs=("evidence://1",), constraints=("advisory only",),
        authoritative_current_state_refs=("state://authoritative/1",), unresolved_ambiguity=(),
        relevant_prior_decisions=(), known_deterministic_results=(), home_assessment="home assessment",
        requested_output_schema="recommendation,rationale", egress_policy="advisory-only", max_budget=16000,
        classification=classification, correlation_id=CORRELATION, packet_digest=sha256(b"p").hexdigest(),
        expires_at=datetime.now(UTC) + timedelta(minutes=10), source_context_id=uuid4(),
    )


class MemoryEventStore:
    def __init__(self) -> None:
        self.events: list[object] = []

    def append(self, event):
        self.events.append(event)
        return event

    def read_aggregate(self, aggregate_type, aggregate_id):
        return [
            {"payload": dict(event.payload), "event_type": event.event_type}
            for event in self.events
            if event.aggregate_type == aggregate_type and event.aggregate_id == aggregate_id
        ]


def test_routine_home_decision_is_deterministic_and_does_not_escalate() -> None:
    assessment = EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.ROUTINE, home_belief=False, home_belief_reason="Routine work fits the home envelope.")
    assert assessment.decision is EscalationDecision.DETERMINISTIC
    assert assessment.policy_permitted is True
    assert assessment.target_tier is None


def test_difficult_home_belief_requires_high_only_when_capacity_is_eligible() -> None:
    assessment = EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.DIFFICULT, home_belief=True, home_belief_reason="Home reliability is exceeded.", capacity=CapacitySnapshot(high_reasoning_available=True))
    assert assessment.decision is EscalationDecision.HIGH_REASONING_REQUIRED
    assert assessment.policy_permitted is True and assessment.capacity_eligible is True
    assert assessment.target_tier is CognitionTier.HIGH_REASONING


def test_empty_capacity_is_truthful_block_and_never_silently_downgrades() -> None:
    assessment = EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.DIFFICULT, home_belief=True, home_belief_reason="Home reliability is exceeded.", capacity=CapacitySnapshot())
    assert assessment.decision is EscalationDecision.CAPACITY_UNAVAILABLE
    assert assessment.policy_permitted is True and assessment.capacity_eligible is False
    assert assessment.target_tier is CognitionTier.HIGH_REASONING


def test_pointless_escalation_does_not_become_a_provider_request() -> None:
    assessment = EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.DIFFICULT, home_belief=False, home_belief_reason="Home can handle this.", capacity=CapacitySnapshot(high_reasoning_available=True))
    assert assessment.decision is EscalationDecision.HOME_DECISION
    assert assessment.target_tier is None


@pytest.mark.parametrize("consequence", [ConsequenceClass.CONSEQUENTIAL_AMBIGUITY, ConsequenceClass.PROTECTED_BOUNDARY, ConsequenceClass.UNKNOWN])
def test_unsafe_or_unknown_consequence_requires_steward(consequence: ConsequenceClass) -> None:
    assessment = EscalationPolicy().evaluate(packet(), consequence=consequence, home_belief=True, home_belief_reason="Material ambiguity remains.", capacity=CapacitySnapshot(high_reasoning_available=True, external_escalation_available=True))
    assert assessment.decision is EscalationDecision.STEWARD_REQUIRED
    assert assessment.policy_permitted is False
    assert assessment.capacity_eligible is False


def test_external_policy_denied_by_classification_even_when_capacity_exists() -> None:
    assessment = EscalationPolicy().evaluate(packet(classification="private"), consequence=ConsequenceClass.DIFFICULT, home_belief=True, home_belief_reason="Independent advisory review may help.", requested_tier=CognitionTier.EXTERNAL_ESCALATION, capacity=CapacitySnapshot(external_escalation_available=True))
    assert assessment.decision is EscalationDecision.POLICY_DENIED
    assert assessment.policy_permitted is False and assessment.capacity_eligible is True


def test_unknown_inputs_and_missing_authority_fail_closed() -> None:
    with pytest.raises(PolicyInputError):
        EscalationPolicy().evaluate(packet(), consequence="not-a-class", home_belief=True, home_belief_reason="x")
    with pytest.raises(PolicyInputError):
        EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.ROUTINE, home_belief=True, home_belief_reason="")
    with pytest.raises(ValueError):
        EscalationPolicy().evaluate(replace(packet(), authority_ref=""), consequence=ConsequenceClass.ROUTINE, home_belief=False, home_belief_reason="routine")


def test_policy_decision_persists_version_and_outcome_as_f2_river_event() -> None:
    store = MemoryEventStore()
    assessment = EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.DIFFICULT, home_belief=True, home_belief_reason="Home reliability is exceeded.", capacity=CapacitySnapshot(high_reasoning_available=True))
    request = _request_for_assessment(assessment)
    request_record = CognitionProvenance.for_request(request, source_event_id=EVENT, office_id=OFFICE, implementation_id=IMPLEMENTATION, authority_ref=assessment.authority_ref)
    CognitionProvenanceWriter(store).record(request_record)
    PolicyDecisionRecorder(store).record(assessment, request_id=request.request_id)
    event = store.events[1]
    assert event.event_type == POLICY_EVENT_TYPE
    assert event.aggregate_type == "cognition_request"
    assert event.payload["policy_version"] == assessment.policy_ref
    assert event.payload["decision"] == assessment.decision.value
    assert event.payload["assessment"]["assessment_id"] == str(assessment.assessment_id)


def test_policy_event_payload_is_reconstructable_after_store_recreation() -> None:
    store = MemoryEventStore()
    assessment = EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.ROUTINE, home_belief=False, home_belief_reason="Routine is within home capability.")
    request = _request_for_assessment(assessment)
    request_record = CognitionProvenance.for_request(request, source_event_id=EVENT, office_id=OFFICE, implementation_id=IMPLEMENTATION, authority_ref=assessment.authority_ref)
    CognitionProvenanceWriter(store).record(request_record)
    PolicyDecisionRecorder(store).record(assessment, request_id=request.request_id)
    reloaded = MemoryEventStore()
    reloaded.events = list(store.events)
    row = reloaded.read_aggregate("cognition_request", request.request_id)[1]
    assert row["payload"]["policy_version"] == "grace-escalation-policy-p1-v1"
    assert row["payload"]["decision"] == "deterministic"


def _request_for_assessment(assessment: object):
    from test_cognition_contracts import capability_request
    request = replace(
        capability_request(),
        resident_id=assessment.resident_id,
        occupant_id=assessment.occupant_id,
        office_id=assessment.office_id,
        implementation_id=assessment.implementation_id,
        authority_ref=assessment.authority_ref,
        correlation_id=assessment.correlation_id,
        classification=assessment.classification,
    )
    return request


def _canonical_policy_store(assessment: object) -> tuple[MemoryEventStore, UUID]:
    request = _request_for_assessment(assessment)
    store = MemoryEventStore()
    request_record = CognitionProvenance.for_request(
        request, source_event_id=EVENT, office_id=OFFICE,
        implementation_id=IMPLEMENTATION, authority_ref=assessment.authority_ref,
    )
    CognitionProvenanceWriter(store).record(request_record)
    return store, request.request_id


def test_policy_recorder_rejects_unrelated_request_before_persistence() -> None:
    assessment = EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.DIFFICULT, home_belief=True, home_belief_reason="Home reliability is exceeded.", capacity=CapacitySnapshot(high_reasoning_available=True))
    store, request_id = _canonical_policy_store(assessment)
    with pytest.raises(PolicyInputError, match="canonical cognition request lineage"):
        PolicyDecisionRecorder(store).record(assessment, request_id=uuid4())
    assert len(store.events) == 1
    assert store.events[0].event_type != POLICY_EVENT_TYPE


@pytest.mark.parametrize("field", [
    "resident_id", "occupant_id", "office_id", "implementation_id",
    "authority_ref", "source_cognition_event_id", "correlation_id",
])
def test_policy_recorder_rejects_identity_or_lineage_substitution(field: str) -> None:
    assessment = EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.DIFFICULT, home_belief=True, home_belief_reason="Home reliability is exceeded.", capacity=CapacitySnapshot(high_reasoning_available=True))
    store, request_id = _canonical_policy_store(assessment)
    replacement = uuid4() if field.endswith("_id") else "authority://forged"
    forged = replace(assessment, **{field: replacement})
    with pytest.raises(PolicyInputError, match="correspondence mismatch"):
        PolicyDecisionRecorder(store).record(forged, request_id=request_id)
    assert len(store.events) == 1


def test_policy_recorder_rejects_unrelated_causation() -> None:
    assessment = EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.ROUTINE, home_belief=False, home_belief_reason="Home can handle this.")
    store, request_id = _canonical_policy_store(assessment)
    with pytest.raises(PolicyInputError, match="causation"):
        PolicyDecisionRecorder(store).record(assessment, request_id=request_id, causation_id=uuid4())
    assert len(store.events) == 1


def test_policy_recorder_rejects_missing_canonical_request() -> None:
    assessment = EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.ROUTINE, home_belief=False, home_belief_reason="Home can handle this.")
    store = MemoryEventStore()
    with pytest.raises(PolicyInputError, match="canonical cognition request lineage"):
        PolicyDecisionRecorder(store).record(assessment, request_id=uuid4())


def test_policy_event_coexists_with_f2_request_lineage() -> None:
    from test_cognition_provenance import MemoryEventStore
    store = MemoryEventStore()
    assessment = EscalationPolicy().evaluate(packet(), consequence=ConsequenceClass.ROUTINE, home_belief=False, home_belief_reason="Routine is within home capability.")
    request = _request_for_assessment(assessment)
    request_record = CognitionProvenance.for_request(
        request, source_event_id=EVENT, office_id=request.office_id,
        implementation_id=request.implementation_id, authority_ref=request.authority_ref,
    )
    CognitionProvenanceWriter(store).record(request_record)
    PolicyDecisionRecorder(store).record(assessment, request_id=request.request_id)
    reconstructed = CognitionProvenanceWriter(store).reconstruct(request.request_id)
    assert reconstructed == (request_record,)
    policy_rows = [row for row in store.read_aggregate("cognition_request", request.request_id) if row["payload"].get("event_type") == POLICY_EVENT_TYPE]
    assert len(policy_rows) == 1
