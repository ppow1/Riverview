"""Bounded RV-008.4 response validation tests."""

import pytest

from riverview.grace.responses import RESPONSE_SCHEMA, _response_outcome, _validate_payload


def test_advice_response_has_declared_outcome() -> None:
    payload = {
        "schema_version": RESPONSE_SCHEMA,
        "summary": "bounded advice",
        "evidence_refs": ["response:test"],
        "escalation_required": False,
    }
    assert _validate_payload("advice", payload, "river")[3] == "advisory_accepted"
    assert _response_outcome("escalation", True) == "escalation_required"


@pytest.mark.parametrize(
    "payload,classification,match",
    [
        ({}, "river", "schema"),
        ({"schema_version": RESPONSE_SCHEMA, "summary": "x", "evidence_refs": [], "escalation_required": False}, "river", "evidence"),
        ({"schema_version": RESPONSE_SCHEMA, "summary": "x", "evidence_refs": ["x"], "escalation_required": False}, "internal", "classification"),
    ],
)
def test_response_validation_fails_closed(payload, classification, match) -> None:
    with pytest.raises((ValueError, TypeError, PermissionError), match=match):
        _validate_payload("advice", payload, classification)


def test_unknown_response_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        _response_outcome("work_order", False)
