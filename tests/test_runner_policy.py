"""Policy tests for the restricted local runner.

Version: 0.5.0
"""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from riverview.autonomy.control import ExecutionResult
from riverview.relay import ClaimedWork
from riverview.runner import RestrictedRunner


def test_runner_repository_is_resolved(tmp_path: Path) -> None:
    runner = RestrictedRunner(tmp_path, "test")
    assert runner.repository == tmp_path.resolve()


def test_runner_preserves_specific_execution_checkpoint() -> None:
    assert RestrictedRunner._checkpoint_from_error(
        "RIV-EXE-0003: Codex CLI exceeded the bounded execution deadline."
    ) == "RIV-EXE-0003"
    assert RestrictedRunner._checkpoint_from_error("unclassified runner failure") == "RIV-RUN-0001"


def test_failed_provider_result_cannot_enter_accepted_reconciliation(monkeypatch, tmp_path: Path) -> None:
    runner = RestrictedRunner(tmp_path, "test")
    (tmp_path / ".git").mkdir()
    work = ClaimedWork(uuid4(), "codex.engineering.v1", "1", {"engineering_intent_id": str(uuid4())}, 900, 1)
    failed = ExecutionResult(
        uuid4(), uuid4(), uuid4(), "codex-cli-local", "timed_out", "timeout", (), ("provider timeout",),
        None, None, ("RIV-EXE-0003",), (), "provider timeout", datetime.now(UTC), datetime.now(UTC),
    )
    decisions: list[str] = []
    failures: list[str] = []
    monkeypatch.setattr("riverview.runner.EngineeringIntentStore.load", lambda _self, _intent_id: {
        "authority_id": uuid4(), "approved_by": "steward", "objective_id": uuid4(), "stage_id": uuid4(),
        "correlation_id": uuid4(), "causation_id": None, "capability_name": "codex.engineering.v1",
        "repository_identity": "ppow1/Riverview", "repository_root": str(tmp_path), "expected_base_sha": "a" * 40,
        "bounded_instruction": "bounded", "allowed_paths": ["docs"], "acceptance_criteria": ["write"],
        "evidence_requirements": ["evidence"], "timeout_seconds": 1, "classification": "river",
        "write_policy": "bounded_write", "action_type": "codex.engineering.v1",
    })
    monkeypatch.setattr("riverview.runner.ExecutionStore.persist", lambda _self, _envelope: failed.execution_id)
    monkeypatch.setattr("riverview.runner.ExecutionStore.start", lambda _self, _execution_id: None)
    monkeypatch.setattr("riverview.runner.CodexCliAdapter.run", lambda _self, _envelope: failed)
    monkeypatch.setattr(runner, "_working_paths", lambda _repository: ())

    class FakeReconciler:
        def persist(self, _result):
            return None

        def reconcile_repository(self, *_args, **_kwargs):
            raise AssertionError("failed provider result must not be repository-reconciled")

        def record_decision(self, _execution, _correlation, decision, *_args):
            decisions.append(decision)

    monkeypatch.setattr("riverview.runner.ResultReconciler", FakeReconciler)
    monkeypatch.setattr(runner, "_fail", lambda _order, checkpoint, _reason, _timed_out: failures.append(checkpoint))
    result = runner._execute_codex(work)
    assert result["status"] == "timed_out"
    assert decisions == ["checkpoint"]
    assert failures == ["RIV-EXE-0003"]
