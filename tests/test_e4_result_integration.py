"""GRC-003-E4 higher-tier result return, replay, and authority boundaries."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4
import pytest

from riverview.reasoning import (CognitionProvenanceWriter, GraceResultIntegrator,
    ResultIntegrationError)
from test_e1_home_cognition import MemoryEventStore
from test_e2_high_reasoning import AUTH, coordinator, packet_and_assessment, provider
from test_e3_external_advisory import ext_fixture


def high_result():
    store=MemoryEventStore(); _, packet, assessment=packet_and_assessment(store)
    generate,_=provider(); outcome=coordinator(store,generate).execute(__import__('riverview.reasoning',fromlist=['HighReasoningInvocation']).HighReasoningInvocation(packet,assessment,AUTH))
    return store, outcome


def test_high_result_returns_to_same_grace_session_and_replays_idempotently():
    store, outcome=high_result(); integrator=GraceResultIntegrator(store)
    first=integrator.integrate(outcome.result,outcome.session,outcome.request,turn=outcome.turn)
    second=integrator.integrate(outcome.result,outcome.session,outcome.request,turn=outcome.turn)
    assert first.result_id == second.result_id and second.idempotent_replay
    assert first.occupant_id == outcome.session.occupant_id
    assert first.authority_scope == ("return:advisory",)
    assert len([r for r in store.read_aggregate("cognition_request", outcome.request.request_id) if r["event_type"] == "cognition.integrated"]) == 1
    reconstructed = CognitionProvenanceWriter(store).reconstruct(outcome.request.request_id)
    assert any(event.event_type.value == "cognition.integrated" and event.result_id == outcome.result.result_id for event in reconstructed)


def test_external_result_integrates_as_external_advisory_without_authority():
    store=MemoryEventStore(); service, invocation, _=ext_fixture(store)
    outcome=service.execute(invocation)
    integrated=GraceResultIntegrator(store).integrate(outcome.result,outcome.session,outcome.request,turn=outcome.turn)
    assert integrated.cognition_tier.value == "EXTERNAL_ESCALATION"
    assert integrated.authority_scope == ("return:advisory",)


@pytest.mark.parametrize("field", ["request_id","correlation_id","resident_id","occupant_id","office_id","implementation_id","packet_id","policy_decision_ref","cognition_tier"])
def test_wrong_result_correspondence_fails_closed(field):
    store,outcome=high_result(); result=outcome.result
    value="forged-policy" if field == "policy_decision_ref" else (uuid4() if field not in {"cognition_tier"} else __import__('riverview.reasoning',fromlist=['CognitionTier']).CognitionTier.EXTERNAL_ESCALATION)
    with pytest.raises((ResultIntegrationError, ValueError)):
        forged=replace(result, **{field:value})
        GraceResultIntegrator(store).integrate(forged,outcome.session,outcome.request,turn=outcome.turn)


def test_malformed_false_generation_and_authority_widening_are_rejected():
    store,outcome=high_result(); integrator=GraceResultIntegrator(store)
    with pytest.raises((ResultIntegrationError, ValueError)):
        integrator.integrate(replace(outcome.result,live_generation=False),outcome.session,outcome.request,turn=outcome.turn)
    with pytest.raises((ResultIntegrationError, ValueError)):
        integrator.integrate(replace(outcome.result,authority_scope=("execute",)),outcome.session,outcome.request,turn=outcome.turn)


def test_conflicting_duplicate_and_wrong_session_are_rejected():
    store,outcome=high_result(); integrator=GraceResultIntegrator(store)
    integrator.integrate(outcome.result,outcome.session,outcome.request,turn=outcome.turn)
    conflict=replace(outcome.result,result_id=uuid4())
    with pytest.raises(ResultIntegrationError,match="conflicting"):
        integrator.integrate(conflict,outcome.session,outcome.request,turn=outcome.turn)
    wrong=replace(outcome.session,session_id=uuid4())
    with pytest.raises(ResultIntegrationError): integrator.integrate(outcome.result,wrong,outcome.request,turn=outcome.turn)
