"""Exactly-once bounded notification records; delivery adapters remain separate."""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from riverview.database import connect


class NotificationStore:
    def emit(self, *, idempotency_key: str, notification_type: str, checkpoint_id: str, summary: str, evidence_refs: tuple[str, ...]) -> UUID:
        if notification_type not in {"steward_checkpoint", "critical_failure", "important_completion", "binding_condition"}:
            raise ValueError("RIV-NOT-0001: notification type is closed.")
        if not checkpoint_id.startswith("RIV-") or not 1 <= len(summary.strip()) <= 1000 or not evidence_refs:
            raise ValueError("RIV-NOT-0001: notification payload is missing or unbounded.")
        with connect() as connection, connection.cursor() as cursor:
            notification_id = uuid4()
            cursor.execute("""INSERT INTO steward_notifications(notification_id,idempotency_key,notification_type,checkpoint_id,summary,evidence_refs,state)
                            VALUES(%s,%s,%s,%s,%s,%s::jsonb,'queued') ON CONFLICT(idempotency_key) DO NOTHING""",
                           (notification_id,idempotency_key,notification_type,checkpoint_id,summary,json.dumps(evidence_refs)))
            cursor.execute("SELECT notification_id FROM steward_notifications WHERE idempotency_key=%s", (idempotency_key,))
            return cursor.fetchone()[0]

    def mark_delivered(self, notification_id: UUID) -> None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE steward_notifications SET state='delivered',delivered_at=COALESCE(delivered_at,now()) WHERE notification_id=%s AND state='queued'", (notification_id,))
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-NOT-0001: notification is not queued or does not exist.")
