"""Contract tests for Riverview Relay records.

Version: 0.4.0
"""

from uuid import uuid4

from riverview.relay import WorkOrder


def test_work_order_contract_keeps_structured_parameters() -> None:
    order = WorkOrder("relay.noop", {"step": 147}, "test", "key", uuid4(), uuid4(), "0.4.0", 5, 30)
    assert order.parameters == {"step": 147}
    assert order.status == "queued"