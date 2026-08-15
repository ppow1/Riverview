import pytest

from riverview.notifications import NotificationStore


def test_notification_type_and_payload_are_closed() -> None:
    with pytest.raises(ValueError, match="closed"):
        NotificationStore().emit(idempotency_key="x", notification_type="execute", checkpoint_id="RIV-X", summary="x", evidence_refs=("e",))
