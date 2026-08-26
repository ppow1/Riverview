"""RUN-005A package-engineer loop tests with a durable-projection fake."""

from __future__ import annotations

from collections import Counter
import threading
import time
import pytest
from uuid import uuid4

from riverview.campaign import (AcceptanceResult, Candidate, DefectInput, PackageDefect,
                                PackageEngineerLoop, PackagePass, RepairResult)
from riverview.campaign import CampaignLifecycleStore
from riverview.campaign import LifecycleGateError
from riverview.database import connect
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

    def record_package_candidate(self, *, package_run_id, candidate_ref, candidate_version_hash, verification):
        run = next(value for value in self.runs.values() if value["package_run_id"] == package_run_id)
        run.update({"state": "candidate_ready", "candidate_ref": candidate_ref,
                    "candidate_version_hash": candidate_version_hash,
                    "internal_verification": verification,
                    "acceptance_candidate_ref": None,
                    "acceptance_candidate_version_hash": None})

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
        run["candidate_ref"] = candidate_ref
        run["candidate_version_hash"] = candidate_version_hash
        run["acceptance_candidate_ref"] = candidate_ref
        run["acceptance_candidate_version_hash"] = candidate_version_hash
        run["internal_verification"] = verification
        self.dispatches.append(candidate_ref)
        return run["acceptance_dispatch_count"]

    def claim_package_acceptance(self, *, package_run_id, candidate_ref, candidate_version_hash, owner_id, lease_seconds=60):
        return True, self.dispatch_package_acceptance(
            package_run_id=package_run_id, candidate_ref=candidate_ref,
            candidate_version_hash=candidate_version_hash, verification={},
        )

    def record_package_acceptance(self, *, package_run_id, accepted, reason=None, owner_id=None):
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


def test_accepted_package_restart_is_a_terminal_noop():
    lifecycle = FakeLifecycle()
    executor = FakeExecutor([])
    first = _loop(lifecycle, executor, lambda candidate, *, worktree_ref: AcceptanceResult(True))
    calls_before = (len(executor.repaired), executor.candidates, len(lifecycle.dispatches))
    second = PackageEngineerLoop(
        lifecycle, objective_id=uuid4(), stage_id=next(iter(lifecycle.runs)),
        worktree_ref="A:/Riverview/package-worktree", executor=executor,
        independent_acceptance=lambda candidate, *, worktree_ref: (_ for _ in ()).throw(AssertionError("redispatched")),
    ).run()
    assert second.state == "accepted"
    assert second.acceptance_dispatches == 1
    assert (len(executor.repaired), executor.candidates, len(lifecycle.dispatches)) == calls_before


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


def test_postgres_accepted_restart_does_not_reexecute_or_redispatch():
    lifecycle, _relay, objective_id, stage_id, _basis_id, _key = _package()
    executor = FakeExecutor([])
    first = PackageEngineerLoop(
        lifecycle, objective_id=objective_id, stage_id=stage_id,
        worktree_ref="A:/Riverview/package-worktree", executor=executor,
        independent_acceptance=lambda candidate, *, worktree_ref: AcceptanceResult(True),
    ).run()
    dispatch_count = lifecycle.package_run(stage_id=stage_id)["acceptance_dispatch_count"]
    recreated = CampaignLifecycleStore()
    second = PackageEngineerLoop(
        recreated, objective_id=objective_id, stage_id=stage_id,
        worktree_ref="A:/Riverview/package-worktree", executor=executor,
        independent_acceptance=lambda candidate, *, worktree_ref: (_ for _ in ()).throw(AssertionError("redispatched")),
    ).run()
    third = PackageEngineerLoop(
        CampaignLifecycleStore(), objective_id=objective_id, stage_id=stage_id,
        worktree_ref="A:/Riverview/package-worktree", executor=executor,
        independent_acceptance=lambda candidate, *, worktree_ref: (_ for _ in ()).throw(AssertionError("redispatched")),
    ).run()
    assert first.state == second.state == third.state == "accepted"
    assert second.acceptance_dispatches == third.acceptance_dispatches == dispatch_count == 1
    assert executor.candidates == 1


def test_postgres_double_start_acceptance_dispatch_has_one_winner():
    lifecycle, _relay, objective_id, stage_id, _basis_id, _key = _package()
    package_run_id = lifecycle.begin_package_run(
        objective_id=objective_id, stage_id=stage_id, worktree_ref="A:/Riverview/package-worktree",
    )
    lifecycle.update_package_run(package_run_id=package_run_id, state="verifying")
    barrier = threading.Barrier(2)
    results = []

    def dispatch() -> None:
        local = CampaignLifecycleStore()
        barrier.wait(timeout=5)
        try:
            results.append(local.dispatch_package_acceptance(
                package_run_id=package_run_id, candidate_ref="commit:" + "b" * 40,
                candidate_version_hash="b" * 40, verification={"full": "pass"},
            ))
        except Exception as exc:  # the losing transaction must fail closed
            results.append(exc)

    threads = [threading.Thread(target=dispatch) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert results == [1, 1]
    assert lifecycle.package_run(stage_id=stage_id)["acceptance_dispatch_count"] == 1


@pytest.mark.parametrize("candidate_ref,candidate_version,dispatch_count,accepted_ref", [
    (None, "a" * 40, 1, None),
    ("commit:" + "a" * 40, None, 1, None),
    ("commit:" + "a" * 40, "a" * 40, 0, None),
    ("commit:" + "a" * 40, "a" * 40, 1, "commit:" + "b" * 40),
])
def test_postgres_malformed_accepted_projection_fails_closed(candidate_ref, candidate_version, dispatch_count, accepted_ref):
    lifecycle, _relay, objective_id, stage_id, _basis_id, _key = _package()
    package_run_id = lifecycle.begin_package_run(
        objective_id=objective_id, stage_id=stage_id, worktree_ref="A:/Riverview/package-worktree",
    )
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """UPDATE campaign_package_runs
                  SET state='accepted',candidate_ref=%s,candidate_version_hash=%s,
                      acceptance_dispatch_count=%s,acceptance_candidate_ref=%s,
                      acceptance_candidate_version_hash=%s
                WHERE package_run_id=%s""",
            (candidate_ref, candidate_version, dispatch_count, accepted_ref,
             "a" * 40 if accepted_ref else None, package_run_id),
        )
    executor = FakeExecutor([])
    with pytest.raises(LifecycleGateError):
        PackageEngineerLoop(
            lifecycle, objective_id=objective_id, stage_id=stage_id,
            worktree_ref="A:/Riverview/package-worktree", executor=executor,
            independent_acceptance=lambda candidate, *, worktree_ref: AcceptanceResult(True),
        ).run()
    assert executor.candidates == 0


def test_postgres_awaiting_acceptance_restart_waits_without_adapter_or_redispatch():
    lifecycle, _relay, objective_id, stage_id, _basis_id, _key = _package()
    package_run_id = lifecycle.begin_package_run(
        objective_id=objective_id, stage_id=stage_id, worktree_ref="A:/Riverview/package-worktree",
    )
    candidate_ref, version_hash = "commit:" + "c" * 40, "c" * 40
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """UPDATE campaign_package_runs
                  SET state='awaiting_independent_acceptance',candidate_ref=%s,
                      candidate_version_hash=%s,acceptance_dispatch_count=1,
                      acceptance_candidate_ref=%s,acceptance_candidate_version_hash=%s
                WHERE package_run_id=%s""",
            (candidate_ref, version_hash, candidate_ref, version_hash, package_run_id),
        )
    executor = FakeExecutor([])
    resumed = PackageEngineerLoop(
        CampaignLifecycleStore(), objective_id=objective_id, stage_id=stage_id,
        worktree_ref="A:/Riverview/package-worktree", executor=executor,
        independent_acceptance=lambda candidate, *, worktree_ref: (_ for _ in ()).throw(AssertionError("redispatched")),
    ).run()
    assert resumed.state == "awaiting_independent_acceptance"
    assert resumed.acceptance_dispatches == 1
    assert executor.candidates == 0


def test_postgres_five_candidate_ready_runners_invoke_one_validator():
    lifecycle, _relay, objective_id, stage_id, _basis_id, _key = _package()
    package_run_id = lifecycle.begin_package_run(
        objective_id=objective_id, stage_id=stage_id, worktree_ref="A:/Riverview/package-worktree",
    )
    candidate_ref, version_hash = "commit:" + "d" * 40, "d" * 40
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """UPDATE campaign_package_runs
                  SET state='candidate_ready',candidate_ref=%s,candidate_version_hash=%s,
                      acceptance_dispatch_count=0
                WHERE package_run_id=%s""",
            (candidate_ref, version_hash, package_run_id),
        )
    calls = []
    barrier = threading.Barrier(5)

    def run_one() -> None:
        local = CampaignLifecycleStore()
        executor = FakeExecutor([])
        loop = PackageEngineerLoop(
            local, objective_id=objective_id, stage_id=stage_id,
            worktree_ref="A:/Riverview/package-worktree", executor=executor,
            independent_acceptance=lambda candidate, *, worktree_ref: (calls.append(candidate.candidate_ref) or AcceptanceResult(True)),
        )
        barrier.wait(timeout=5)
        loop.run()

    threads = [threading.Thread(target=run_one) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert calls == [candidate_ref]
    projection = CampaignLifecycleStore().package_run(stage_id=stage_id)
    assert projection["acceptance_dispatch_count"] == 1
    assert projection["state"] == "accepted"


def test_postgres_expired_acceptance_owner_can_be_reclaimed_once():
    lifecycle, _relay, objective_id, stage_id, _basis_id, _key = _package()
    package_run_id = lifecycle.begin_package_run(
        objective_id=objective_id, stage_id=stage_id, worktree_ref="A:/Riverview/package-worktree",
    )
    candidate_ref, version_hash = "commit:" + "e" * 40, "e" * 40
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """UPDATE campaign_package_runs
                  SET state='candidate_ready',candidate_ref=%s,candidate_version_hash=%s
                WHERE package_run_id=%s""",
            (candidate_ref, version_hash, package_run_id),
        )
    owner_a, owner_b = uuid4(), uuid4()
    assert lifecycle.claim_package_acceptance(
        package_run_id=package_run_id, candidate_ref=candidate_ref,
        candidate_version_hash=version_hash, owner_id=owner_a, lease_seconds=1,
    ) == (True, 1)
    time.sleep(1.2)
    assert lifecycle.claim_package_acceptance(
        package_run_id=package_run_id, candidate_ref=candidate_ref,
        candidate_version_hash=version_hash, owner_id=owner_b, lease_seconds=60,
    ) == (True, 1)
    with pytest.raises(LifecycleGateError):
        lifecycle.record_package_acceptance(package_run_id=package_run_id, accepted=True, owner_id=owner_a)
