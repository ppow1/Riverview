"""Transactional waypoint and work-order state for Riverview Relay.

Version: 0.4.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from riverview.database import DatabaseConfig, connect
from riverview.river.events import Classification, RiverEvent


@dataclass(frozen=True, slots=True)
class WorkOrder:
    action_type: str
    parameters: dict[str, Any]
    requested_by: str
    idempotency_key: str
    correlation_id: UUID
    work_order_id: UUID
    action_version: str
    expected_duration_seconds: int
    hard_timeout_seconds: int
    status: str = "queued"


@dataclass(frozen=True, slots=True)
class ClaimedWork:
    work_order_id: UUID
    action_type: str
    action_version: str
    parameters: dict[str, Any]
    hard_timeout_seconds: int
    attempt: int


class RelayStore:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    @staticmethod
    def _append_event(cursor: Any, *, event_type: str, work_order_id: UUID, correlation_id: UUID, payload: dict[str, Any]) -> None:
        event = RiverEvent(
            event_type=event_type,
            aggregate_type="work_order",
            aggregate_id=work_order_id,
            correlation_id=correlation_id,
            causation_id=work_order_id,
            idempotency_key=f"{event_type}:{work_order_id}",
            classification=Classification.RIVER,
            payload=payload,
        )
        cursor.execute(
            """INSERT INTO river_events(
                event_id,event_type,aggregate_type,aggregate_id,correlation_id,causation_id,
                idempotency_key,classification,payload,occurred_at
            ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
            ON CONFLICT(idempotency_key) DO NOTHING""",
            (event.event_id, event.event_type, event.aggregate_type, event.aggregate_id,
             event.correlation_id, event.causation_id, event.idempotency_key,
             event.classification.value, json.dumps(dict(event.payload)), event.occurred_at),
        )

    def enqueue(self, action_type: str, parameters: dict[str, Any], requested_by: str, idempotency_key: str, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> WorkOrder:
        """Create one durable order or return the existing idempotent order."""
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute("SELECT action_version, expected_duration_seconds, hard_timeout_seconds, enabled FROM approved_actions WHERE action_type=%s", (action_type,))
            action = cursor.fetchone()
            if not action or not action[3]:
                raise RuntimeError(f"RIV-WRK-0001: Action is unknown or disabled: {action_type}")
            order_id = uuid4(); correlation = correlation_id or uuid4()
            cursor.execute(
                """INSERT INTO work_orders (work_order_id, action_type, action_version, status, parameters, requested_by, idempotency_key, correlation_id, causation_id, expected_duration_seconds, hard_timeout_seconds)
                   VALUES (%s,%s,%s,'queued',%s::jsonb,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (idempotency_key) DO NOTHING
                   RETURNING work_order_id""",
                (order_id, action_type, action[0], json.dumps(parameters), requested_by, idempotency_key, correlation, causation_id, action[1], action[2]),
            )
            inserted = cursor.fetchone()
            if not inserted:
                cursor.execute("SELECT work_order_id FROM work_orders WHERE idempotency_key=%s", (idempotency_key,)); order_id = cursor.fetchone()[0]
            cursor.execute("SELECT action_type, parameters, requested_by, idempotency_key, correlation_id, work_order_id, action_version, expected_duration_seconds, hard_timeout_seconds, status FROM work_orders WHERE work_order_id=%s", (order_id,))
            row = cursor.fetchone()
            self._append_event(cursor, event_type="work.order.queued", work_order_id=row[5], correlation_id=row[4], payload={"action_type": row[0], "status": row[9]})
            return WorkOrder(*row)

    def claim(self, worker_id: str, lease_seconds: int = 30) -> ClaimedWork | None:
        """Claim one queued order without permitting duplicate workers."""
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """WITH candidate AS (
                       SELECT work_order_id FROM work_orders WHERE status='queued' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1
                   ), claimed AS (
                       UPDATE work_orders w SET status='claimed', lease_owner=%s, lease_expires_at=now()+make_interval(secs=>%s), last_heartbeat_at=now(), started_at=COALESCE(started_at,now()), updated_at=now()
                       FROM candidate c WHERE w.work_order_id=c.work_order_id
                       RETURNING w.work_order_id,w.action_type,w.action_version,w.parameters,w.hard_timeout_seconds
                   ) SELECT * FROM claimed""",
                (worker_id, lease_seconds),
            )
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute("SELECT COALESCE(MAX(attempt),0)+1 FROM work_order_attempts WHERE work_order_id=%s", (row[0],)); attempt = cursor.fetchone()[0]
            cursor.execute("INSERT INTO work_order_attempts (work_order_id,attempt,worker_id) VALUES (%s,%s,%s)", (row[0], attempt, worker_id))
            return ClaimedWork(*row, attempt)

    def heartbeat(self, work_order_id: UUID, worker_id: str, lease_seconds: int = 30) -> None:
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE work_orders SET status='running',last_heartbeat_at=now(),lease_expires_at=now()+make_interval(secs=>%s),updated_at=now() WHERE work_order_id=%s AND lease_owner=%s AND status IN ('claimed','running')", (lease_seconds, work_order_id, worker_id))
            if cursor.rowcount != 1: raise RuntimeError("RIV-WRK-0002: Heartbeat did not own an active lease.")

    def progress(self, work_order_id: UUID, worker_id: str, *, phase: str, progress_percent: int | None = None, summary: str = "") -> None:
        """Record one bounded human-visible progress pulse without changing lifecycle state."""

        bounded_percent = None if progress_percent is None else max(0, min(int(progress_percent), 100))
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """UPDATE work_orders
                   SET last_heartbeat_at=now(),updated_at=now(),result_report=COALESCE(result_report,'{}'::jsonb) || %s::jsonb
                   WHERE work_order_id=%s AND lease_owner=%s AND status IN ('claimed','running')""",
                (json.dumps({"phase": phase[:120], "progress_percent": bounded_percent, "last_activity": summary[:240]}), work_order_id, worker_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-WRK-0002: Progress did not own an active lease.")
            cursor.execute("SELECT correlation_id FROM work_orders WHERE work_order_id=%s", (work_order_id,))
            correlation_id = cursor.fetchone()[0]
            self._append_event(cursor, event_type="work.order.progress", work_order_id=work_order_id, correlation_id=correlation_id, payload={"status": "running", "phase": phase[:120], "progress_percent": bounded_percent, "summary": summary[:240]})

    def complete(self, work_order_id: UUID, worker_id: str, result: dict[str, Any]) -> None:
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE work_orders SET status='succeeded',result_report=%s::jsonb,finished_at=now(),lease_expires_at=NULL,updated_at=now() WHERE work_order_id=%s AND lease_owner=%s AND status IN ('claimed','running') RETURNING correlation_id", (json.dumps(result), work_order_id, worker_id))
            if cursor.rowcount != 1: raise RuntimeError("RIV-WRK-0003: Completion did not own an active lease.")
            correlation_id = cursor.fetchone()[0]
            cursor.execute("UPDATE work_order_attempts SET finished_at=now(),exit_code=0 WHERE work_order_id=%s AND worker_id=%s AND finished_at IS NULL", (work_order_id, worker_id))
            self._append_event(cursor, event_type="work.order.completed", work_order_id=work_order_id, correlation_id=correlation_id, payload={"status": "succeeded", "result_category": result.get("status", "succeeded")})

    def sweep_expired(self) -> list[UUID]:
        """Mark expired leases and open one Steward escalation per order."""
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE work_orders SET status='timed_out',error_checkpoint='RIV-WRK-0004',finished_at=now(),updated_at=now() WHERE status IN ('claimed','running') AND lease_expires_at < now() RETURNING work_order_id")
            expired = [row[0] for row in cursor.fetchall()]
            for order_id in expired:
                cursor.execute("INSERT INTO steward_escalations (escalation_id,work_order_id,checkpoint_id,reason,state) VALUES (%s,%s,'RIV-WRK-0004','Worker lease expired without completion.','open')", (uuid4(), order_id))
            return expired

    def retry_if_safe(self, work_order_id: UUID, correlation_id: UUID) -> WorkOrder:
        """Create one immutable retry-safe successor without rewriting history."""
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT action_type,action_version,parameters,requested_by,idempotency_key,
                          correlation_id,expected_duration_seconds,hard_timeout_seconds,status,error_checkpoint
                   FROM work_orders WHERE work_order_id=%s FOR UPDATE""",
                (work_order_id,),
            )
            row = cursor.fetchone()
            if row is None or row[5] != correlation_id:
                raise RuntimeError("RIV-GRC-0007: retry correlation does not match the work order.")
            if row[8] not in {"failed", "timed_out"}:
                raise RuntimeError("RIV-GRC-0007: work order is not in a retryable terminal state.")
            cursor.execute("SELECT successor_work_order_id FROM work_order_successor_lineage WHERE failed_work_order_id=%s", (work_order_id,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    """SELECT action_type,parameters,requested_by,idempotency_key,correlation_id,
                              work_order_id,action_version,expected_duration_seconds,hard_timeout_seconds,status
                       FROM work_orders WHERE work_order_id=%s""",
                    (existing[0],),
                )
                return WorkOrder(*cursor.fetchone())
            cursor.execute("SELECT retry_safe FROM approved_actions WHERE action_type=%s AND enabled=true", (row[0],))
            safe = cursor.fetchone()
            cursor.execute("SELECT count(*) FROM work_order_attempts WHERE work_order_id=%s", (work_order_id,))
            attempts = cursor.fetchone()[0]
            if not safe or not safe[0] or attempts >= 2:
                raise RuntimeError("RIV-GRC-0007: retry requires a Steward checkpoint.")
            successor = uuid4()
            retry_key = f"retry:{work_order_id}:2"
            cursor.execute(
                """INSERT INTO work_orders(
                    work_order_id,action_type,action_version,status,parameters,requested_by,
                    idempotency_key,correlation_id,causation_id,expected_duration_seconds,hard_timeout_seconds)
                   VALUES(%s,%s,%s,'queued',%s::jsonb,%s,%s,%s,%s,%s,%s)""",
                (successor, row[0], row[1], json.dumps(row[2]), row[3], retry_key, row[5], work_order_id, row[6], row[7]),
            )
            failure_class = "timeout" if row[8] == "timed_out" or row[9] == "RIV-EXE-0003" else "provider_failure"
            cursor.execute(
                """INSERT INTO work_order_successor_lineage(
                    lineage_id,failed_work_order_id,successor_work_order_id,attempt,failure_class,idempotency_key)
                   VALUES(%s,%s,%s,2,%s,%s)""",
                (uuid4(), work_order_id, successor, failure_class, retry_key),
            )
            self._append_event(
                cursor,
                event_type="work.order.successor.queued",
                work_order_id=successor,
                correlation_id=row[5],
                payload={"failed_work_order_id": str(work_order_id), "attempt": 2, "failure_class": failure_class},
            )
            cursor.execute(
                """SELECT action_type,parameters,requested_by,idempotency_key,correlation_id,
                          work_order_id,action_version,expected_duration_seconds,hard_timeout_seconds,status
                   FROM work_orders WHERE work_order_id=%s""",
                (successor,),
            )
            return WorkOrder(*cursor.fetchone())
