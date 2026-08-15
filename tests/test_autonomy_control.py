"""Pure contract tests for the bounded autonomous control plane."""

from pathlib import Path
from uuid import uuid4

import pytest

from riverview.autonomy.control import ExecutionEnvelope, RetryPolicy


def envelope(**overrides: object) -> ExecutionEnvelope:
    values: dict[str, object] = {
        "execution_id": uuid4(),
        "correlation_id": uuid4(),
        "capability_name": "codex.engineering.v1",
        "repository_identity": "ppow1/Riverview",
        "repository_root": Path("A:/Riverview/repo"),
        "expected_base_sha": "a" * 40,
        "bounded_instruction": "Run the bounded acceptance fixture and report evidence.",
        "allowed_paths": ("tests/fixtures/autonomy",),
        "acceptance_criteria": ("fixture passes",),
        "evidence_requirements": ("test result",),
        "timeout_seconds": 60,
        "retry_key": f"test:{uuid4()}",
    }
    values.update(overrides)
    return ExecutionEnvelope(**values)


def test_envelope_rejects_absolute_allowed_path() -> None:
    with pytest.raises(ValueError, match="allowed paths"):
        envelope(allowed_paths=("A:/outside",))


def test_envelope_rejects_bad_base_sha() -> None:
    with pytest.raises(ValueError, match="base SHA"):
        envelope(expected_base_sha="not-a-sha")


def test_retry_policy_is_one_bounded_retry() -> None:
    assert RetryPolicy().decide("relay.noop", 1, failure_class="timeout")["retry"] is True
    assert RetryPolicy().decide("relay.noop", 2, failure_class="timeout")["retry"] is False


def test_capacity_freshness_bound_is_validated() -> None:
    from riverview.autonomy import CapabilityRegistry

    with pytest.raises(ValueError, match="freshness"):
        CapabilityRegistry().select("bounded-engineering", max_age_seconds=0)


def test_dispatch_rejects_protected_classification() -> None:
    from riverview.autonomy import CapabilityRegistry

    with pytest.raises(ValueError, match="protected"):
        CapabilityRegistry().dispatch("bounded-engineering", classification="undercurrent")
