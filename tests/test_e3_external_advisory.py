"""GRC-003-E3 external advisory boundary tests."""

from datetime import UTC, datetime
from dataclasses import replace
import json

import pytest

from riverview.reasoning import (
    EXTERNAL_ADVISORY_CAPABILITY, AuthorizedHighReasoningProvider, BindingConfigurationLoader,
    CognitionBindingAdapter, CognitionProvenanceWriter, CognitionTier, EscalationDecision,
    ExternalAdvisoryCoordinator, HighReasoningExecutionError, HighReasoningInvocation,
    ReasoningResponse,
)
from riverview.reasoning.escalation_policy import CapacitySnapshot, EscalationPolicy
from test_e1_home_cognition import MemoryEventStore
from test_e2_high_reasoning import AUTH, packet_and_assessment


def ext_fixture(store, *, classification="operational", rows=None, changes=None):
    _, packet, _ = packet_and_assessment(store, classification)
    assessment = EscalationPolicy().evaluate(packet, consequence="difficult", home_belief=True,
        home_belief_reason="External independent advice is warranted.",
        requested_tier=CognitionTier.EXTERNAL_ESCALATION,
        capacity=CapacitySnapshot(external_escalation_available=True))
    calls = []
    value = {"recommendation":"Seek bounded external advice.","rationale":"Independent review is useful.",
             "uncertainty":None,"confidence":0.7,"constraints":["advisory only"],"unresolved_questions":[],
             "further_escalation_warranted":False,"authority_scope":["return:advisory"],
             "live_generation":True,"provenance_refs":["external://e3/response"]}
    value.update(changes or {})
    def generate(request):
        calls.append(request)
        return ReasoningResponse(__import__('uuid').uuid4(),request.request_id,request.correlation_id,
            "provider:e3-fixture","advice",json.dumps(value),("external://e3/response",),request.classification,datetime.now(UTC))
    config = BindingConfigurationLoader.from_mapping({"EXTERNAL_ESCALATION": {
        "capability_name":EXTERNAL_ADVISORY_CAPABILITY,"policy_ref":assessment.policy_ref,
        "configuration_ref":"config://external/e3","resource_class_ref":"resource-class://external"}})
    row = {"participant_id":"participant:e3","provider_id":"provider:e3-fixture","provider_type":"external-fixture",
           "role":"advisory","health":"healthy","capacity":1,"capability_name":EXTERNAL_ADVISORY_CAPABILITY,
           "contract_version":"fixture-v1","classification":True}
    catalog = type("Catalog", (), {"available_for":lambda *_a,**_k: rows if rows is not None else [row]})()
    service = ExternalAdvisoryCoordinator(event_store=store,
        binding_adapter=CognitionBindingAdapter(catalog, config),
        provider=AuthorizedHighReasoningProvider("provider:e3-fixture", AUTH, generate))
    return service, HighReasoningInvocation(packet, assessment, AUTH), calls


def test_approved_external_advice_is_external_advisory_and_persisted():
    store=MemoryEventStore(); service, invocation, calls=ext_fixture(store)
    outcome=service.execute(invocation)
    assert outcome.result.cognition_tier is CognitionTier.EXTERNAL_ESCALATION
    assert outcome.result.actor_class.value == "external_reasoning"
    assert outcome.result.live_generation and outcome.result.authority_scope == ("return:advisory",)
    assert len(calls)==1 and calls[0].request_type == "analysis"
    assert CognitionProvenanceWriter(store).reconstruct(outcome.request.request_id)[-1].event_type.value == "cognition.completed"


def test_external_requires_external_p1_and_never_falls_back():
    store=MemoryEventStore(); service, invocation, calls=ext_fixture(store)
    denied=replace(invocation.assessment, decision=EscalationDecision.HIGH_REASONING_REQUIRED,
                   target_tier=CognitionTier.HIGH_REASONING)
    with pytest.raises(HighReasoningExecutionError, match="authorization"):
        service.execute(HighReasoningInvocation(invocation.packet, denied, AUTH))
    assert not calls


@pytest.mark.parametrize("changes", [{"authority_scope":["execute"]},{"live_generation":False},{"provenance_refs":[]}])
def test_external_malformed_authority_and_false_generation_fail_closed(changes):
    store=MemoryEventStore(); service, invocation, calls=ext_fixture(store, changes=changes)
    outcome=service.execute(invocation)
    assert outcome.result.status.value == "malformed" and not outcome.result.live_generation


def test_external_provider_unavailable_and_binding_mismatch_are_truthful():
    store=MemoryEventStore(); service, invocation, calls=ext_fixture(store, rows=[])
    outcome=service.execute(invocation)
    assert outcome.result.status.value == "unavailable" and not calls
    store=MemoryEventStore(); service, invocation, calls=ext_fixture(store, rows=[{"participant_id":"p","provider_id":"other","provider_type":"fixture","role":"advisory","health":"healthy","capacity":1,"capability_name":EXTERNAL_ADVISORY_CAPABILITY,"classification":True}])
    outcome=service.execute(invocation)
    assert outcome.result.status.value == "unavailable" and not calls
