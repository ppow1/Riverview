import pytest
from uuid import uuid4

from riverview.database import connect
from riverview.notifications import NotificationStore


def test_notification_type_and_payload_are_closed() -> None:
    with pytest.raises(ValueError, match="closed"):
        NotificationStore().emit(idempotency_key="x", notification_type="execute", checkpoint_id="RIV-X", summary="x", evidence_refs=("e",))


def test_steward_attention_classes_are_exactly_once_and_operator_visible() -> None:
    store = NotificationStore()
    key = f"test:steward-attention:{uuid4()}"
    first = store.emit(
        idempotency_key=key,
        notification_type="blocked_requires_steward",
        checkpoint_id="RIV-HERMES-TRANCHE2-BLOCKED",
        summary="Riverview Hermes needs your assistance.",
        evidence_refs=("tranche2:gateway-restart-authorization",),
    )
    second = store.emit(
        idempotency_key=key,
        notification_type="blocked_requires_steward",
        checkpoint_id="RIV-HERMES-TRANCHE2-BLOCKED",
        summary="Riverview Hermes needs your assistance.",
        evidence_refs=("tranche2:gateway-restart-authorization",),
    )
    assert first == second
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT notification_type,summary,state FROM steward_notifications WHERE notification_id=%s", (first,))
        assert cursor.fetchone() == ("blocked_requires_steward", "Riverview Hermes needs your assistance.", "queued")
