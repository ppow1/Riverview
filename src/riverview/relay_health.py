"""Live lifecycle acceptance for Riverview Relay.

Version: 0.4.0
"""

from __future__ import annotations

import json
from uuid import uuid4

from riverview.database import connect
from riverview.relay import RelayStore


def acceptance() -> dict[str, object]:
    store = RelayStore()
    key = f"relay-acceptance:{uuid4()}"
    first = store.enqueue("relay.noop", {}, "acceptance", key)
    duplicate = store.enqueue("relay.noop", {}, "acceptance", key)
    claimed = store.claim("acceptance-worker", 30)
    if not claimed or claimed.work_order_id != first.work_order_id or duplicate.work_order_id != first.work_order_id:
        raise RuntimeError("RIV-WRK-0005: Claim or idempotency invariant failed.")
    store.heartbeat(claimed.work_order_id, "acceptance-worker", 30)
    store.complete(claimed.work_order_id, "acceptance-worker", {"status": "accepted"})

    timeout = store.enqueue("relay.noop", {}, "acceptance", f"relay-timeout:{uuid4()}")
    timed_claim = store.claim("timeout-worker", 30)
    if not timed_claim or timed_claim.work_order_id != timeout.work_order_id:
        raise RuntimeError("RIV-WRK-0005: Timeout probe claim failed.")
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE work_orders SET lease_expires_at=now()-interval '1 second' WHERE work_order_id=%s", (timeout.work_order_id,))
    expired = store.sweep_expired()
    if timeout.work_order_id not in expired:
        raise RuntimeError("RIV-WRK-0004: Expired lease was not escalated.")
    return {"status":"healthy","idempotent_enqueue":True,"claim_heartbeat_complete":True,"timeout_escalated":True}


if __name__ == "__main__":
    print(json.dumps(acceptance(), indent=2, sort_keys=True))