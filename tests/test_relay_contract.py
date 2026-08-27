"""Contract tests for Riverview Relay records.

Version: 0.4.0
"""

from uuid import uuid4

from riverview.relay import AttemptIdentity, RelayStore, WorkOrder
from riverview.relay.store import FencedClaimedWork


def test_work_order_contract_keeps_structured_parameters() -> None:
    order = WorkOrder("relay.noop", {"step": 147}, "test", "key", uuid4(), uuid4(), "0.4.0", 5, 30)
    assert order.parameters == {"step": 147}
    assert order.status == "queued"


def test_compatibility_claim_preserves_correlation_id(monkeypatch) -> None:
    correlation_id = uuid4()
    fenced = FencedClaimedWork(
        identity=AttemptIdentity(uuid4(), uuid4(), 1, uuid4(), uuid4()),
        action_type="relay.noop", action_version="0.5.0", parameters={},
        hard_timeout_seconds=5, expected_duration_seconds=1,
        correlation_id=correlation_id, seat_id="C3", role="writer",
    )
    store = RelayStore()
    monkeypatch.setattr(store, "claim_fenced", lambda *args, **kwargs: fenced)
    claimed = store.claim("worker", worker_instance_id=uuid4(), seat_id="C3")
    assert claimed is not None
    assert claimed.correlation_id == correlation_id
