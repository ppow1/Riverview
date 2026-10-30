from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from riverview.intake.engineering import EngineeringIntent
from riverview.mcp.comms5 import Comms5Error, Comms5Service


def _intent(**overrides: object) -> EngineeringIntent:
    values: dict[str, object] = {
        "seed_id": uuid4(),
        "objective_id": uuid4(),
        "stage_id": uuid4(),
        "repository_identity": "Riverview standalone",
        "repository_root": Path.cwd(),
        "expected_base_sha": "a" * 40,
        "bounded_instruction": "Return exactly OK. Do not use tools. Do not modify files.",
        "allowed_paths": (".",),
        "acceptance_criteria": ("return exactly OK",),
        "evidence_requirements": ("record the exact base SHA",),
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


def test_existing_acceptance_repository_identity_is_valid() -> None:
    _intent().validate()


def test_engineering_intent_accepts_valid_linked_git_worktree(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    git_dir = tmp_path / "repository.git" / "worktrees" / "worktree"
    common_dir = tmp_path / "repository.git"
    git_dir.mkdir(parents=True)
    common_dir.mkdir(parents=True, exist_ok=True)
    worktree.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/test\n", encoding="utf-8")
    (git_dir / "commondir").write_text("../..\n", encoding="utf-8")
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")

    _intent(repository_root=worktree).validate()


@pytest.mark.parametrize(
    "marker_contents",
    ["not a gitdir pointer\n", "gitdir: missing-worktree-metadata\n"],
)
def test_engineering_intent_rejects_invalid_linked_git_worktree_marker(
    tmp_path: Path, marker_contents: str
) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text(marker_contents, encoding="utf-8")

    with pytest.raises(ValueError, match="not an approved Git repository"):
        _intent(repository_root=worktree).validate()


def test_comms5_describes_and_exposes_governed_formation_enqueue() -> None:
    operation = Comms5Service().describe_operation("form_and_queue_work")
    assert operation["authorization"] == "STEWARD-GATED_WRITE"
    assert operation["required"] == [
        "objective_id",
        "stage_id",
        "authority_id",
        "explicit_steward_confirmation",
        "idempotency_key",
        "client context",
    ]



def test_recovery_operation_remains_a_distinct_existing_work_order_path() -> None:
    recovery = Comms5Service().describe_operation("revalidate_and_queue_work")
    assert recovery["required"][0] == "work_order_id"
    assert "RIV-EXE-0008" in recovery["description"]


def test_formation_operation_rejects_invalid_objective_id_before_mutation() -> None:
    with pytest.raises(Comms5Error, match="invalid"):
        Comms5Service().form_and_queue_work(
            {
                "objective_id": "not-a-uuid",
                "stage_id": str(uuid4()),
                "authority_id": str(uuid4()),
                "explicit_steward_confirmation": True,
                "idempotency_key": "test-invalid-objective",
                "client_id": "test",
                "client_type": "test",
                "client_name": "test",
                "authenticated_principal": "untrusted-client-provenance",
            },
            transport_principal="steward",
        )
