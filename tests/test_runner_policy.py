"""Policy tests for the restricted local runner.

Version: 0.5.0
"""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

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
    assert RestrictedRunner._checkpoint_from_error(None) == "RIV-RUN-0001"


def test_result_summary_is_bounded_without_removing_the_database_guard() -> None:
    from riverview.autonomy.control import ResultReconciler

    summary = ResultReconciler._bounded_persisted_summary("x" * 5000)
    assert len(summary) <= 4000
    assert "bounded summary truncated" in summary
    assert ResultReconciler._bounded_persisted_summary(None)


def test_diagnostic_tail_accepts_absent_provider_output() -> None:
    from riverview.autonomy.control import CodexCliAdapter

    assert CodexCliAdapter._safe_diagnostic_tail(None) == ""


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


def _successful_codex_result():
    return ExecutionResult(
        uuid4(), uuid4(), uuid4(), "codex-cli-local", "succeeded", "completed", (), (),
        None, None, (), (), "bounded success", datetime.now(UTC), datetime.now(UTC),
    )


def _codex_work() -> ClaimedWork:
    return ClaimedWork(
        uuid4(), "codex.engineering.v1", "1", {"engineering_intent_id": str(uuid4())}, 900, 1,
        attempt_id=uuid4(), lease_generation=1, fencing_token=uuid4(), worker_instance_id=uuid4(),
    )


def _codex_record(tmp_path: Path) -> dict:
    return {
        "authority_id": uuid4(), "approved_by": "steward", "objective_id": uuid4(), "stage_id": uuid4(),
        "correlation_id": uuid4(), "causation_id": None, "capability_name": "codex.engineering.v1",
        "repository_identity": "ppow1/Riverview", "repository_root": str(tmp_path), "expected_base_sha": "a" * 40,
        "bounded_instruction": "bounded", "allowed_paths": ["docs"], "acceptance_criteria": ["write"],
        "evidence_requirements": ["evidence"], "timeout_seconds": 1, "classification": "river",
        "write_policy": "bounded_write", "action_type": "codex.engineering.v1",
    }


def test_stale_codex_result_is_rejected_before_reconciliation(monkeypatch, tmp_path: Path) -> None:
    runner = RestrictedRunner(tmp_path, "test")
    work = _codex_work()
    result = _successful_codex_result()
    calls: list[str] = []
    monkeypatch.setattr("riverview.runner.EngineeringIntentStore.load", lambda _self, _intent_id: _codex_record(tmp_path))
    monkeypatch.setattr("riverview.runner.ExecutionStore.persist", lambda _self, _envelope: result.execution_id)
    monkeypatch.setattr("riverview.runner.ExecutionStore.start", lambda _self, _execution_id: None)
    monkeypatch.setattr("riverview.runner.CodexCliAdapter.run", lambda _self, _envelope: result)
    monkeypatch.setattr(runner, "_working_paths", lambda _repository: ())

    successor = _codex_work()

    class RaceStore:
        active_identity = runner._identity(work)
        successor_identity = runner._identity(successor)
        late_evidence: list[dict] = []

        def supersede(self):
            calls.append("successor-claimed")
            self.active_identity = self.successor_identity

        def assert_fence_current(self, _identity):
            calls.append("fence")
            if _identity != self.active_identity:
                raise RuntimeError("RIV-WRK-0003: superseded by successor")

        def complete_fenced(self, _identity, payload):
            calls.append("late-audit")
            assert payload["status"] == "late_or_stale"
            self.late_evidence.append(payload)
            raise RuntimeError("RIV-WRK-0003: superseded")

    class Reconciler:
        def persist(self, _result):
            calls.append("persist")

        def reconcile_repository(self, *_args, **_kwargs):
            calls.append("reconcile")
            raise AssertionError("stale result crossed reconciliation")

    race_store = RaceStore()
    runner.store = race_store
    monkeypatch.setattr("riverview.runner.CodexCliAdapter.run", lambda _self, _envelope: (race_store.supersede(), result)[1])
    monkeypatch.setattr("riverview.runner.ResultReconciler", Reconciler)
    outcome = runner._execute_codex(work)
    assert outcome["status"] == "stale"
    assert calls == ["successor-claimed", "persist", "fence", "late-audit"]
    assert race_store.active_identity == race_store.successor_identity
    assert race_store.late_evidence[0]["execution_id"] == str(result.execution_id)


def test_current_codex_result_reconciles_before_terminal_completion(monkeypatch, tmp_path: Path) -> None:
    runner = RestrictedRunner(tmp_path, "test")
    work = _codex_work()
    result = _successful_codex_result()
    calls: list[str] = []
    monkeypatch.setattr("riverview.runner.EngineeringIntentStore.load", lambda _self, _intent_id: _codex_record(tmp_path))
    monkeypatch.setattr("riverview.runner.ExecutionStore.persist", lambda _self, _envelope: result.execution_id)
    monkeypatch.setattr("riverview.runner.ExecutionStore.start", lambda _self, _execution_id: None)
    monkeypatch.setattr("riverview.runner.CodexCliAdapter.run", lambda _self, _envelope: result)
    monkeypatch.setattr(runner, "_working_paths", lambda _repository: ())
    monkeypatch.setattr("riverview.runner.subprocess.check_output", lambda *_args, **_kwargs: "head\n")

    class CurrentStore:
        def assert_fence_current(self, _identity):
            calls.append("fence")

        def complete_fenced(self, _identity, _payload):
            calls.append("complete")

    class Reconciler:
        def persist(self, _result):
            calls.append("persist")

        def reconcile_repository(self, *_args, **_kwargs):
            calls.append("reconcile")
            return {"changed_paths": (), "outside_scope": ()}

        def record_decision(self, _execution, _correlation, decision, *_args):
            calls.append(decision)

    runner.store = CurrentStore()
    monkeypatch.setattr("riverview.runner.ResultReconciler", Reconciler)
    outcome = runner._execute_codex(work)
    assert outcome["status"] == "succeeded"
    assert calls == ["persist", "fence", "reconcile", "accepted", "complete"]


def test_reconciliation_failure_does_not_complete_current_work(monkeypatch, tmp_path: Path) -> None:
    runner = RestrictedRunner(tmp_path, "test")
    work = _codex_work()
    result = _successful_codex_result()
    calls: list[str] = []
    monkeypatch.setattr("riverview.runner.EngineeringIntentStore.load", lambda _self, _intent_id: _codex_record(tmp_path))
    monkeypatch.setattr("riverview.runner.ExecutionStore.persist", lambda _self, _envelope: result.execution_id)
    monkeypatch.setattr("riverview.runner.ExecutionStore.start", lambda _self, _execution_id: None)
    monkeypatch.setattr("riverview.runner.CodexCliAdapter.run", lambda _self, _envelope: result)
    monkeypatch.setattr(runner, "_working_paths", lambda _repository: ())

    class CurrentStore:
        def assert_fence_current(self, _identity):
            calls.append("fence")

        def complete_fenced(self, _identity, _payload):
            calls.append("complete")

    class Reconciler:
        def persist(self, _result):
            calls.append("persist")

        def reconcile_repository(self, *_args, **_kwargs):
            calls.append("reconcile")
            raise RuntimeError("RIV-REC-0003: verification failed")

        def record_decision(self, _execution, _correlation, decision, *_args):
            calls.append(decision)

    runner.store = CurrentStore()
    monkeypatch.setattr("riverview.runner.ResultReconciler", Reconciler)
    with pytest.raises(RuntimeError, match="verification failed"):
        runner._execute_codex(work)
    assert calls == ["persist", "fence", "reconcile", "checkpoint"]
    assert "complete" not in calls
