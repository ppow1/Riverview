"""RUN-003 live PostgreSQL acceptance tests for exact campaign attempt fencing.

Version: 0.1.0
"""

from __future__ import annotations

import threading
import time
from dataclasses import replace
from uuid import uuid4

import pytest

from riverview.database import connect
from riverview.relay import RelayStore


def _claimed(role: str = "validator", seat: str = "C2"):
    store = RelayStore()
    for _ in range(10):
        order = store.enqueue("relay.noop", {"delay_seconds": 1}, "run003-pytest", f"run003:{uuid4()}")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE work_orders SET role=%s,seat_id=%s WHERE work_order_id=%s", (role, seat, order.work_order_id))
        claimed = store.claim("run003-pytest", 30, worker_instance_id=uuid4(), seat_id=seat,
                              role=role, work_order_id=order.work_order_id)
        if claimed is not None:
            return store, order, claimed, store._legacy_identity(order.work_order_id, "run003-pytest")
    pytest.fail("dedicated fencing fixture was repeatedly consumed before claim")


def test_claim_identity_and_heartbeat_are_distinct_from_progress() -> None:
    store, order, claimed, identity = _claimed()
    assert claimed.attempt_id and claimed.lease_generation and claimed.fencing_token
    assert claimed.worker_instance_id and claimed.seat_id == "C2" and claimed.role == "validator"

    store.heartbeat_fenced(identity, 30)
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT progress_count FROM work_orders WHERE work_order_id=%s", (order.work_order_id,))
        assert cursor.fetchone()[0] == 0

    store.progress_fenced(identity, idempotency_key=f"progress:{claimed.attempt_id}", message="step complete")
    store.progress_fenced(identity, idempotency_key=f"progress:{claimed.attempt_id}", message="duplicate")
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT progress_count,last_progress_at FROM work_orders WHERE work_order_id=%s", (order.work_order_id,))
        count, timestamp = cursor.fetchone()
        assert count == 1 and timestamp is not None
    store.complete_fenced(identity, {"status": "succeeded", "test": "identity"})


def test_reconciliation_authority_blocks_expiry_during_real_postgres_side_effect() -> None:
    store, order, claimed, identity = _claimed()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE work_orders SET lease_expires_at=now()+interval '0.5 seconds' WHERE work_order_id=%s",
            (order.work_order_id,),
        )

    entered = threading.Event()
    attempted = threading.Event()
    finished = threading.Event()
    sweep: dict[str, object] = {}

    def expire_concurrently() -> None:
        entered.wait(timeout=5)
        attempted.set()
        sweep["expired"] = store.expire_leases()
        finished.set()

    worker = threading.Thread(target=expire_concurrently)
    worker.start()
    with store.reconciliation_authority(identity) as authority:
        entered.set()
        assert attempted.wait(timeout=2)
        assert finished.wait(timeout=2)  # SKIP LOCKED returns while A owns the row lock
        time.sleep(1.2)  # the lease is logically expired, but A owns the row lock
        sweep["reconciled"] = True
        authority.complete({"status": "succeeded", "protected": True})
    worker.join(timeout=5)

    assert sweep["expired"] == []
    assert sweep["reconciled"] is True
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT status,active_attempt_id FROM work_orders WHERE work_order_id=%s", (order.work_order_id,))
        status, active_attempt = cursor.fetchone()
    assert status == "succeeded"
    assert active_attempt is None


def test_reconciliation_authority_failure_releases_lock_for_expiry_recovery() -> None:
    store, order, claimed, identity = _claimed()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE work_orders SET lease_expires_at=now()+interval '30 seconds' WHERE work_order_id=%s",
            (order.work_order_id,),
        )

    with pytest.raises(RuntimeError, match="reconciliation failure"):
        with store.reconciliation_authority(identity):
            raise RuntimeError("reconciliation failure")

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE work_orders SET lease_expires_at=now()-interval '1 second' WHERE work_order_id=%s", (order.work_order_id,))
    expired = store.expire_leases()
    assert any(item.attempt_id == identity.attempt_id for item in expired)
    store.requeue_timed_out(order.work_order_id)
    successor = store.claim("run003-pytest", 30, worker_instance_id=uuid4(), seat_id="C2",
                            role="validator", work_order_id=order.work_order_id)
    assert successor is not None
    store.complete_fenced(store._legacy_identity(order.work_order_id, "run003-pytest"), {"status": "succeeded"})


@pytest.mark.parametrize("field", ["fencing_token", "lease_generation", "worker_instance_id"])
def test_wrong_fencing_component_cannot_heartbeat_or_complete(field: str) -> None:
    store, order, claimed, identity = _claimed()
    wrong = replace(identity, **{field: uuid4() if field != "lease_generation" else identity.lease_generation + 1})
    with pytest.raises(RuntimeError, match="fenced|late or stale"):
        store.heartbeat_fenced(wrong, 30)
    with pytest.raises(RuntimeError, match="late or stale"):
        store.complete_fenced(wrong, {"status": "succeeded", "wrong": field})
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT status,active_attempt_id FROM work_orders WHERE work_order_id=%s", (order.work_order_id,))
        status, active_attempt = cursor.fetchone()
        assert status == "claimed" and active_attempt == claimed.attempt_id
    store.complete_fenced(identity, {"status": "succeeded", "test": field})


def test_expiry_retry_and_late_result_preservation() -> None:
    store, order, first, identity = _claimed()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE work_orders SET lease_expires_at=now()-interval '1 second' WHERE work_order_id=%s", (order.work_order_id,))
    assert any(item.attempt_id == first.attempt_id for item in store.expire_leases())
    store.requeue_timed_out(order.work_order_id)
    second = store.claim("run003-pytest", 30, worker_instance_id=uuid4(), seat_id="C2", role="validator")
    assert second is not None
    assert second.attempt_id != first.attempt_id
    assert second.fencing_token != first.fencing_token
    assert second.lease_generation > first.lease_generation

    with pytest.raises(RuntimeError, match="late or stale"):
        store.complete_fenced(identity, {"status": "succeeded", "stale": True})
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT late_or_stale FROM work_order_attempts WHERE attempt_id=%s", (first.attempt_id,))
        assert cursor.fetchone()[0] is True
        cursor.execute("SELECT status,active_attempt_id FROM work_orders WHERE work_order_id=%s", (order.work_order_id,))
        assert cursor.fetchone() == ("claimed", second.attempt_id)
    store.complete_fenced(store._legacy_identity(order.work_order_id, "run003-pytest"), {"status": "succeeded"})


def test_current_phase_has_no_objective_level_authority() -> None:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("""SELECT column_name FROM information_schema.columns
                         WHERE table_name='objectives' AND column_name='active_stage_id'""")
        assert cursor.fetchone() is None
        cursor.execute("""SELECT column_name FROM information_schema.columns
                         WHERE table_name='objective_stages' AND column_name IN ('sort_order','status')""")
        assert {row[0] for row in cursor.fetchall()} == {"sort_order", "status"}


def test_substantial_action_lease_covers_hard_timeout_with_grace() -> None:
    assert RelayStore.lease_seconds_for(1800) == 1860
    assert RelayStore.lease_seconds_for(30) == 30
    assert RelayStore.lease_seconds_for(1800, requested=120) == 120


def test_generic_relay_worker_cannot_claim_internal_campaign_action() -> None:
    store = RelayStore()
    order = store.enqueue("campaign.hermes.engineering", {}, "run003-internal", f"run003-internal:{uuid4()}")
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE work_orders SET seat_id='C3' WHERE work_order_id=%s", (order.work_order_id,))
    assert store.claim_fenced(
        "relay.primary", uuid4(), seat_id="C3", role="writer", work_order_id=order.work_order_id,
    ) is None
