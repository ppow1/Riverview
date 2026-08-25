from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

import pytest

from riverview.reasoning import (
    CapabilityResourceRequest,
    CognitionActorClass,
    CognitionFailureCode,
    CognitionResult,
    CognitionResultStatus,
    CognitionTier,
    EscalationAssessment,
    EscalationDecision,
    ResidentReasoningPacket,
)


def future(minutes: int = 10) -> datetime:
    return datetime.now(UTC) + timedelta(minutes=minutes)


def past() -> datetime:
    return datetime.now(UTC) - timedelta(seconds=1)


def packet(*, tier: CognitionTier = CognitionTier.HOME_COGNITION) -> ResidentReasoningPacket:
    return ResidentReasoningPacket(
        packet_id=uuid4(),
        resident_id=RESIDENT,
        occupant_id=OCCUPANT,
        office_id=OFFICE,
        implementation_id=IMPLEMENTATION,
        source_cognition_event_id=EVENT,
        objective_id=OBJECTIVE,
        authority_ref="authority://grace/operations",
        cognition_tier=tier,
        request_class="routine_operational_cognition",
        objective="Keep the accepted objective moving safely.",
        question="What is the next bounded operational decision?",
        operational_state_refs=("state://objective/1",),
        evidence_refs=("evidence://objective/1",),
        constraints=("Do not execute without the governed action path.",),
        authoritative_current_state_refs=("state://authoritative/objective/1",),
        unresolved_ambiguity=("No unresolved ambiguity.",),
        relevant_prior_decisions=("decision://objective/previous",),
        known_deterministic_results=("Dependency remains ready.",),
        home_assessment="Routine bounded cognition is appropriate.",
        requested_output_schema="recommendation,rationale,uncertainty,next_step",
        egress_policy="local-only-unless-policy-permits",
        max_budget=16000,
        classification="operational",
        correlation_id=CORRELATION,
        packet_digest=sha256(b"bounded-packet").hexdigest(),
        expires_at=future(),
        source_context_id=CONTEXT,
    )


def capability_request(*, tier: CognitionTier = CognitionTier.HOME_COGNITION) -> CapabilityResourceRequest:
    return CapabilityResourceRequest(
        request_id=REQUEST,
        correlation_id=CORRELATION,
        resident_id=RESIDENT,
        occupant_id=OCCUPANT,
        office_id=OFFICE,
        implementation_id=IMPLEMENTATION,
        authority_ref="authority://grace/operations",
        cognition_tier=tier,
        required_capability="resident_reasoning",
        classification="operational",
        policy_ref="policy://grace/cognition/v1",
        authorization_ref="authority://grace/operations",
        priority=10,
        deadline_at=future(),
        latency_requirement="bounded-interactive",
        exclusions=("unapproved-provider",),
        constraints=("return advisory reasoning only",),
    )


def result(*, tier: CognitionTier = CognitionTier.HOME_COGNITION, actor: CognitionActorClass = CognitionActorClass.GRACE_HOME_COGNITION) -> CognitionResult:
    created = datetime.now(UTC)
    return CognitionResult(
        result_id=uuid4(),
        request_id=REQUEST,
        correlation_id=CORRELATION,
        resident_id=RESIDENT,
        occupant_id=OCCUPANT,
        office_id=OFFICE,
        implementation_id=IMPLEMENTATION,
        authority_ref="authority://grace/operations",
        source_cognition_event_id=EVENT,
        cognition_tier=tier,
        status=CognitionResultStatus.COMPLETED,
        recommendation="Continue through the accepted bounded path.",
        rationale="The authoritative state supports the routine recommendation.",
        uncertainty=None,
        confidence=0.9,
        constraints=("No direct execution authority.",),
        unresolved_questions=(),
        further_escalation_warranted=False,
        provider_ref="provider://approved/instance",
        resource_class_ref="resource-class://resident-reasoning",
        packet_id=PACKET_ID,
        policy_decision_ref="policy-decision://1",
        provenance_refs=("provenance://request/1",),
        live_generation=True,
        actor_class=actor,
        classification="operational",
        created_at=created,
        expires_at=created + timedelta(minutes=5),
    )


RESIDENT = uuid4()
OCCUPANT = uuid4()
OFFICE = uuid4()
CORRELATION = uuid4()
REQUEST = uuid4()
CONTEXT = uuid4()
PACKET_ID = uuid4()
IMPLEMENTATION = uuid4()
EVENT = uuid4()
OBJECTIVE = uuid4()


def test_valid_home_high_and_external_contracts_are_distinct() -> None:
    assert packet().cognition_tier is CognitionTier.HOME_COGNITION
    assert packet(tier=CognitionTier.HIGH_REASONING).cognition_tier is CognitionTier.HIGH_REASONING
    assert packet(tier=CognitionTier.EXTERNAL_ESCALATION).cognition_tier is CognitionTier.EXTERNAL_ESCALATION
    assert capability_request(tier=CognitionTier.HIGH_REASONING).cognition_tier is CognitionTier.HIGH_REASONING


def test_unknown_tier_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        packet(tier="RTX_4090")  # type: ignore[arg-type]


def test_resident_identity_and_correlation_are_required() -> None:
    with pytest.raises(ValueError, match="resident_id"):
        replace(packet(), resident_id="grace")  # type: ignore[arg-type]


def test_packet_is_bounded_and_has_no_transcript_surface() -> None:
    p = packet()
    assert "transcript" not in p.as_typed_payload()
    with pytest.raises(TypeError):
        ResidentReasoningPacket(**{**p.as_typed_payload(), "transcript": "x"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="exceeds"):
        ResidentReasoningPacket(
            packet_id=p.packet_id, resident_id=p.resident_id, occupant_id=p.occupant_id,
            office_id=p.office_id, authority_ref=p.authority_ref, cognition_tier=p.cognition_tier,
            implementation_id=p.implementation_id, source_cognition_event_id=p.source_cognition_event_id,
            objective_id=p.objective_id,
            request_class=p.request_class, objective=p.objective, question=p.question,
            operational_state_refs=tuple(f"state://{i}" for i in range(65)),
            evidence_refs=p.evidence_refs, constraints=p.constraints,
            authoritative_current_state_refs=p.authoritative_current_state_refs,
            unresolved_ambiguity=p.unresolved_ambiguity,
            relevant_prior_decisions=p.relevant_prior_decisions,
            known_deterministic_results=p.known_deterministic_results,
            home_assessment=p.home_assessment, requested_output_schema=p.requested_output_schema,
            egress_policy=p.egress_policy, max_budget=p.max_budget,
            classification=p.classification,
            correlation_id=p.correlation_id, packet_digest=p.packet_digest, expires_at=future(),
        )


def test_all_context_paths_have_field_and_aggregate_bounds() -> None:
    p = packet()
    with pytest.raises(ValueError, match="invalid reference"):
        replace(p, evidence_refs=("x" * 501,))
    with pytest.raises(ValueError, match="exceeds its bound"):
        replace(p, relevant_prior_decisions=tuple(f"decision://{i}" for i in range(65)))
    with pytest.raises(ValueError, match="aggregate bound"):
        replace(p, unresolved_ambiguity=("x" * 4_000,) * 16)
    with pytest.raises(ValueError, match="aggregate bound"):
        replace(p, objective="x" * 4_000, question="y" * 4_000, home_assessment="z" * 4_000,
                requested_output_schema="o" * 4_000, egress_policy="e" * 4_000,
                constraints=("c" * 4_000,) * 16)


def test_reference_based_packet_round_trip_preserves_complete_context() -> None:
    original = packet()
    restored = ResidentReasoningPacket.from_typed_payload(original.as_typed_payload())
    assert restored.authoritative_current_state_refs == original.authoritative_current_state_refs
    assert restored.relevant_prior_decisions == original.relevant_prior_decisions
    assert restored.known_deterministic_results == original.known_deterministic_results
    assert restored.requested_output_schema == original.requested_output_schema
    assert restored.egress_policy == original.egress_policy


def test_provider_or_resource_replacement_does_not_change_identity() -> None:
    first = result()
    second = replace(first, provider_ref="provider://replacement", resource_class_ref="resource-class://replacement")
    assert first.resident_id == second.resident_id == RESIDENT
    assert first.occupant_id == second.occupant_id == OCCUPANT
    assert first.office_id == second.office_id == OFFICE
    assert first.implementation_id == second.implementation_id == IMPLEMENTATION
    assert first.authority_ref == second.authority_ref == "authority://grace/operations"


def test_tier_transition_preserves_identity() -> None:
    home = result()
    high = replace(home, cognition_tier=CognitionTier.HIGH_REASONING, actor_class=CognitionActorClass.GRACE_HIGH_REASONING)
    external = replace(home, cognition_tier=CognitionTier.EXTERNAL_ESCALATION, actor_class=CognitionActorClass.EXTERNAL_REASONING)
    for candidate in (high, external):
        assert (candidate.resident_id, candidate.occupant_id, candidate.office_id) == (RESIDENT, OCCUPANT, OFFICE)
        assert candidate.implementation_id == IMPLEMENTATION
        assert candidate.authority_ref == "authority://grace/operations"


@pytest.mark.parametrize("field", ["resident_id", "occupant_id", "office_id", "implementation_id", "authority_ref"])
def test_result_identity_correspondence_is_fail_closed(field: str) -> None:
    request = capability_request()
    changed = replace(request, **{field: uuid4() if field != "authority_ref" else "authority://substituted"})
    with pytest.raises(ValueError, match=field):
        result().validate_against(changed)


def test_escalation_assessment_keeps_belief_policy_and_capacity_distinct() -> None:
    assessment = EscalationAssessment(
        assessment_id=uuid4(), resident_id=RESIDENT, occupant_id=OCCUPANT,
        office_id=OFFICE, implementation_id=IMPLEMENTATION,
        authority_ref="authority://grace/operations", source_cognition_event_id=EVENT,
            packet_id=PACKET_ID, objective_id=OBJECTIVE,
            correlation_id=CORRELATION, question="Which bounded path is safest?",
            authoritative_current_state_refs=("state://authoritative/1",),
            evidence_refs=("evidence://1",), constraints=("advisory only",),
            provenance_refs=("provenance://assessment/1",), home_belief=True,
        home_belief_reason="The question exceeds the home reliability envelope.",
        policy_permitted=True, policy_reason="The classification permits high reasoning.",
        capacity_eligible=True, capacity_reason="An eligible capability class is available.",
        decision=EscalationDecision.HIGH_REASONING_REQUIRED,
        reason_class="consequential_ambiguity", policy_ref="policy://grace/cognition/v1",
        classification="operational", created_at=datetime.now(UTC), expires_at=future(),
        target_tier=CognitionTier.HIGH_REASONING,
    )
    payload = assessment.as_typed_payload()
    assert payload["home_belief"] is True
    assert payload["policy_permitted"] is True
    assert payload["capacity_eligible"] is True
    assert payload["decision"] == "high_reasoning_required"


def test_policy_denial_is_not_collapsed_into_home_belief() -> None:
    assessment = EscalationAssessment(
        assessment_id=uuid4(), resident_id=RESIDENT, occupant_id=OCCUPANT,
        office_id=OFFICE, implementation_id=IMPLEMENTATION,
        authority_ref="authority://grace/operations", source_cognition_event_id=EVENT,
        packet_id=PACKET_ID, objective_id=OBJECTIVE,
        correlation_id=CORRELATION, question="Which bounded path is safest?",
        authoritative_current_state_refs=("state://authoritative/1",),
        evidence_refs=("evidence://1",), constraints=("advisory only",),
        provenance_refs=("provenance://assessment/1",), home_belief=True, home_belief_reason="Needs stronger judgment.",
        policy_permitted=False, policy_reason="Classification is not externally eligible.",
        capacity_eligible=True, capacity_reason="Capacity exists but policy denies it.",
        decision=EscalationDecision.POLICY_DENIED, reason_class="protected_boundary",
        policy_ref="policy://grace/cognition/v1", classification="operational",
        created_at=datetime.now(UTC), expires_at=future(),
    )
    assert assessment.home_belief is True
    assert assessment.policy_permitted is False
    assert assessment.capacity_eligible is True


def test_capability_request_is_topology_neutral() -> None:
    payload = capability_request(tier=CognitionTier.HIGH_REASONING).as_typed_payload()
    assert payload["cognition_tier"] == "HIGH_REASONING"
    assert not {"gpu_id", "model_name", "endpoint", "provider_hostname"}.intersection(payload)


def test_valid_home_high_and_external_results_are_advisory() -> None:
    assert result().status is CognitionResultStatus.COMPLETED
    high = result(tier=CognitionTier.HIGH_REASONING, actor=CognitionActorClass.GRACE_HIGH_REASONING)
    external = result(tier=CognitionTier.EXTERNAL_ESCALATION, actor=CognitionActorClass.EXTERNAL_REASONING)
    assert high.as_typed_payload()["authority_scope"] == ["return:advisory"]
    assert external.as_typed_payload()["actor_class"] == "external_reasoning"


def test_missing_rationale_and_authority_widening_are_rejected() -> None:
    base = result()
    with pytest.raises(ValueError, match="recommendation and rationale"):
        replace(base, rationale=None)
    with pytest.raises(ValueError, match="advisory"):
        replace(base, authority_scope=("execute",))


@pytest.mark.parametrize("status,code", [
    (CognitionResultStatus.UNAVAILABLE, CognitionFailureCode.UNAVAILABLE),
    (CognitionResultStatus.TIMEOUT, CognitionFailureCode.TIMEOUT),
    (CognitionResultStatus.POLICY_REFUSED, CognitionFailureCode.POLICY_REFUSED),
    (CognitionResultStatus.CAPACITY_UNAVAILABLE, CognitionFailureCode.CAPACITY_UNAVAILABLE),
])
def test_unavailable_and_timeout_results_are_truthful(status: CognitionResultStatus, code: CognitionFailureCode) -> None:
    base = result()
    failed = replace(
        base, status=status, recommendation=None, rationale=None, provider_ref=None,
        resource_class_ref=None, live_generation=False, failure_code=code,
        failure_reason=code.value,
    )
    assert failed.live_generation is False
    assert failed.failure_code is code


def test_correlation_tier_classification_and_resident_mismatch_are_rejected() -> None:
    request = capability_request()
    valid = result()
    valid.validate_against(request)
    with pytest.raises(ValueError, match="correlation_id"):
        replace(valid, correlation_id=uuid4()).validate_against(request)
    with pytest.raises(ValueError, match="tier"):
        replace(valid, cognition_tier=CognitionTier.HIGH_REASONING).validate_against(request)
    with pytest.raises(ValueError, match="resident_id"):
        replace(valid, resident_id=uuid4()).validate_against(request)
    with pytest.raises(ValueError, match="classification"):
        replace(valid, classification="private").validate_against(request)


def test_expired_packet_and_request_are_rejected() -> None:
    p = packet()
    with pytest.raises(ValueError, match="expired"):
        replace(p, expires_at=past())
    with pytest.raises(ValueError, match="expired"):
        replace(capability_request(), deadline_at=past())


def test_deterministic_result_cannot_claim_live_generation() -> None:
    base = result()
    with pytest.raises(ValueError, match="deterministic"):
        replace(base, actor_class=CognitionActorClass.DETERMINISTIC_SUBSTRATE)
    deterministic = replace(base, actor_class=CognitionActorClass.DETERMINISTIC_SUBSTRATE, live_generation=False)
    assert deterministic.live_generation is False


def test_serialization_preserves_version_and_identity() -> None:
    payload = packet().as_typed_payload()
    assert payload["schema_version"] == "riverview-cognition-f1-v1"
    assert payload["resident_id"] == str(RESIDENT)
    assert payload["occupant_id"] == str(OCCUPANT)
    restored = ResidentReasoningPacket.from_typed_payload(payload)
    assert restored.packet_id == packet_id_from(payload)
    assert restored.resident_id == RESIDENT
    assert restored.cognition_tier is CognitionTier.HOME_COGNITION
    restored_result = CognitionResult.from_typed_payload(result().as_typed_payload())
    assert restored_result.occupant_id == OCCUPANT
    assert restored_result.authority_scope == ("return:advisory",)


def packet_id_from(payload: dict[str, object]):
    from uuid import UUID

    return UUID(str(payload["packet_id"]))
