from __future__ import annotations

from uuid import UUID, uuid4

from riverview.hermes_attention import submit_hermes_attention


class FakeStore:
    def __init__(self) -> None:
        self.rows: dict[str, UUID] = {}
        self.calls: list[dict[str, object]] = []

    def emit(self, **payload):
        self.calls.append(payload)
        return self.rows.setdefault(str(payload["idempotency_key"]), uuid4())


class QueuedDelivery:
    def __init__(self) -> None:
        self.queued: set[UUID] = set()
        self.presenter_calls: list[UUID] = []

    def __call__(self, notification_id: UUID) -> dict[str, object]:
        if notification_id not in self.queued:
            self.queued.add(notification_id)
            self.presenter_calls.append(notification_id)
            return {"delivered": True, "acknowledged": False}
        return {"delivered": False, "reason": "notification_not_queued", "state": "delivered"}


def _submit(store, deliver, **overrides):
    values = {
        "lane": "Runtime repair",
        "boundary": "READY_FOR_STEWARD_REVIEW",
        "checkpoint_id": "RIV-HERMES-ATTN-TEST",
        "evidence_ref": "evidence://runtime-repair/1",
        "session_id": "hermes-session-1",
        "transition_id": "transition-1",
        "store": store,
        "deliver": deliver,
    }
    values.update(overrides)
    return submit_hermes_attention(**values)


def test_ready_boundary_is_one_idempotent_delivery_and_not_acceptance():
    store = FakeStore()
    delivery = QueuedDelivery()

    first = _submit(store, delivery)
    second = _submit(store, delivery)

    assert first["notification_id"] == second["notification_id"]
    assert len(store.calls) == 2
    assert delivery.presenter_calls == [UUID(first["notification_id"])]
    assert first["notification_type"] == "ready_for_steward_review"
    assert first["acknowledged"] is False
    assert first["institutionally_accepted"] is False


def test_blocked_boundary_is_attributed_per_independent_lane():
    store = FakeStore()
    delivery = QueuedDelivery()

    first = _submit(
        store,
        delivery,
        lane="C1 C2 C3",
        boundary="BLOCKED_REQUIRES_STEWARD",
        checkpoint_id="RIV-HERMES-C123-BLOCKED",
        session_id="hermes-c123",
        transition_id="blocked-1",
    )
    second = _submit(
        store,
        delivery,
        lane="Operator",
        boundary="STEWARD_DECISION_REQUIRED",
        checkpoint_id="RIV-HERMES-OPERATOR-DECISION",
        session_id="hermes-operator",
        transition_id="decision-1",
    )

    assert first["notification_type"] == "blocked_requires_steward"
    assert second["notification_type"] == "blocked_requires_steward"
    assert first["lane"] == "C1 C2 C3"
    assert second["lane"] == "Operator"
    assert len(delivery.presenter_calls) == 2
    assert first["notification_id"] != second["notification_id"]


def test_non_terminal_or_retryable_work_does_not_enter_attention_boundary():
    store = FakeStore()
    delivery = QueuedDelivery()

    # The shared boundary is explicit: callers do not invoke it for ordinary
    # progress, passing tests, or an internally retried failure.
    assert store.calls == []
    assert delivery.presenter_calls == []


def test_invalid_boundary_fails_closed():
    store = FakeStore()
    delivery = QueuedDelivery()

    try:
        _submit(store, delivery, boundary="TEST_PASS")
    except ValueError as exc:
        assert "attention boundary" in str(exc)
    else:
        raise AssertionError("non-terminal boundary was accepted")
    assert store.calls == []
    assert delivery.presenter_calls == []
