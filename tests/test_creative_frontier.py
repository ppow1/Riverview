from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from riverview.operator.sillytavern import ask_sillytavern
from riverview.reasoning import ReasoningResponse
from riverview.residents.registry import ResidentRecord
from riverview.residents.workflows import propose_design
from riverview.security.creative import select_creative_route


def _provider(request):
    return ReasoningResponse(
        uuid4(), request.request_id, request.correlation_id, "local:fixture", "advice",
        "bounded creative advice", ("fixture://response",), request.classification, datetime.now(UTC)
    )


def test_sillytavern_preserves_resident_and_correlation() -> None:
    record = ResidentRecord("RES-000001", "estate://residents/res-000001", "Manager", "estate://source", "operational", "verified")
    correlation = uuid4()
    session, response = ask_sillytavern(record, provider_id="local:fixture", classification="private", correlation_id=correlation, instruction="Suggest a bounded scene.", provider=_provider)
    assert session.resident_id == record.resident_id
    assert response.correlation_id == correlation


def test_creative_and_design_boundaries_fail_closed() -> None:
    assert select_creative_route("adult-local", "local:fixture").protected_reference_only
    with pytest.raises(PermissionError):
        select_creative_route("adult-local", "cloud:fixture")
    proposal = propose_design(author_reference="estate://residents/res-000001", rationale="bounded", destination="review://design")
    assert proposal.review_state == "review_required"
