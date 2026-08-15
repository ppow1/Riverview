"""PostgreSQL acceptance for the RV-004.5 full-loop mailbox contract."""

from __future__ import annotations

import json
import time
from uuid import uuid4

from riverview.database import connect
from riverview.mailbox import REASONING_CONSUMER_ID, MailboxStore


def accept() -> dict[str, object]:
    store = MailboxStore()
    key = f"acceptance.rv0045.{uuid4()}"
    request = store.submit(
        sender_id="rv-0045-acceptance",
        requester_id=REASONING_CONSUMER_ID,
        message_type="acceptance.reasoning.request",
        idempotency_key=key,
        payload={"summary": "bounded full-loop acceptance"},
        ttl_seconds=120,
    )
    acknowledged = store.acknowledge_reasoning(request.request_id, request.correlation_id)
    acknowledgement_retry = store.acknowledge_reasoning(request.request_id, request.correlation_id)
    claimed = store.claim_reasoning(request.request_id, request.correlation_id, lease_seconds=120)
    claim_retry = store.claim_reasoning(request.request_id, request.correlation_id, lease_seconds=120)
    response = store.respond_reasoning(
        request.request_id,
        request.correlation_id,
        response_type="advice",
        summary="Bounded acceptance response.",
        evidence_refs=["acceptance:rv0045"],
        escalation_required=False,
    )
    response_retry = store.respond_reasoning(
        request.request_id,
        request.correlation_id,
        response_type="advice",
        summary="Retry must reconcile the canonical response.",
        evidence_refs=["acceptance:rv0045:retry"],
        escalation_required=False,
    )
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT event_type,correlation_id,causation_id FROM river_events "
            "WHERE aggregate_type='mailbox_request' AND aggregate_id=%s ORDER BY sequence_id",
            (request.request_id,),
        )
        events = cursor.fetchall()
        cursor.execute(
            "SELECT completion_state,acknowledgement_state,claim_state,response_id "
            "FROM mailbox_messages WHERE request_id=%s",
            (request.request_id,),
        )
        final = cursor.fetchone()
    timeout = store.submit(
        sender_id="rv-0045-acceptance",
        requester_id=REASONING_CONSUMER_ID,
        message_type="acceptance.timeout",
        idempotency_key=f"{key}.timeout",
        payload={"summary": "bounded timeout"},
        ttl_seconds=1,
    )
    time.sleep(1.1)
    first_expiry = store.expire_and_escalate()
    second_expiry = store.expire_and_escalate()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM steward_escalations WHERE mailbox_request_id=%s",
            (timeout.request_id,),
        )
        escalation_count = cursor.fetchone()[0]
    if final[0] != "completed" or escalation_count != 1:
        raise RuntimeError("RIV-MCP-0008: full-loop acceptance did not complete safely.")
    return {
        "status": "healthy",
        "request_id": str(request.request_id),
        "correlation_id": str(request.correlation_id),
        "response_id": str(response.response_id),
        "duplicate_ack_same": acknowledgement_retry.request_id == acknowledged.request_id,
        "duplicate_claim_same": claim_retry.claim_owner == claimed.claim_owner,
        "duplicate_response_same": response_retry.response_id == response.response_id,
        "event_types": [row[0] for row in events],
        "timeout_request_id": str(timeout.request_id),
        "timeout_first_count": len(first_expiry),
        "timeout_second_count": len(second_expiry),
        "timeout_escalation_count": escalation_count,
    }


if __name__ == "__main__":
    print(json.dumps(accept(), indent=2, sort_keys=True))
