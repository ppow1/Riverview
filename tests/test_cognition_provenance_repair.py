"""GRC-006R durable request/result correspondence regressions."""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

from riverview.reasoning import (
    CognitionFailureCode,
    CognitionProvenance,
    CognitionProvenanceEventType,
    CognitionProvenanceWriter,
    ProvenanceLineageError,
)
from test_cognition_contracts import result
from test_cognition_provenance import (
    IMPLEMENTATION,
    OFFICE,
    SOURCE_EVENT,
    MemoryEventStore,
    request,
)


def _request_record():
    req = request()
    return req, CognitionProvenance.for_request(
        req,
        source_event_id=SOURCE_EVENT,
        office_id=OFFICE,
        implementation_id=IMPLEMENTATION,
        authority_ref=req.authority_ref,
        event_id=uuid4(),
    )


def _matching_result():
    response = replace(result(), source_cognition_event_id=SOURCE_EVENT)
    return CognitionProvenance.for_result(
        response,
        source_event_id=SOURCE_EVENT,
        event_type=CognitionProvenanceEventType.COMPLETED,
        event_id=uuid4(),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("resident_id", uuid4()),
        ("occupant_id", uuid4()),
        ("office_id", uuid4()),
        ("implementation_id", uuid4()),
        ("authority_ref", "authority://substituted"),
        ("source_event_id", uuid4()),
    ],
)
def test_durable_writer_rejects_each_stored_request_correspondence_substitution(field, value) -> None:
    _, request_record = _request_record()
    store = MemoryEventStore()
    writer = CognitionProvenanceWriter(store)
    writer.record(request_record)
    before = tuple(store.events)

    forged = replace(_matching_result(), **{field: value})
    with pytest.raises(ProvenanceLineageError, match=f"{field} correspondence mismatch"):
        writer.record(forged)

    assert tuple(store.events) == before


def test_matching_result_is_durable_and_reconstructs_against_stored_request() -> None:
    _, request_record = _request_record()
    store = MemoryEventStore()
    writer = CognitionProvenanceWriter(store)
    writer.record(request_record)
    result_record = _matching_result()

    writer.record(result_record)
    reloaded = CognitionProvenanceWriter(MemoryEventStore(store.events)).reconstruct(request_record.request_id)
    assert [item.event_type for item in reloaded] == [
        CognitionProvenanceEventType.REQUESTED,
        CognitionProvenanceEventType.COMPLETED,
    ]
    assert reloaded[1].source_event_id == reloaded[0].source_event_id


@pytest.mark.parametrize("event_type", [
    CognitionProvenanceEventType.UNAVAILABLE,
    CognitionProvenanceEventType.REJECTED,
    CognitionProvenanceEventType.TIMED_OUT,
])
def test_failure_events_use_the_same_durable_request_correspondence(event_type) -> None:
    _, request_record = _request_record()
    store = MemoryEventStore()
    writer = CognitionProvenanceWriter(store)
    writer.record(request_record)
    status, failure_code = {
        CognitionProvenanceEventType.UNAVAILABLE: ("unavailable", CognitionFailureCode.UNAVAILABLE),
        CognitionProvenanceEventType.REJECTED: ("denied", CognitionFailureCode.DENIED),
        CognitionProvenanceEventType.TIMED_OUT: ("timeout", CognitionFailureCode.TIMEOUT),
    }[event_type]
    failure = replace(_matching_result(), event_type=event_type, result_id=None, packet_id=None,
                      status=status, failure_code=failure_code,
                      live_generation=False, provider_ref=None, resource_class_ref=None)
    writer.record(failure)
    assert len(store.events) == 2

    forged = replace(failure, office_id=uuid4(), event_id=uuid4())
    with pytest.raises(ProvenanceLineageError, match="office_id correspondence mismatch"):
        writer.record(forged)
    assert len(store.events) == 2


def test_malformed_stored_request_fails_before_append() -> None:
    _, request_record = _request_record()
    store = MemoryEventStore()
    writer = CognitionProvenanceWriter(store)
    writer.record(request_record)
    original = store.events[0]
    store.events[0] = replace(original, payload={"schema_version": "not-cognition-provenance"})

    with pytest.raises(ProvenanceLineageError, match="stored request lineage is malformed"):
        writer.record(_matching_result())
    assert len(store.events) == 1
