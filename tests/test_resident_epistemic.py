from datetime import UTC, datetime
from uuid import uuid4

import pytest

from riverview.reasoning.epistemic import (
    CREATIVE,
    REASONED,
    VERIFIED,
    EpistemicSpan,
    ProvenanceRecord,
    build_epistemic_metadata,
    mask_labels,
)
from riverview.reasoning.contracts import ReasoningResponse
from riverview.reasoning.resident_home import _DECISION_FORMAT


def test_epistemic_masks_are_extensible_and_labelled() -> None:
    assert VERIFIED | REASONED | CREATIVE == 21
    assert mask_labels(21) == ["VERIFIED", "REASONED", "CREATIVE"]


def test_span_supports_multiple_classes_and_bounded_provenance() -> None:
    span = EpistemicSpan(
        span_id="s1", start=0, end=11, mask=VERIFIED | REASONED,
        provenance=(ProvenanceRecord(
            source_class="live_telemetry", evidence_ref="evidence://1",
            observed_at=datetime(2026, 8, 28, tzinfo=UTC), freshness="current",
            capability="operations.host-resources.read",
        ),),
    )
    metadata = build_epistemic_metadata([span], response_text="C2 is ready")
    assert metadata["summary_mask"] == VERIFIED | REASONED
    assert metadata["spans"][0]["mask"] == VERIFIED | REASONED
    assert metadata["spans"][0]["provenance"][0]["evidence_ref"] == "evidence://1"


def test_home_decision_contract_requires_epistemic_spans() -> None:
    assert "epistemic_spans" in _DECISION_FORMAT["required"]


def test_spans_fail_closed_for_invalid_offsets_or_provenance() -> None:
    with pytest.raises(ValueError, match="span bounds"):
        EpistemicSpan(span_id="s", start=2, end=1, mask=VERIFIED)
    with pytest.raises(ValueError, match="evidence"):
        ProvenanceRecord(source_class="live_telemetry", evidence_ref="", observed_at=None)


def test_reasoning_response_carries_epistemic_metadata() -> None:
    span = EpistemicSpan("s1", 0, 5, VERIFIED, (ProvenanceRecord("institutional", "river://1"),))
    response = ReasoningResponse(uuid4(), uuid4(), uuid4(), "test:provider", "advice", "Known", ("test://response",), "operational", datetime.now(UTC), epistemic=build_epistemic_metadata([span], response_text="Known"))
    assert response.as_typed_payload()["epistemic"]["summary_mask"] == VERIFIED
