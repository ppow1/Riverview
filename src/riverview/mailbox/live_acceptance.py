"""PostgreSQL acceptance for RV-008.2 mailbox correlation.

Version: 0.10.0

Creates one bounded, completed acceptance lineage and leaves it as durable
evidence. No provider, browser, or execution adapter is invoked.
"""

from __future__ import annotations

import json
import time
from uuid import uuid4

from riverview.database import connect
from riverview.mailbox import MailboxStore


def accept() -> dict[str, object]:
    store = MailboxStore()
    key = f"acceptance.rv0082.{uuid4()}"
    first = store.submit(
        sender_id="acceptance",
        requester_id="acceptance",
        message_type="acceptance.request",
        idempotency_key=key,
        payload={"bounded": True},
    )
    duplicate = store.submit(
        sender_id="acceptance",
        requester_id="acceptance",
        message_type="acceptance.request",
        idempotency_key=key,
        payload={"bounded": True},
        correlation_id=uuid4(),
    )
    if duplicate.request_id != first.request_id or duplicate.correlation_id != first.correlation_id:
        raise RuntimeError("RIV-MCP-0008: duplicate delivery created a second lineage.")
    store.acknowledge(first.request_id, "acceptance")
    store.claim(first.request_id, "acceptance")
    response = store.respond(
        first.request_id,
        responder_id="acceptance",
        response_type="acceptance.response",
        payload={"result": "one-lineage"},
    )
    duplicate_response = store.respond(
        first.request_id,
        responder_id="acceptance-retry",
        response_type="acceptance.response",
        payload={"result": "must-not-replace"},
    )
    if duplicate_response.response_id != response.response_id:
        raise RuntimeError("RIV-MCP-0008: duplicate response replaced the canonical response.")
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT event_type,correlation_id,causation_id FROM river_events WHERE aggregate_type='mailbox_request' AND aggregate_id=%s ORDER BY sequence_id",
            (first.request_id,),
        )
        events = cursor.fetchall()
    if not events or any(row[1] != first.correlation_id for row in events):
        raise RuntimeError("RIV-EVT-0004: mailbox River correlation is incomplete.")
    expiring = store.submit(
        sender_id="acceptance",
        requester_id="acceptance",
        message_type="acceptance.expiry",
        idempotency_key=f"{key}.expiry",
        payload={"bounded": True},
        ttl_seconds=1,
    )
    time.sleep(1.1)
    if expiring.request_id not in store.expire():
        raise RuntimeError("RIV-MCP-0008: expiry did not transition the pending request.")
    return {
        "status": "healthy",
        "request_id": str(first.request_id),
        "correlation_id": str(first.correlation_id),
        "response_id": str(response.response_id),
        "duplicate_delivery_reused_request": True,
        "duplicate_response_reused_response": True,
        "expiry_transition_verified": True,
        "event_types": [row[0] for row in events],
    }


if __name__ == "__main__":
    print(json.dumps(accept(), indent=2, sort_keys=True))
