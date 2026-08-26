"""GRC-003-E2 high-reasoning request, lineage, and failure boundaries."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from riverview.reasoning import (
    HIGH_REASONING_CAPABILITY, AuthorizedHighReasoningProvider, BindingConfigurationLoader,
    CognitionBindingAdapter, CognitionProvenanceWriter, CognitionTier,
    ConsequenceClass, EscalationDecision, EscalationPolicy, HighReasoningCoordinator,
    HighReasoningExecutionError, HighReasoningInvocation, ReasoningAssemblyRequest,
    ResidentReasoningPacketAssembler, ReasoningResponse,
)
from riverview.reasoning.escalation_policy import CapacitySnapshot, POLICY_VERSION
from test_e1_home_cognition import MemoryEventStore, grace_state


AUTH = "authority://grace/high/e2"


def packet_and_assessment(store, classification="internal"):
    state = grace_state()
    now = datetime.now(UTC)
    packet = ResidentReasoningPacketAssembler().assemble(
        state.context_bundle,
        ReasoningAssemblyRequest(
            packet_id=uuid4(), resident_id=state.resident_id, occupant_id=state.occupant_id,
            implementation_id=state.implementation_id, source_cognition_event_id=uuid4(),
            objective_id=uuid4(), correlation_id=uuid4(), cognition_tier=CognitionTier.HIGH_REASONING,
            request_class="high_reasoning_review", objective="Resolve a consequential ambiguity safely.",
            exact_question="Which bounded advisory path is appropriate?",
            home_assessment="Home cognition believes stronger reasoning may help.",
            requested_output_schema="grace-high-reasoning-e2-v1",
            egress_policy="provider-neutral-authorized-local-advisory", classification=classification,
            max_budget=16000, expires_at=now + timedelta(minutes=5),
            constraints=("advisory only",), causation_id=None,
        ),
    )
    assessment = EscalationPolicy().evaluate(
        packet, consequence=ConsequenceClass.DIFFICULT, home_belief=True,
        home_belief_reason="Home reliability is exceeded.", requested_tier=CognitionTier.HIGH_REASONING,
        capacity=CapacitySnapshot(high_reasoning_available=True), now=now,
    )
    return state, packet, assessment


def provider(summary=None, **changes):
    calls = []
    value = {"recommendation":"Use the bounded advisory path.", "rationale":"The evidence supports review.",
             "uncertainty":None, "confidence":0.8, "constraints":["advisory only"],
             "unresolved_questions":[], "further_escalation_warranted":False,
             "authority_scope":["return:advisory"], "live_generation":True,
             "provenance_refs":["provider://e2/response"]}
    value.update(changes)
    def generate(request):
        calls.append(request)
        return ReasoningResponse(uuid4(), request.request_id, request.correlation_id, "provider:e2-fixture",
            "analysis", summary or json.dumps(value), ("provider://e2/response",), request.classification, datetime.now(UTC))
    return generate, calls


def coordinator(store, generate, rows=None, provider_id="provider:e2-fixture"):
    config = BindingConfigurationLoader.from_mapping({"HIGH_REASONING": {
        "capability_name": HIGH_REASONING_CAPABILITY, "policy_ref": POLICY_VERSION,
        "configuration_ref":"config://high/e2", "resource_class_ref":"resource-class://high"}})
    row = {"participant_id":"participant:e2", "provider_id":provider_id, "provider_type":"fixture",
           "role":"advisory", "health":"healthy", "capacity":2,
           "capability_name":HIGH_REASONING_CAPABILITY, "contract_version":"fixture-v1", "classification":True}
    catalog_rows = [row] if rows is None else rows
    return HighReasoningCoordinator(event_store=store, binding_adapter=CognitionBindingAdapter(type("C", (), {"available_for":lambda *_a,**_k: catalog_rows})(), config),
        provider=AuthorizedHighReasoningProvider(provider_id, AUTH, generate))


def test_high_reasoning_requires_p1_and_emits_live_f2_lineage():
    store = MemoryEventStore()
    state, packet, assessment = packet_and_assessment(store)
    generate, calls = provider()
    outcome = coordinator(store, generate).execute(HighReasoningInvocation(packet, assessment, AUTH))
    assert outcome.result.cognition_tier is CognitionTier.HIGH_REASONING
    assert outcome.result.live_generation is True and outcome.result.authority_scope == ("return:advisory",)
    assert len(calls) == 1 and calls[0].request_type == "analysis"
    assert "high_reasoning_required" in calls[0].instruction
    lineage = CognitionProvenanceWriter(store).reconstruct(outcome.request.request_id)
    assert [item.event_type.value for item in lineage] == ["cognition.requested", "cognition.started", "cognition.completed"]


def test_high_reasoning_denied_without_matching_p1_and_never_falls_back():
    store = MemoryEventStore(); _, packet, assessment = packet_and_assessment(store)
    generate, calls = provider()
    denied = replace(assessment, decision=EscalationDecision.POLICY_DENIED, policy_permitted=False,
                     capacity_eligible=False, target_tier=CognitionTier.HIGH_REASONING)
    with pytest.raises(HighReasoningExecutionError, match="authorization"):
        coordinator(store, generate).execute(HighReasoningInvocation(packet, denied, AUTH))
    assert not calls


def test_high_provider_unavailable_is_truthful_and_lineaged():
    store = MemoryEventStore(); _, packet, assessment = packet_and_assessment(store)
    generate, calls = provider()
    outcome = coordinator(store, generate, rows=[]).execute(HighReasoningInvocation(packet, assessment, AUTH))
    assert outcome.result.status.value == "unavailable" and not outcome.result.live_generation and not calls


@pytest.mark.parametrize("changes", [{"live_generation":False}, {"authority_scope":["execute"]}, {"provenance_refs":[]}])
def test_malformed_false_live_and_authority_widening_are_rejected(changes):
    store = MemoryEventStore(); _, packet, assessment = packet_and_assessment(store)
    generate, calls = provider(**changes)
    outcome = coordinator(store, generate).execute(HighReasoningInvocation(packet, assessment, AUTH))
    assert len(calls) == 1 and outcome.result.status.value == "malformed" and not outcome.result.live_generation


def test_identity_and_binding_mismatch_fail_closed():
    store = MemoryEventStore(); _, packet, assessment = packet_and_assessment(store)
    generate, calls = provider()
    with pytest.raises(HighReasoningExecutionError, match="does not correspond"):
        coordinator(store, generate).execute(HighReasoningInvocation(packet, replace(assessment, correlation_id=uuid4()), AUTH))
    assert not calls
    store = MemoryEventStore(); _, packet, assessment = packet_and_assessment(store)
    generate, calls = provider()
    outcome = coordinator(store, generate, rows=[{"participant_id":"participant:e2", "provider_id":"other",
        "provider_type":"fixture", "role":"advisory", "health":"healthy", "capacity":2,
        "capability_name":HIGH_REASONING_CAPABILITY, "classification":True}]).execute(HighReasoningInvocation(packet, assessment, AUTH))
    assert outcome.result.status.value == "unavailable" and not calls
