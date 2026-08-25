"""GRC-006 cognition provenance and River lineage tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from riverview.reasoning import (
    CognitionActorClass,
    CognitionFailureCode,
    CognitionProvenance,
    CognitionProvenanceEventType,
    CognitionProvenanceWriter,
    CognitionResultStatus,
    CognitionTier,
    ProvenanceLineageError,
)
from riverview.river import RiverEvent
from test_cognition_contracts import OFFICE as REQUEST_OFFICE
from test_cognition_contracts import IMPLEMENTATION as REQUEST_IMPLEMENTATION
from test_cognition_contracts import capability_request, result


SOURCE_EVENT = uuid4()
OFFICE = REQUEST_OFFICE
IMPLEMENTATION = REQUEST_IMPLEMENTATION


class MemoryEventStore:
    """Restart-surviving test double for the existing EventStore protocol."""

    def __init__(self, events: list[RiverEvent] | None = None) -> None:
        self.events = events if events is not None else []

    def append(self, event: RiverEvent) -> SimpleNamespace:
        existing = next((item for item in self.events if item.idempotency_key == event.idempotency_key), None)
        if existing is not None:
            return SimpleNamespace(sequence_id=self.events.index(existing) + 1, event_id=existing.event_id, inserted=False)
        self.events.append(event)
        return SimpleNamespace(sequence_id=len(self.events), event_id=event.event_id, inserted=True)

    def read_aggregate(self, aggregate_type, aggregate_id):
        return [
            {
                "sequence_id": index + 1,
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "payload": dict(event.payload),
                "occurred_at": event.occurred_at.isoformat(),
            }
            for index, event in enumerate(self.events)
            if event.aggregate_type == aggregate_type and event.aggregate_id == aggregate_id
        ]


def request():
    return capability_request()


def test_request_event_uses_river_foundation_and_preserves_lineage() -> None:
    req = request()
    provenance = CognitionProvenance.for_request(
        req,
        source_event_id=SOURCE_EVENT,
        office_id=OFFICE,
        implementation_id=IMPLEMENTATION,
        authority_ref="authority://grace/operations",
        authoritative_state_refs=("state://current/1",),
        evidence_refs=("evidence://source/1",),
        event_id=uuid4(),
    )
    provenance.validate_against_request(req)
    event = provenance.to_river_event()
    assert isinstance(event, RiverEvent)
    assert event.aggregate_type == "cognition_request"
    assert event.aggregate_id == req.request_id
    assert event.correlation_id == req.correlation_id
    assert event.causation_id is None
    assert event.payload["source_event_id"] == str(SOURCE_EVENT)
    assert event.payload["resident_id"] == str(req.resident_id)
    assert event.payload["live_generation"] is False


def test_authoritative_event_type_vocabulary_is_complete() -> None:
    assert {item.value for item in CognitionProvenanceEventType} == {
        "cognition.requested", "cognition.admitted", "cognition.held", "cognition.started",
        "cognition.completed", "cognition.unavailable", "cognition.rejected",
        "cognition.timed_out", "cognition.integrated",
    }


def test_result_corresponds_to_exact_request_and_rejects_unrelated_request() -> None:
    req = request()
    response = result()
    response.validate_against(req)
    provenance = CognitionProvenance.for_result(response, source_event_id=SOURCE_EVENT)
    provenance.validate_against_request(req)
    with pytest.raises(ProvenanceLineageError, match="request_id|correlation_id"):
        provenance.validate_against_request(replace(req, request_id=uuid4()))


@pytest.mark.parametrize("tier,actor", [
    (CognitionTier.HIGH_REASONING, CognitionActorClass.GRACE_HIGH_REASONING),
    (CognitionTier.EXTERNAL_ESCALATION, CognitionActorClass.EXTERNAL_REASONING),
])
def test_live_high_and_external_events_require_truthful_observation(tier, actor) -> None:
    selected = result(tier=tier, actor=actor)
    record = CognitionProvenance.for_result(selected, source_event_id=SOURCE_EVENT)
    assert record.live_generation is True
    assert record.provider_ref == selected.provider_ref
    assert record.resource_class_ref == selected.resource_class_ref


def test_source_request_result_lineage_reconstructs_after_restart() -> None:
    req = request()
    response = result()
    store = MemoryEventStore()
    writer = CognitionProvenanceWriter(store)
    request_record = CognitionProvenance.for_request(
        req, source_event_id=SOURCE_EVENT, office_id=OFFICE,
        implementation_id=IMPLEMENTATION, authority_ref="authority://grace/operations",
        event_id=uuid4(), occurred_at=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
    )
    result_record = CognitionProvenance.for_result(
        response, source_event_id=SOURCE_EVENT, causation_id=request_record.event_id,
        event_id=uuid4(), occurred_at=datetime(2026, 8, 25, 12, 1, tzinfo=UTC),
    )
    writer.record(request_record)
    writer.record(result_record)
    reloaded = CognitionProvenanceWriter(MemoryEventStore(store.events)).reconstruct(req.request_id)
    assert [record.event_type for record in reloaded] == [CognitionProvenanceEventType.REQUESTED, CognitionProvenanceEventType.COMPLETED]
    assert reloaded[1].causation_id == reloaded[0].event_id
    assert reloaded[1].source_event_id == SOURCE_EVENT
    assert reloaded[1].occurred_at == datetime(2026, 8, 25, 12, 1, tzinfo=UTC)


def test_idempotent_duplicate_is_safe_but_conflicting_payload_is_rejected() -> None:
    req = request()
    record = CognitionProvenance.for_request(
        req, source_event_id=SOURCE_EVENT, office_id=OFFICE,
        implementation_id=IMPLEMENTATION, authority_ref="authority://grace/operations", event_id=uuid4(),
    )
    store = MemoryEventStore()
    writer = CognitionProvenanceWriter(store)
    assert writer.record(record).inserted is True
    assert writer.record(record).inserted is False
    conflicting = replace(record, authority_ref="authority://substituted")
    with pytest.raises(ProvenanceLineageError, match="conflicting payload"):
        writer.record(conflicting)


def test_request_provenance_rejects_identity_substitution_and_result_cannot_float() -> None:
    req = request()
    with pytest.raises(ProvenanceLineageError, match="office_id"):
        CognitionProvenance.for_request(
            req, source_event_id=SOURCE_EVENT, office_id=uuid4(),
            implementation_id=IMPLEMENTATION, authority_ref=req.authority_ref,
        )
    writer = CognitionProvenanceWriter(MemoryEventStore())
    with pytest.raises(ProvenanceLineageError, match="no recorded request lineage"):
        writer.record(CognitionProvenance.for_result(result(), source_event_id=SOURCE_EVENT))


def test_failure_and_unavailable_outcomes_remain_truthful() -> None:
    base = result()
    unavailable = replace(
        base, status=CognitionResultStatus.UNAVAILABLE, recommendation=None, rationale=None,
        provider_ref=None, resource_class_ref=None, live_generation=False,
        failure_code=CognitionFailureCode.UNAVAILABLE, failure_reason="provider unavailable",
    )
    record = CognitionProvenance.for_result(unavailable, source_event_id=SOURCE_EVENT)
    assert record.event_type is CognitionProvenanceEventType.UNAVAILABLE
    assert record.live_generation is False
    assert record.failure_code is CognitionFailureCode.UNAVAILABLE
    assert record.result_id == unavailable.result_id


def test_deterministic_event_cannot_claim_generation_and_grace_event_requires_observation() -> None:
    req = request()
    deterministic = CognitionProvenance.for_request(
        req, source_event_id=SOURCE_EVENT, office_id=OFFICE,
        implementation_id=IMPLEMENTATION, authority_ref="authority://grace/operations",
    )
    assert deterministic.live_generation is False
    with pytest.raises(ProvenanceLineageError, match="deterministic"):
        replace(deterministic, live_generation=True)
    with pytest.raises(ProvenanceLineageError, match="provider/resource"):
        replace(CognitionProvenance.for_result(result(), source_event_id=SOURCE_EVENT), provider_ref=None)


@pytest.mark.parametrize("actor", [
    CognitionActorClass.CODEX_WORKER_EXECUTION,
    CognitionActorClass.ENGINEERING_VALIDATION,
    CognitionActorClass.STEWARD_DECISION,
])
def test_non_grace_actor_classes_remain_distinct_from_grace(actor: CognitionActorClass) -> None:
    record = CognitionProvenance.for_request(
        request(), source_event_id=SOURCE_EVENT, office_id=OFFICE,
        implementation_id=IMPLEMENTATION, authority_ref="authority://grace/operations",
    )
    record = replace(record, actor_class=actor)
    payload = record.as_typed_payload()
    assert payload["actor_class"] == actor.value
    assert payload["live_generation"] is False
    assert payload["actor_class"] != CognitionActorClass.GRACE_HOME_COGNITION.value


def test_serialization_preserves_correlation_causation_timestamp_and_identity() -> None:
    req = request()
    record = CognitionProvenance.for_request(
        req, source_event_id=SOURCE_EVENT, office_id=OFFICE,
        implementation_id=IMPLEMENTATION, authority_ref="authority://grace/operations",
        causation_id=uuid4(), event_id=uuid4(), occurred_at=datetime(2026, 8, 25, 13, 0, tzinfo=UTC),
    )
    restored = CognitionProvenance.from_typed_payload(record.as_typed_payload())
    assert restored.correlation_id == record.correlation_id
    assert restored.causation_id == record.causation_id
    assert restored.occurred_at == record.occurred_at
    assert restored.resident_id == record.resident_id
    assert "recommendation" not in restored.as_typed_payload()


def test_missing_source_lineage_and_authority_widening_fail_closed() -> None:
    req = request()
    with pytest.raises(ProvenanceLineageError, match="source_event_id"):
        CognitionProvenance.for_request(
            req, source_event_id=None, office_id=OFFICE, implementation_id=IMPLEMENTATION,
            authority_ref="authority://grace/operations",
        )
    record = CognitionProvenance.for_request(
        req, source_event_id=SOURCE_EVENT, office_id=OFFICE,
        implementation_id=IMPLEMENTATION, authority_ref="authority://grace/operations",
    )
    assert "execute" not in record.as_typed_payload()


def test_result_prose_transcript_and_provider_never_supply_identity() -> None:
    response = result()
    record = CognitionProvenance.for_result(response, source_event_id=SOURCE_EVENT)
    payload = record.as_typed_payload()
    assert payload["resident_id"] == str(response.resident_id)
    assert payload["occupant_id"] == str(response.occupant_id)
    assert payload["office_id"] == str(response.office_id)
    assert "recommendation" not in payload
    assert "rationale" not in payload
    assert payload["provider_ref"] == response.provider_ref
