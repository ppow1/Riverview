"""Pure contract tests for the bounded autonomous control plane."""

import json
import subprocess
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


def test_codex_adapter_rejects_a_bounded_write_with_no_observable_change(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repository = tmp_path
    (repository / ".git").mkdir()
    commands: list[list[str]] = []
    popen_kwargs: dict[str, object] = {}

    class Completed:
        returncode = 0

        def communicate(self, timeout: int) -> tuple[str, str]:
            return "provider evidence", ""

    def git_output(command: list[str], **kwargs: object) -> str:
        return "a" * 40 if command[1] == "rev-parse" else ""

    monkeypatch.setattr("riverview.autonomy.control.subprocess.check_output", git_output)
    monkeypatch.setattr("riverview.autonomy.control.subprocess.run", lambda *args, **kwargs: None)
    def popen(command: list[str], **kwargs: object) -> Completed:
        commands.append(command)
        popen_kwargs.update(kwargs)
        return Completed()

    monkeypatch.setattr("riverview.autonomy.control.subprocess.Popen", popen)
    result = CodexCliAdapter(executable="codex-test").run(envelope(repository_root=repository, write_policy="bounded_write"))
    assert result.result_category == "failed"
    assert result.checkpoint_refs == ("RIV-EXE-0010",)
    assert commands[0][commands[0].index("--sandbox") + 1] == "workspace-write"


def test_codex_adapter_materializes_a_real_bounded_write(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repository = tmp_path
    (repository / ".git").mkdir()
    commands: list[list[str]] = []
    popen_kwargs: dict[str, object] = {}
    target = "docs/accepted.txt"

    class Completed:
        returncode = 0

        def communicate(self, timeout: int) -> tuple[str, str]:
            return "provider evidence", ""

    def git_output(command: list[str], **kwargs: object) -> str:
        if command[1] == "rev-parse":
            return "a" * 40
        if command[1] == "status":
            return f"?? {target}\n"
        return ""

    def git_run(command: list[str], **kwargs: object) -> None:
        if command[1:3] == ["worktree", "add"]:
            worktree = Path(command[5])
            (worktree / target).parent.mkdir(parents=True)
            (worktree / target).write_text("bounded result", encoding="utf-8")

    monkeypatch.setattr("riverview.autonomy.control.subprocess.check_output", git_output)
    monkeypatch.setattr("riverview.autonomy.control.subprocess.run", git_run)
    def popen(command: list[str], **kwargs: object) -> Completed:
        commands.append(command)
        popen_kwargs.update(kwargs)
        return Completed()

    monkeypatch.setattr("riverview.autonomy.control.subprocess.Popen", popen)

    result = CodexCliAdapter(executable="codex-test").run(
        envelope(repository_root=repository, write_policy="bounded_write", allowed_paths=("docs/accepted.txt",))
    )

    assert result.result_category == "succeeded"
    assert result.changed_paths == (target,)
    assert (repository / target).read_text(encoding="utf-8") == "bounded result"
    assert commands[0][commands[0].index("--sandbox") + 1] == "workspace-write"
    assert popen_kwargs["stdin"] is subprocess.DEVNULL


def test_worktree_paths_sees_a_new_markdown_file(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "--quiet", str(repository)], check=True, capture_output=True)
    target = repository / "docs" / "accepted.md"
    target.parent.mkdir()
    target.write_text("bounded result", encoding="utf-8")
    assert CodexCliAdapter._worktree_paths(repository) == ("docs/accepted.md",)


def test_commit_sha_evidence_requirement_triggers_commit_phase() -> None:
    assert CodexCliAdapter._requires_commit(("commit SHA",)) is True
    assert CodexCliAdapter._requires_commit(("publication evidence",)) is False


def test_adapter_error_preserves_bounded_worktree_evidence() -> None:
    summary = CodexCliAdapter._adapter_error_summary(
        error="RIV-REC-0004: publication requires a verified commit.",
        execution_root=Path("A:/Riverview/repo"),
        worktree=Path("C:/Temp/riverview-codex-worktree-example"),
        allowed_paths=("docs/result.md",),
        changed_paths=("docs/result.md",),
        provider_output="provider claimed completion",
        stdout='{"type":"turn.completed"}',
        stderr="",
    )
    evidence = json.loads(summary)
    assert evidence["temporary_worktree"].replace("\\", "/") == "C:/Temp/riverview-codex-worktree-example"
    assert evidence["changed_paths"] == ["docs/result.md"]
    assert evidence["provider_output_tail"] == "provider claimed completion"


def test_adapter_error_checkpoint_preserves_reconciliation_class() -> None:
    assert CodexCliAdapter._checkpoint_for_error("RIV-REC-0004: commit missing") == "RIV-REC-0004"
    assert CodexCliAdapter._checkpoint_for_error("RIV-EXE-0010: empty write") == "RIV-EXE-0010"


def test_timeout_diagnostics_are_bounded_redacted_and_phase_oriented() -> None:
    summary = CodexCliAdapter._timeout_diagnostic_summary(
        process_id=123,
        elapsed_seconds=300.25,
        stdout='{"type":"thread.started"}\n{"type":"turn.started","token":"secret-value"}\n',
        stderr="authorization=secret-value",
        changed_paths=("docs/result.md",),
        target_state={"docs/result.md": True},
    )
    assert "turn.started" in summary
    assert "secret-value" not in summary
    assert '"process_id":123' in summary
    assert '"changed_paths_at_timeout":["docs/result.md"]' in summary


def test_windows_timeout_terminates_provider_process_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    class Process:
        pid = 456

        def kill(self) -> None:
            raise AssertionError("tree termination should use taskkill on Windows")

    monkeypatch.setattr("riverview.autonomy.control.os.name", "nt")
    monkeypatch.setattr(
        "riverview.autonomy.control.subprocess.run",
        lambda command, **kwargs: calls.append(command),
    )
    CodexCliAdapter._terminate_process_tree(Process())  # type: ignore[arg-type]
    assert calls == [["taskkill", "/PID", "456", "/T", "/F"]]


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


def test_positive_bounded_write_survives_copyback_commit_publication_and_reconciliation(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    remote = tmp_path / "remote.git"
    repository.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repository, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@riverview.local"], cwd=repository, check=True)
    subprocess.run(["git", "config", "user.name", "Riverview Test"], cwd=repository, check=True)
    (repository / "README.md").write_text("base", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repository, check=True)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repository, check=True, capture_output=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=repository, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=repository, check=True, capture_output=True)
    worktree = tmp_path / "isolated-worktree"
    worktree.mkdir()
    (worktree / "docs").mkdir()
    (worktree / "docs" / "result.md").write_text("governed bounded write", encoding="utf-8")
    CodexCliAdapter._copy_allowed_changes(worktree, repository, ("docs/result.md",))
    commit = CodexCliAdapter._commit_allowed_changes(repository, ("docs/result.md",), uuid4())
    published = CodexCliAdapter._publish_commit(repository, commit)
    evidence = ResultReconciler.validate_observed_state(
        result_category="succeeded", observed_head=commit, expected_base_sha=base,
        changed_paths=("docs/result.md",), claimed_changed_paths=("docs/result.md",),
        allowed_paths=("docs/result.md",), repository_root=repository,
        acceptance_criteria=("docs/result.md exists", "docs/result.md contains governed bounded write"),
        evidence_requirements=("resulting commit SHA", "publication to origin/main"), write_policy="bounded_write",
        commit_sha=commit, remote_verified_sha=published,
    )
    assert evidence["content_verified"] is True
    assert (repository / "docs" / "result.md").is_file()
    assert subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=repository, text=True).strip() == commit


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
