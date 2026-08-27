"""RUN-004B bounded one-go runner integration tests."""

from __future__ import annotations

from collections import deque
from uuid import uuid4

import pytest

from riverview.campaign.one_go import CampaignOneGoRunner, OneGoError, WorkerSlot
from riverview.campaign import DefectInput
from riverview.relay import AttemptIdentity, ClaimedWork
from riverview.relay.store import FencedClaimedWork
from riverview.resources.control import ResourceControlError, SeatClaim


def _fenced(role: str) -> FencedClaimedWork:
    return FencedClaimedWork(
        AttemptIdentity(uuid4(), uuid4(), 1, uuid4(), uuid4()),
        "relay.noop", "1", {}, 30, 5, uuid4(), "worker-seat", role,
    )


class FakeRelay:
    def __init__(self, roles: list[str]) -> None:
        self.pending = deque(_fenced(role) for role in roles)
        self.completed: list[AttemptIdentity] = []

    def claim_fenced(self, _worker_id, _worker_instance_id, *, seat_id, role, work_order_id=None, objective_id=None):
        for item in tuple(self.pending):
            if item.role == role:
                self.pending.remove(item)
                return item
        return None

    def complete_fenced(self, identity, _result):
        self.completed.append(identity)


class FakeLifecycle:
    def __init__(self) -> None:
        self.running: list[ClaimedWork] = []
        self.handoffs = 0
        self.repairs = 0
        self.validations: list[dict] = []

    def mark_running(self, work):
        self.running.append(work)

    def handoff_writer_to_validation(self, *_args, **_kwargs):
        self.handoffs += 1
        return uuid4()

    def record_repair_completion(self, *_args, **_kwargs):
        self.repairs += 1
        return uuid4()

    def record_validation(self, work, **kwargs):
        self.validations.append({"work": work, **kwargs})
        return uuid4()


def _runner(roles, executors, relay=None, lifecycle=None):
    slots = (WorkerSlot("writer-worker", "writer-slot", ("writer",), uuid4()),
             WorkerSlot("validator-worker", "validator-slot", ("validator",), uuid4()),
             WorkerSlot("repair-worker", "repair-slot", ("repair_writer",), uuid4()),
             WorkerSlot("revalidator-worker", "revalidator-slot", ("revalidator",), uuid4()))
    instance = CampaignOneGoRunner(slots, executors, relay=relay or FakeRelay(roles), lifecycle=lifecycle or FakeLifecycle(), max_steps=20)
    instance.admit_eligible_stages = lambda: ()
    return instance


def _success(**extra):
    return {"status": "succeeded", "result_version_hash": "a" * 40,
            "implementation_ref": "commit:" + "a" * 40,
            "evidence_refs": ["execution:one"], **extra}


def test_one_go_advances_writer_to_independent_validator_without_manual_handoff():
    relay = FakeRelay(["writer", "validator"])
    lifecycle = FakeLifecycle()
    runner = _runner(["writer", "validator"], {
        "writer": lambda _work: _success(),
        "validator": lambda _work: _success(verdict="PASS", basis_hash="basis", findings_summary=(), defects=()),
        "repair_writer": lambda _work: _success(), "revalidator": lambda _work: _success(),
    }, relay, lifecycle)
    outcomes = runner.run(max_steps=4)
    assert [outcome["role"] for outcome in outcomes] == ["writer", "validator"]
    assert lifecycle.handoffs == 1
    assert lifecycle.validations[0]["verdict"] == "PASS"
    assert len(relay.completed) == 2


def test_one_go_runs_validation_failure_repair_and_revalidation_loop():
    relay = FakeRelay(["writer", "validator", "repair_writer", "revalidator"])
    lifecycle = FakeLifecycle()
    runner = _runner(["writer", "validator", "repair_writer", "revalidator"], {
        "writer": lambda _work: _success(),
        "validator": lambda _work: _success(verdict="FAIL", basis_hash="basis", findings_summary=("defect",), defects=(DefectInput("criterion", "blocking", "expected", "observed", "evidence:test", "repair"),)),
        "repair_writer": lambda _work: _success(),
        "revalidator": lambda _work: _success(verdict="PASS", basis_hash="basis", findings_summary=(), defects=()),
    }, relay, lifecycle)
    outcomes = runner.run(max_steps=8)
    assert [outcome["role"] for outcome in outcomes] == ["writer", "validator", "repair_writer", "revalidator"]
    assert [entry["verdict"] for entry in lifecycle.validations] == ["FAIL", "PASS"]
    assert lifecycle.repairs == 1
    assert len(relay.completed) == 4


def test_one_go_preserves_stale_fence_and_does_not_dispatch_downstream(monkeypatch):
    relay = FakeRelay(["writer", "validator"])
    lifecycle = FakeLifecycle()
    original_complete = relay.complete_fenced

    def stale(_identity, _result):
        raise RuntimeError("RIV-WRK-0003: Terminal result was late or stale.")

    relay.complete_fenced = stale
    runner = _runner(["writer", "validator"], {
        "writer": lambda _work: _success(), "validator": lambda _work: _success(verdict="PASS", basis_hash="basis", findings_summary=(), defects=()),
        "repair_writer": lambda _work: _success(), "revalidator": lambda _work: _success(),
    }, relay, lifecycle)
    outcome = runner.tick()
    assert outcome["status"] == "stale"
    assert lifecycle.handoffs == 0
    assert lifecycle.validations == []
    relay.complete_fenced = original_complete


def test_one_go_is_bounded_and_worker_slots_are_configurable():
    relay = FakeRelay([])
    runner = _runner([], {role: lambda _work: _success() for role in ("writer", "validator", "repair_writer", "revalidator")}, relay)
    assert runner.run(max_steps=3) == ()
    assert all(slot.seat_id != "C1" for slot in runner.workers)


def test_one_go_handles_two_bounded_repair_cycles_without_collapsing_history():
    class RepairLoopRelay(FakeRelay):
        def complete_fenced(self, identity, result):
            super().complete_fenced(identity, result)
            if len(self.completed) in {4, 5}:
                self.pending.append(_fenced("repair_writer" if len(self.completed) == 4 else "revalidator"))

    relay = RepairLoopRelay(["writer", "validator", "repair_writer", "revalidator"])
    lifecycle = FakeLifecycle()
    validation_count = 0

    def validate(_work):
        nonlocal validation_count
        validation_count += 1
        failed = validation_count < 3
        return _success(verdict="FAIL" if failed else "PASS", basis_hash="basis", findings_summary=("defect",) if failed else (), defects=(DefectInput("criterion", "blocking", "expected", "observed", "evidence:test", "repair"),) if failed else ())

    runner = _runner(["writer", "validator", "repair_writer", "revalidator", "repair_writer", "revalidator"], {
        "writer": lambda _work: _success(), "validator": validate,
        "repair_writer": lambda _work: _success(), "revalidator": validate,
    }, relay, lifecycle)
    outcomes = runner.run(max_steps=12)
    assert [outcome["role"] for outcome in outcomes] == ["writer", "validator", "repair_writer", "revalidator", "repair_writer", "revalidator"]
    assert [entry["verdict"] for entry in lifecycle.validations] == ["FAIL", "FAIL", "PASS"]


def test_one_go_resume_uses_persisted_pending_role_without_replaying_writer():
    relay = FakeRelay(["writer", "validator"])
    lifecycle = FakeLifecycle()
    first = _runner(["writer"], {role: lambda _work: _success() for role in ("writer", "validator", "repair_writer", "revalidator")}, relay, lifecycle)
    assert [item["role"] for item in first.run(max_steps=1)] == ["writer"]
    second = _runner(["validator"], {role: lambda _work: _success(verdict="PASS", basis_hash="basis", findings_summary=(), defects=()) for role in ("writer", "validator", "repair_writer", "revalidator")}, relay, lifecycle)
    assert [item["role"] for item in second.run(max_steps=1)] == ["validator"]


class FakeResourceClaims:
    def __init__(self) -> None:
        self.seat_claim = SeatClaim(uuid4(), "C3", "reservation", "worker", "claimed", None)
        self.calls: list[tuple[str, object]] = []

    def claim(self, seat_id, work_id, owner_id):
        self.calls.append(("claim", (seat_id, work_id, owner_id)))
        return self.seat_claim

    def attach_work(self, claim_id, work_id):
        self.calls.append(("attach", (claim_id, work_id)))

    def transition(self, claim_id, state):
        self.calls.append(("transition", (claim_id, state)))

    def release(self, claim_id, *, reason, failed=False):
        self.calls.append(("release", (claim_id, reason, failed)))


class BusyResourceClaims(FakeResourceClaims):
    def claim(self, seat_id, work_id, owner_id):
        raise ResourceControlError("seat is already claimed")


class FakeResourcePlanner:
    def __init__(self, claim):
        self.claim = claim

    def claim_automatic(self, work_id, owner_id, *, role):
        return self.claim, f"selected C3 under HIGHEST_CAPACITY for {role}"


class SeatRelay(FakeRelay):
    def claim_fenced(self, worker_id, worker_instance_id, *, seat_id, role, **kwargs):
        assert seat_id == "C3"
        item = _fenced(role)
        return FencedClaimedWork(
            AttemptIdentity(item.identity.work_order_id, item.identity.attempt_id, item.identity.lease_generation, item.identity.fencing_token, item.identity.worker_instance_id),
            item.action_type, item.action_version, item.parameters, item.hard_timeout_seconds, item.expected_duration_seconds, item.correlation_id,
            "C3", role,
        )


def test_resource_claim_wraps_automatic_admission_and_releases_success():
    resources = FakeResourceClaims()
    runner = CampaignOneGoRunner(
        (WorkerSlot("auto-worker", "AUTO", ("writer",), uuid4()),),
        {"writer": lambda _work: _success(), "validator": lambda _work: _success(), "repair_writer": lambda _work: _success(), "revalidator": lambda _work: _success()},
        relay=SeatRelay(["writer"]), lifecycle=FakeLifecycle(),
        resource_planner=FakeResourcePlanner(resources.seat_claim), resource_claim_store=resources,
    )
    runner.admit_eligible_stages = lambda: ()
    outcome = runner.tick()
    assert outcome["status"] == "succeeded"
    assert [call[0] for call in resources.calls] == ["attach", "transition", "transition", "release"]
    assert resources.calls[-1][1][2] is False


def test_resource_claim_releases_failed_when_executor_raises():
    resources = FakeResourceClaims()
    runner = CampaignOneGoRunner(
        (WorkerSlot("auto-worker", "AUTO", ("writer",), uuid4()),),
        {"writer": lambda _work: (_ for _ in ()).throw(RuntimeError("provider failed")), "validator": lambda _work: _success(), "repair_writer": lambda _work: _success(), "revalidator": lambda _work: _success()},
        relay=SeatRelay(["writer"]), lifecycle=FakeLifecycle(),
        resource_planner=FakeResourcePlanner(resources.seat_claim), resource_claim_store=resources,
        attention_delivery=lambda _key: {"status": "delivered"},
    )
    runner.admit_eligible_stages = lambda: ()
    outcome = runner.tick()
    assert outcome["status"] == "failed"
    assert resources.calls[-1][0] == "release"
    assert resources.calls[-1][1][2] is True


def test_explicit_resource_claim_failure_does_not_substitute_seat():
    resources = BusyResourceClaims()
    runner = CampaignOneGoRunner(
        (WorkerSlot("fixed-worker", "C2", ("writer",), uuid4()),),
        {role: lambda _work: _success() for role in ("writer", "validator", "repair_writer", "revalidator")},
        relay=FakeRelay(["writer"]), lifecycle=FakeLifecycle(),
        resource_planner=FakeResourcePlanner(resources.seat_claim), resource_claim_store=resources,
    )
    runner.admit_eligible_stages = lambda: ()
    with pytest.raises(OneGoError, match="explicit seat C2"):
        runner.tick()
