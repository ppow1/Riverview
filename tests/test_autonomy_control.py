"""Pure contract tests for the bounded autonomous control plane."""

from pathlib import Path
from uuid import uuid4

import pytest

from riverview.autonomy.control import (
    CodexCliAdapter,
    ContinuousMomentumEngine,
    ExecutionEnvelope,
    ResultReconciler,
    RetryPolicy,
)


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


def test_envelope_allows_only_the_two_governed_policies() -> None:
    assert envelope(write_policy="bounded_write").write_policy == "bounded_write"
    with pytest.raises(ValueError, match="unsupported"):
        envelope(write_policy="unrestricted").__post_init__()


def test_codex_adapter_selects_write_sandbox_only_for_bounded_write(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repository = tmp_path
    (repository / ".git").mkdir()
    commands: list[list[str]] = []

    class Completed:
        returncode = 0

        def communicate(self, timeout: int) -> tuple[str, str]:
            return "provider evidence", ""

    def git_output(command: list[str], **kwargs: object) -> str:
        return "a" * 40 if command[1] == "rev-parse" else ""

    monkeypatch.setattr("riverview.autonomy.control.subprocess.check_output", git_output)
    monkeypatch.setattr("riverview.autonomy.control.subprocess.run", lambda *args, **kwargs: None)
    monkeypatch.setattr("riverview.autonomy.control.subprocess.Popen", lambda command, **kwargs: commands.append(command) or Completed())
    result = CodexCliAdapter(executable="codex-test").run(envelope(repository_root=repository, write_policy="bounded_write"))
    assert result.result_category == "succeeded"
    assert commands[0][commands[0].index("--sandbox") + 1] == "workspace-write"


def test_authoritative_verifier_rejects_success_without_required_artifact(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="no authoritative changed path"):
        ResultReconciler.validate_observed_state(
            result_category="succeeded", observed_head="a" * 40, expected_base_sha="a" * 40,
            changed_paths=(), allowed_paths=("docs/result.md",), repository_root=tmp_path,
            acceptance_criteria=("docs/result.md exists",), write_policy="bounded_write",
        )


def test_authoritative_verifier_rejects_out_of_scope_change(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="escaped envelope"):
        ResultReconciler.validate_observed_state(
            result_category="succeeded", observed_head="a" * 40, expected_base_sha="a" * 40,
            changed_paths=("docs/result.md", "src/other.py"), allowed_paths=("docs/result.md",),
            repository_root=tmp_path, write_policy="bounded_write",
        )


def test_authoritative_verifier_checks_artifact_and_content(tmp_path: Path) -> None:
    artifact = tmp_path / "docs" / "result.md"
    artifact.parent.mkdir()
    artifact.write_text("governed smoke test; no runtime behavior", encoding="utf-8")
    evidence = ResultReconciler.validate_observed_state(
        result_category="succeeded", observed_head="a" * 40, expected_base_sha="a" * 40,
        changed_paths=("docs/result.md",), allowed_paths=("docs/result.md",), repository_root=tmp_path,
        acceptance_criteria=("docs/result.md exists", "docs/result.md contains governed smoke test"), write_policy="bounded_write",
    )
    assert evidence["content_verified"] is True


def test_authoritative_verifier_rejects_provider_failure(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="not successful"):
        ResultReconciler.validate_observed_state(
            result_category="failed", observed_head="a" * 40, expected_base_sha="a" * 40,
            changed_paths=(), allowed_paths=("docs/result.md",), repository_root=tmp_path,
        )


def test_authoritative_verifier_requires_commit_and_publication_when_declared(tmp_path: Path) -> None:
    artifact = tmp_path / "docs" / "result.md"
    artifact.parent.mkdir()
    artifact.write_text("ok", encoding="utf-8")
    with pytest.raises(RuntimeError, match="resulting commit"):
        ResultReconciler.validate_observed_state(
            result_category="succeeded", observed_head="a" * 40, expected_base_sha="a" * 40,
            changed_paths=("docs/result.md",), allowed_paths=("docs/result.md",), repository_root=tmp_path,
            acceptance_criteria=("docs/result.md exists",), evidence_requirements=("resulting commit SHA",), write_policy="bounded_write",
        )


def test_bounded_worktree_copy_handles_create_delete_and_path_boundary(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    repository = tmp_path / "repository"
    worktree.mkdir()
    repository.mkdir()
    (worktree / "docs").mkdir()
    (worktree / "docs" / "result.md").write_text("ok", encoding="utf-8")
    (repository / "docs").mkdir()
    (repository / "docs" / "old.md").write_text("old", encoding="utf-8")
    CodexCliAdapter._copy_allowed_changes(worktree, repository, ("docs/result.md", "docs/old.md"))
    assert (repository / "docs" / "result.md").read_text(encoding="utf-8") == "ok"
    assert not (repository / "docs" / "old.md").exists()
    with pytest.raises(RuntimeError, match="invalid"):
        CodexCliAdapter._copy_allowed_changes(worktree, repository, ("../outside",))


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


def test_continuous_frontier_is_bounded() -> None:
    with pytest.raises(ValueError, match="frontier limit"):
        ContinuousMomentumEngine().frontier(limit=65)
