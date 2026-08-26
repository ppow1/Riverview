"""RUN-005A package-engineer loop tests with a durable-projection fake."""

from __future__ import annotations

from collections import Counter
from uuid import uuid4

from riverview.campaign import (AcceptanceResult, Candidate, DefectInput, PackageDefect,
                                PackageEngineerLoop, PackagePass, RepairResult)
from riverview.campaign import CampaignLifecycleStore
from test_campaign_validation_lifecycle import _package


def _defect(number: int, root: str | None = None) -> PackageDefect:
    return PackageDefect(
        DefectInput(f"criterion-{number}", "blocking", "expected", f"observed-{number}",
                    f"evidence:package:{number}", "repair the bounded defect"),
        root or f"root-{number}", f"RIV-PKG-{number:04d}", f"pytest tests/test_{number}.py",
        f"stdout:package:{number}", f"stderr:package:{number}", "test fixture defect",
    )


class FakeLifecycle:
    def __init__(self) -> None:
        self.runs = {}
        self.entries = []
        self.dispatches = []

    def begin_package_run(self, *, objective_id, stage_id, worktree_ref, package_run_id=None):
        run_id = self.runs.get(stage_id, {}).get("package_run_id", package_run_id or uuid4())
        self.runs.setdefault(stage_id, {"package_run_id": run_id, "state": "executing",
                                        "repair_generation": 0, "discovery_sequence": 0,
                                        "worktree_ref": worktree_ref, "acceptance_dispatch_count": 0})
        return run_id

    def package_run(self, *, stage_id):
        return self.runs.get(stage_id)

    def update_package_run(self, *, package_run_id, **values):
        run = next(value for value in self.runs.values() if value["package_run_id"] == package_run_id)
        run.update({key: value for key, value in values.items() if value is not None})

    def record_package_ledger_entry(self, *, package_run_id, **values):
        run = next(value for value in self.runs.values() if value["package_run_id"] == package_run_id)
        run["discovery_sequence"] += 1
        entry = {"ledger_id": uuid4(), "root_cause_key": values["root_cause_key"],
                 "discovery_sequence": run["discovery_sequence"], "status": "observed"}
        self.entries.append(entry)
        return entry["ledger_id"]

    def update_package_ledger_entry(self, *, ledger_id, **values):
        entry = next(item for item in self.entries if item["ledger_id"] == ledger_id)
        entry.update(values)

    def package_ledger(self, *, package_run_id):
        return tuple(self.entries)

    def dispatch_package_acceptance(self, *, package_run_id, candidate_ref, candidate_version_hash, verification):
        run = next(value for value in self.runs.values() if value["package_run_id"] == package_run_id)
        run["acceptance_dispatch_count"] += 1
        run["state"] = "awaiting_independent_acceptance"
        self.dispatches.append(candidate_ref)
        return run["acceptance_dispatch_count"]

    def record_package_acceptance(self, *, package_run_id, accepted, reason=None):
        run = next(value for value in self.runs.values() if value["package_run_id"] == package_run_id)
        run["state"] = "accepted" if accepted else "acceptance_failed"
        run["last_error"] = reason


class FakeExecutor:
    def __init__(self, passes, full_passes=()):
        self.passes = list(passes)
        self.full_passes = list(full_passes)
        self.repaired = []
        self.verifications = []
        self.candidates = 0

    def execute(self, *, worktree_ref, repair_generation):
        return self.passes.pop(0) if self.passes else PackagePass()

    def repair(self, defect, *, worktree_ref, repair_generation):
        self.repaired.append((defect.root_cause_key, worktree_ref, repair_generation))
        return RepairResult(True, (f"src/{defect.root_cause_key}.py",), "bounded repair", "focused tests pass")

    def verify_repair(self, defect, repair, *, worktree_ref):
        self.verifications.append(defect.root_cause_key)
        return True

    def full_verify(self, *, worktree_ref, repair_generation):
        return self.full_passes.pop(0) if self.full_passes else PackagePass(verification={"full": "pass"})

    def create_candidate(self, *, worktree_ref, repair_generation):
        self.candidates += 1
        return Candidate(f"candidate:{self.candidates}", f"{self.candidates:040d}", {"candidate": self.candidates})


def _loop(fake_lifecycle, executor, acceptance, *, max_repairs=3):
    return PackageEngineerLoop(fake_lifecycle, objective_id=uuid4(), stage_id=uuid4(),
                                worktree_ref="A:/Riverview/package-worktree", executor=executor,
                                independent_acceptance=acceptance,
                                max_repairs_per_root=max_repairs).run()


def test_package_engineer_repairs_many_sequential_defects_without_intermediate_acceptance():
    lifecycle = FakeLifecycle()
    defects = tuple(_defect(number) for number in range(1, 12))
    executor = FakeExecutor([PackagePass((defect,)) for defect in defects])
    acceptance_calls = []
    outcome = _loop(lifecycle, executor, lambda candidate, *, worktree_ref: (acceptance_calls.append(candidate) or AcceptanceResult(True)))
    assert outcome.state == "accepted"
    assert len(lifecycle.entries) == 11
    assert len(executor.verifications) == 11
    assert len(acceptance_calls) == 1
    assert len(lifecycle.dispatches) == 1
    assert len({item[1] for item in executor.repaired}) == 1


def test_independent_failure_returns_all_defects_to_package_engineer_then_revalidates():
    lifecycle = FakeLifecycle()
    first_defect = _defect(1)
    validator_defects = (_defect(2), _defect(3))
    executor = FakeExecutor([PackagePass((first_defect,))])
    results = iter((AcceptanceResult(False, validator_defects, "validator found two defects"), AcceptanceResult(True)))
    outcome = _loop(lifecycle, executor, lambda candidate, *, worktree_ref: next(results))
    assert outcome.state == "accepted"
    assert outcome.acceptance_dispatches == 2
    assert [entry["root_cause_key"] for entry in lifecycle.entries] == ["root-1", "root-2", "root-3"]
    assert executor.candidates == 2


def test_same_root_defect_escalates_after_bounded_repairs_without_spinning():
    lifecycle = FakeLifecycle()
    defect = _defect(1, "same-root")
    executor = FakeExecutor([PackagePass((defect,)) for _ in range(4)])
    outcome = _loop(lifecycle, executor, lambda candidate, *, worktree_ref: AcceptanceResult(True), max_repairs=3)
    assert outcome.state == "escalated"
    assert "same-root" in outcome.reason
    assert len(executor.repaired) == 3
    assert len(lifecycle.dispatches) == 0


def test_restart_projection_reuses_package_run_and_preserves_ledger():
    lifecycle = FakeLifecycle()
    objective_id, stage_id = uuid4(), uuid4()
    run_id = lifecycle.begin_package_run(objective_id=objective_id, stage_id=stage_id, worktree_ref="A:/Riverview/package-worktree")
    lifecycle.record_package_ledger_entry(package_run_id=run_id, objective_id=objective_id, stage_id=stage_id,
                                          root_cause_key="restart-root", checkpoint="RIV-RESTART",
                                          observed_behavior="bad", expected_behavior="good",
                                          evidence_ref="evidence:restart", root_cause="persisted root")
    resumed = lifecycle.begin_package_run(objective_id=objective_id, stage_id=stage_id, worktree_ref="A:/Riverview/package-worktree")
    assert resumed == run_id
    assert lifecycle.package_run(stage_id=stage_id)["discovery_sequence"] == 1
    assert lifecycle.package_ledger(package_run_id=run_id)[0]["root_cause_key"] == "restart-root"


def test_postgres_package_ledger_and_restart_projection_survive_store_recreation():
    lifecycle, _relay, objective_id, stage_id, _basis_id, _key = _package()
    defect = _defect(99)
    executor = FakeExecutor([PackagePass((defect,))])
    outcome = PackageEngineerLoop(
        lifecycle, objective_id=objective_id, stage_id=stage_id,
        worktree_ref="A:/Riverview/package-worktree", executor=executor,
        independent_acceptance=lambda candidate, *, worktree_ref: AcceptanceResult(True),
    ).run()
    assert outcome.state == "accepted"
    recreated = CampaignLifecycleStore()
    projection = recreated.package_run(stage_id=stage_id)
    assert projection["state"] == "accepted"
    assert projection["acceptance_dispatch_count"] == 1
    assert recreated.package_ledger(package_run_id=outcome.package_run_id)[0]["required_repair"] == defect.defect.required_repair


def test_postgres_multi_defect_and_independent_fail_return_to_repair():
    lifecycle, _relay, objective_id, stage_id, _basis_id, _key = _package()
    defects = tuple(_defect(number) for number in range(201, 204))
    executor = FakeExecutor([PackagePass((defect,)) for defect in defects])
    verdicts = iter((AcceptanceResult(False, (_defect(300), _defect(301)), "independent findings"),
                     AcceptanceResult(True)))
    outcome = PackageEngineerLoop(
        lifecycle, objective_id=objective_id, stage_id=stage_id,
        worktree_ref="A:/Riverview/package-worktree", executor=executor,
        independent_acceptance=lambda candidate, *, worktree_ref: next(verdicts),
    ).run()
    assert outcome.state == "accepted"
    assert outcome.acceptance_dispatches == 2
    assert len(lifecycle.package_ledger(package_run_id=outcome.package_run_id)) == 5
    assert lifecycle.package_run(stage_id=stage_id)["state"] == "accepted"
