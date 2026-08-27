from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from riverview.resources.control import DurableResourcePlanner, DurableResourcePolicy, ResourceControlError, ResourcePolicyStore, SeatClaim, SeatClaimStore
from riverview.resources.registry import ResourceRegistry


class FakeCursor:
    description = [type("Column", (), {"name": name}) for name in ("policy_id", "revision", "mode", "parameters", "changed_by", "authority", "rationale", "steward_lock", "updated_at")]

    def __init__(self, *, locked: bool = False, duplicate_claim: bool = False):
        self.policy = ["codex-fleet", 1, "HIGHEST_CAPACITY", {}, "system", "system", "initial", locked, datetime.now(UTC)]
        self.rowcount = 0
        self.duplicate_claim = duplicate_claim
        self.claim_row = (uuid4(), "C3", "work-1", "worker-1", "claimed", datetime.now(UTC))
        self.last_query = ""

    def execute(self, sql, params=()):
        self.last_query = sql
        if "INSERT INTO resource_seat_claims" in sql and self.duplicate_claim:
            raise RuntimeError("unique constraint")
        if sql.startswith("UPDATE resource_policy"):
            self.policy[1] = params[0]
            self.policy[2] = params[1] if isinstance(params[1], str) and params[1] in {"DRAIN", "PRESERVE", "PRIORITY"} else self.policy[2]
            self.policy[4] = params[3] if len(params) > 3 else self.policy[4]
            self.rowcount = 1
        elif sql.startswith("UPDATE resource_seat_claims"):
            self.rowcount = 1
        elif sql.startswith("INSERT"):
            self.rowcount = 1
        else:
            self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def fetchone(self):
        if "resource_policy" in self.last_query:
            return tuple(self.policy)
        return self.claim_row

    def fetchall(self):
        return []


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def cursor(self):
        return self._cursor


def factory_for(cursor):
    return lambda: FakeConnection(cursor)


def test_policy_store_rejects_unknown_modes_before_database_access():
    def forbidden():
        raise AssertionError("database must not be touched")

    with pytest.raises(ResourceControlError, match="unsupported"):
        ResourcePolicyStore(forbidden).set("NOT_A_POLICY", actor="steward", authority="steward")


def test_steward_lock_rejects_lower_authority_mutation():
    cursor = FakeCursor(locked=True)
    store = ResourcePolicyStore(factory_for(cursor))
    with pytest.raises(ResourceControlError, match="Steward-locked"):
        store.set("DRAIN", {"target_seat": "C3"}, actor="grace", authority="delegated-operations")


def test_steward_can_change_policy_and_lock():
    cursor = FakeCursor()
    store = ResourcePolicyStore(factory_for(cursor))
    changed = store.set("DRAIN", {"target_seat": "C3"}, actor="steward", authority="steward", rationale="retirement plan")
    assert changed.mode == "DRAIN"
    assert changed.revision == 2


def test_reset_consumption_is_not_an_ordinary_policy_mutation():
    cursor = FakeCursor()
    store = ResourcePolicyStore(factory_for(cursor))
    with pytest.raises(ResourceControlError, match="reset-credit"):
        store.set("HIGHEST_CAPACITY", {"consume_reset": True}, actor="grace", authority="delegated-operations")


def test_duplicate_active_seat_claim_is_fail_closed():
    cursor = FakeCursor(duplicate_claim=True)
    store = SeatClaimStore(factory_for(cursor))
    with pytest.raises(ResourceControlError, match="already claimed"):
        store.claim("C3", "work-1", "worker-1")


def test_claim_transition_release_and_expiry_recovery_use_bounded_states():
    cursor = FakeCursor()
    store = SeatClaimStore(factory_for(cursor))
    claim = store.claim("C3", "work-1", "worker-1")
    assert claim.state == "claimed"
    store.transition(claim.claim_id, "running")
    store.release(claim.claim_id, reason="completed")
    assert store.recover_expired() == 1


def test_durable_planner_re_evaluates_after_atomic_claim_race():
    registry = ResourceRegistry.from_mappings([
        {"resource_id": f"codex.seat.{seat}", "provider_id": "codex-cli", "capabilities": ["bounded-engineering"], "classification_eligibility": ["river"], "health": "healthy", "available": True, "observed_capacity": capacity, "observed_at": "2026-08-27T00:00:00Z", "roles": ["writer"], "seat_id": seat}
        for seat, capacity in (("C1", 60), ("C2", 80), ("C3", 90))
    ])
    policy = DurableResourcePolicy("codex-fleet", 1, "HIGHEST_CAPACITY", {}, "steward", "steward", None, False, datetime(2026, 8, 27, 0, 15, tzinfo=UTC))

    class Policy:
        def get(self): return policy

    class Claims:
        def __init__(self): self.calls = []
        def claim(self, seat_id, work_id, owner_id, **kwargs):
            self.calls.append(seat_id)
            if seat_id == "C3": raise ResourceControlError("seat C3 is already claimed")
            return SeatClaim(uuid4(), seat_id, work_id, owner_id, "claimed", datetime.now(UTC))

    claims = Claims()
    claimed, reason = DurableResourcePlanner(registry, Policy(), claims).claim_automatic("work-1", "worker-1", now=datetime(2026, 8, 27, 0, 15, tzinfo=UTC))
    assert claims.calls == ["C3", "C2"]
    assert claimed.seat_id == "C2"
    assert "claim race" in reason
