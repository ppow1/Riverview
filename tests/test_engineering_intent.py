"""Pure contract tests for typed Steward engineering formation."""

from pathlib import Path
from uuid import uuid4

import pytest

from riverview.intake import EngineeringIntent


def intent(**overrides: object) -> EngineeringIntent:
    values: dict[str, object] = {
        "seed_id": uuid4(),
        "objective_id": uuid4(),
        "stage_id": uuid4(),
        "repository_identity": "ppow1/Riverview",
        "repository_root": Path.cwd(),
        "expected_base_sha": "a" * 40,
        "bounded_instruction": "Inspect the repository and return bounded evidence.",
        "allowed_paths": ("src", "docs", "AI_HINTS.md"),
        "acceptance_criteria": ("No files are changed.",),
        "evidence_requirements": ("Return the observed Git HEAD.",),
        "capability_name": "codex.engineering.v1",
        "action_type": "codex.engineering.v1",
        "timeout_seconds": 300,
        "classification": "river",
        "correlation_id": uuid4(),
        "causation_id": uuid4(),
        "idempotency_key": f"test:{uuid4()}",
    }
    values.update(overrides)
    return EngineeringIntent(**values)


def test_typed_intent_validates_without_becoming_executable_text() -> None:
    value = intent()
    value.validate()
    assert value.write_policy == "read_only"


def test_typed_intent_rejects_unapproved_repository() -> None:
    with pytest.raises(ValueError, match="repository identity"):
        intent(repository_identity="other/repository").validate()


def test_typed_intent_rejects_unregistered_action() -> None:
    with pytest.raises(ValueError, match="registered Codex"):
        intent(action_type="shell.exec").validate()


def test_typed_intent_requires_steward_and_known_policy() -> None:
    with pytest.raises(ValueError, match="Steward-approved"):
        intent(approved_by="chatgpt").validate()
    with pytest.raises(ValueError, match="unsupported"):
        intent(write_policy="workspace_write").validate()
    intent(write_policy="bounded_write").validate()


def test_typed_intent_requires_bounded_idempotency() -> None:
    with pytest.raises(ValueError, match="idempotency"):
        intent(idempotency_key=" ").validate()
