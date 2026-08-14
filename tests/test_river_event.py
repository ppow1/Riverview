"""Unit tests for the first River event contract.

Version: 0.2.1
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from riverview.river import Classification, RiverEvent


def test_event_is_immutable_and_payload_is_detached() -> None:
    source = {"step": 147}
    event = RiverEvent(
        event_type="workflow.step.ready",
        aggregate_type="workflow",
        aggregate_id=uuid4(),
        idempotency_key="workflow:one:147",
        payload=source,
        occurred_at=datetime(2026, 8, 14, tzinfo=UTC),
    )
    source["step"] = 999
    assert event.payload["step"] == 147
    assert event.classification is Classification.RIVER


def test_event_rejects_empty_identity_fields() -> None:
    with pytest.raises(ValueError, match="event_type"):
        RiverEvent(
            event_type=" ",
            aggregate_type="workflow",
            aggregate_id=uuid4(),
            idempotency_key="key",
            payload={},
        )


def test_event_requires_timezone_aware_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        RiverEvent(
            event_type="workflow.step.ready",
            aggregate_type="workflow",
            aggregate_id=uuid4(),
            idempotency_key="key",
            payload={},
            occurred_at=datetime(2026, 8, 14, tzinfo=UTC).replace(tzinfo=None),
        )