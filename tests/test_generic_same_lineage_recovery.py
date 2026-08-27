from pathlib import Path

import pytest

from riverview.autonomy.stale_base import (
    RepositoryDriftAnalyzer,
    immutable_contract_matches,
    is_recoverable_failure,
)

BASE = "a" * 40
HEAD = "b" * 40
PATH = "docs/operations/roadmap/evidence/milestone.md"


def analyzer(monkeypatch: pytest.MonkeyPatch, changed: str, descendant: bool = True) -> RepositoryDriftAnalyzer:
    value = RepositoryDriftAnalyzer()
    monkeypatch.setattr(value, "_git", lambda _repo, *_args: changed)
    monkeypatch.setattr(value, "_is_ancestor", lambda _repo, _base, _head: descendant)
    return value


def test_recoverable_failure_classes_include_old_and_infrastructure_failures() -> None:
    assert is_recoverable_failure("RIV-EXE-0008")
    assert is_recoverable_failure("RIV-EXE-0003")
    assert is_recoverable_failure("RIV-EXE-0010")
    assert is_recoverable_failure("RIV-REC-0004")
    assert not is_recoverable_failure("RIV-GRC-0010")


def test_pre_execution_reasoning_adapter_failure_is_recoverable_only_with_evidence() -> None:
    evidence = {"status": "failed", "reason": "RIV-REASON-0001: request type is unsupported", "execution_started": False}
    assert is_recoverable_failure("RIV-REASON-0001", evidence)
    assert not is_recoverable_failure("RIV-REASON-0001", {"status": "failed", "reason": "model rejected work"})


def test_original_failure_does_not_control_drift_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    result = analyzer(monkeypatch, "src/riverview/autonomy/control.py\n").assess(Path.cwd(), BASE, (PATH,), proposed_base_sha=HEAD)
    assert result.decision == "material_drift"


def test_exact_base_allows_same_lineage_successor(monkeypatch: pytest.MonkeyPatch) -> None:
    result = analyzer(monkeypatch, "").assess(Path.cwd(), BASE, (PATH,), proposed_base_sha=BASE)
    assert result.decision == "safe_revalidation"
    assert result.changed_paths == ()


def test_safe_descendant_drift_revalidates(monkeypatch: pytest.MonkeyPatch) -> None:
    result = analyzer(monkeypatch, "docs/notes.md\n").assess(Path.cwd(), BASE, (PATH,), proposed_base_sha=HEAD)
    assert result.decision == "safe_revalidation"


def test_infrastructure_repair_requires_all_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    result = analyzer(monkeypatch, "src/riverview/autonomy/control.py\n").assess(
        Path.cwd(), BASE, (PATH,), proposed_base_sha=HEAD, infrastructure_repair_evidence={}
    )
    assert result.decision == "material_drift"


def test_infrastructure_repair_is_bounded_when_proven(monkeypatch: pytest.MonkeyPatch) -> None:
    evidence = {key: True for key in (
        "repository_identity_unchanged", "allowed_paths_unchanged", "capability_unchanged",
        "action_unchanged", "write_policy_unchanged", "instruction_unchanged",
        "reconciliation_not_weakened", "authority_not_weakened", "target_requirements_unchanged",
        "descendant_of_approved_base", "tests_passed",
    )}
    result = analyzer(monkeypatch, "src/riverview/autonomy/control.py\n").assess(
        Path.cwd(), BASE, (PATH,), proposed_base_sha=HEAD, infrastructure_repair_evidence=evidence
    )
    assert result.decision == "infrastructure_repair_revalidation"


def test_non_descendant_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    result = analyzer(monkeypatch, "docs/notes.md\n", False).assess(Path.cwd(), BASE, (PATH,), proposed_base_sha=HEAD)
    assert result.decision == "invalid_repository"


def contract() -> dict[str, object]:
    return {
        "repository_identity": "ppow1/Riverview", "repository_root": "A:/Riverview/repo",
        "expected_base_sha": BASE, "bounded_instruction": "write one file",
        "allowed_paths": [PATH], "acceptance_criteria": ["file exists"],
        "evidence_requirements": ["commit SHA"], "capability_name": "codex.engineering.v1",
        "action_type": "codex.engineering.v1", "write_policy": "bounded_write",
    }


def test_scope_mutation_fails_closed() -> None:
    value = contract()
    authority = {"contract": value}
    mutated = {**value, "acceptance_criteria": ["different"]}
    assert not immutable_contract_matches(authority, mutated, ["codex.engineering.v1"], "codex.engineering.v1")


def test_allowed_path_widening_fails_closed() -> None:
    value = contract()
    mutated = {**value, "allowed_paths": [PATH, "src"]}
    assert not immutable_contract_matches({"contract": value}, mutated, ["codex.engineering.v1"], "codex.engineering.v1")


def test_write_policy_mutation_fails_closed() -> None:
    value = contract()
    mutated = {**value, "write_policy": "read_only"}
    assert not immutable_contract_matches({"contract": value}, mutated, ["codex.engineering.v1"], "codex.engineering.v1")


def test_authority_and_capability_mutation_fails_closed() -> None:
    value = contract()
    assert not immutable_contract_matches({"contract": value}, value, ["other"], "codex.engineering.v1")


def test_drift_evidence_is_immutable_after_assessment(monkeypatch: pytest.MonkeyPatch) -> None:
    result = analyzer(monkeypatch, "docs/notes.md\n").assess(Path.cwd(), BASE, (PATH,), proposed_base_sha=HEAD)
    with pytest.raises(AttributeError):
        result.decision = "material_drift"  # type: ignore[misc]
