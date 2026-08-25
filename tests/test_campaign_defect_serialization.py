from __future__ import annotations

import json

import pytest

from riverview.campaign import DefectInput, LifecycleGateError


def test_structured_defect_round_trips_through_canonical_json_payload() -> None:
    original = DefectInput("criterion-1", "blocking", "expected", "observed", "evidence:one", "repair action")
    encoded = json.dumps(original.as_payload(), sort_keys=True)
    restored = DefectInput.from_payload(json.loads(encoded))
    assert restored == original
    assert restored.as_payload() == original.as_payload()


def test_malformed_or_unbounded_defect_payload_fails_closed() -> None:
    with pytest.raises(LifecycleGateError, match="malformed"):
        DefectInput.from_payload({"severity": "blocking"})
    with pytest.raises(LifecycleGateError, match="exceeds its bound"):
        DefectInput("criterion", "blocking", "x" * 8_001, "observed", "evidence:one", "repair").as_payload()
