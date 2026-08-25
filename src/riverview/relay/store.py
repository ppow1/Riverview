"""Transactional waypoint and work-order state for Riverview Relay.

Version: 0.4.0
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from collections.abc import Iterator
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
    attempt_id: UUID | None = None
    lease_generation: int | None = None
    fencing_token: UUID | None = None
    worker_instance_id: UUID | None = None
    seat_id: str | None = None
    role: str | None = None


@dataclass(frozen=True, slots=True)
class AttemptIdentity:
    """The complete authority fence for one executable attempt."""

    work_order_id: UUID
    attempt_id: UUID
    lease_generation: int
    fencing_token: UUID
    worker_instance_id: UUID


class FenceNotCurrentError(RuntimeError):
    """The exact attempt no longer owns the active work-order fence."""


class FencedReconciliation:
    """A transaction-scoped authority guard for external reconciliation."""

    def __init__(self, cursor: Any, identity: AttemptIdentity, correlation_id: UUID) -> None:
        self._cursor = cursor
        self.identity = identity
        self.correlation_id = correlation_id

    def complete(self, result: dict[str, Any]) -> None:
        """Complete the protected attempt on the same row-lock transaction."""
        self._cursor.execute(
            """UPDATE work_orders SET status='succeeded', result_report=%s::jsonb,
                      finished_at=now(), lease_expires_at=NULL,
                      active_attempt_id=NULL, lease_generation=NULL, fencing_token=NULL,
                      worker_instance_id=NULL, seat_id=NULL, role=NULL, updated_at=now()
                WHERE work_order_id=%s AND status IN ('claimed','running')
                  AND active_attempt_id=%s AND lease_generation=%s
                  AND fencing_token=%s AND worker_instance_id=%s""",
            (json.dumps(result), self.identity.work_order_id, self.identity.attempt_id,
             self.identity.lease_generation, self.identity.fencing_token,
             self.identity.worker_instance_id),
        )
        if self._cursor.rowcount != 1:
            raise FenceNotCurrentError("RIV-WRK-0003: Protected terminal update lost the active fence.")
        self._cursor.execute(
            """UPDATE work_order_attempts
                  SET finished_at=now(), terminal_state='succeeded', exit_code=0
                WHERE attempt_id=%s AND work_order_id=%s""",
            (self.identity.attempt_id, self.identity.work_order_id),
        )
        RelayStore._append_event(
            self._cursor, event_type="runner.state_transition",
            work_order_id=self.identity.work_order_id,
            correlation_id=self.correlation_id,
            payload={"from": "running", "to": "succeeded", "attempt_id": str(self.identity.attempt_id)},
            idempotency_key=f"runner.complete:{self.identity.attempt_id}",
        )


@dataclass(frozen=True, slots=True)
class FencedClaimedWork:
    """Claimed work plus its immutable active-attempt identity."""

    identity: AttemptIdentity
    action_type: str
    action_version: str
    parameters: dict[str, Any]
    hard_timeout_seconds: int
    expected_duration_seconds: int
    correlation_id: UUID
    seat_id: str
    role: str


class RelayStore:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    @staticmethod
    def _append_event(cursor: Any, *, event_type: str, work_order_id: UUID, correlation_id: UUID,
                      payload: dict[str, Any], idempotency_key: str | None = None) -> bool:
        event = RiverEvent(
            event_type=event_type,
            aggregate_type="work_order",
            aggregate_id=work_order_id,
            correlation_id=correlation_id,
            causation_id=work_order_id,
            idempotency_key=idempotency_key or f"{event_type}:{work_order_id}",
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
        return cursor.rowcount == 1

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

    def claim_fenced(
        self,
        worker_id: str,
        worker_instance_id: UUID,
        *,
        seat_id: str,
        role: str,
        lease_seconds: int = 30,
        work_order_id: UUID | None = None,
    ) -> FencedClaimedWork | None:
        """Claim one order and persist one exact, transactionally fenced attempt."""
        if seat_id not in {"C1", "C2", "C3"}:
            raise ValueError("RIV-WRK-0010: seat_id must be C1, C2, or C3.")
        if not role.strip():
            raise ValueError("RIV-WRK-0010: role must not be empty.")
        attempt_id = uuid4()
        fencing_token = uuid4()
        with connect(self._config) as connection, connection.cursor() as cursor:
            claim_sql = """SELECT work_order_id, action_type, action_version, parameters,
                          hard_timeout_seconds, expected_duration_seconds, correlation_id
                     FROM work_orders
                    WHERE status = 'queued' AND active_attempt_id IS NULL
                      AND (role IS NULL OR role=%s)
                      AND (seat_id IS NULL OR seat_id=%s)
                """
            claim_params: list[Any] = [role, seat_id]
            if work_order_id is not None:
                claim_sql += " AND work_order_id=%s"
                claim_params.append(work_order_id)
            claim_sql += " ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
            cursor.execute(claim_sql, claim_params)
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute("SELECT COALESCE(MAX(lease_generation), 0) + 1 FROM work_order_attempts WHERE work_order_id=%s", (row[0],))
            attempt = int(cursor.fetchone()[0])
            cursor.execute(
                """INSERT INTO work_order_attempts(
                    attempt_id, work_order_id, attempt, worker_id, lease_generation,
                    fencing_token, worker_instance_id, seat_id, role,
                    last_heartbeat_at
                ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,now())""",
                (attempt_id, row[0], attempt, worker_id, attempt, fencing_token,
                 worker_instance_id, seat_id, role),
            )
            cursor.execute(
                """UPDATE work_orders
                      SET status='claimed', active_attempt_id=%s,
                          lease_generation=%s, fencing_token=%s,
                          worker_instance_id=%s, seat_id=%s, role=%s,
                          lease_owner=%s, lease_expires_at=now()+make_interval(secs=>%s),
                          last_heartbeat_at=now(), started_at=COALESCE(started_at,now()),
                          updated_at=now()
                    WHERE work_order_id=%s AND status='queued' AND active_attempt_id IS NULL""",
                (attempt_id, attempt, fencing_token, worker_instance_id, seat_id, role,
                 worker_id, lease_seconds, row[0]),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-WRK-0011: claim lost the locked work order.")
            self._append_event(
                cursor, event_type="runner.attempt.claimed", work_order_id=row[0],
                correlation_id=self._correlation(cursor, row[0]),
                payload={"attempt_id": str(attempt_id), "lease_generation": attempt,
                         "fencing_token": str(fencing_token),
                         "worker_instance_id": str(worker_instance_id),
                         "seat_id": seat_id, "role": role},
                idempotency_key=f"runner.attempt.claimed:{attempt_id}",
            )
            return FencedClaimedWork(
                AttemptIdentity(row[0], attempt_id, attempt, fencing_token, worker_instance_id),
                row[1], row[2], row[3], row[4], row[5], row[6], seat_id, role,
            )

    def claim(self, worker_id: str, lease_seconds: int = 30, *,
              worker_instance_id: UUID | None = None, seat_id: str = "C1",
              role: str = "writer", work_order_id: UUID | None = None) -> ClaimedWork | None:
        """Compatibility claim; it still creates the exact fenced identity."""
        instance = worker_instance_id or uuid4()
        claim = self.claim_fenced(worker_id, instance, seat_id=seat_id, role=role,
                                  lease_seconds=lease_seconds, work_order_id=work_order_id)
        if claim is None:
            return None
        return ClaimedWork(
            work_order_id=claim.identity.work_order_id,
            action_type=claim.action_type,
            action_version=claim.action_version,
            parameters=claim.parameters,
            hard_timeout_seconds=claim.hard_timeout_seconds,
            attempt=claim.identity.lease_generation,
            attempt_id=claim.identity.attempt_id,
            lease_generation=claim.identity.lease_generation,
            fencing_token=claim.identity.fencing_token,
            worker_instance_id=claim.identity.worker_instance_id,
            seat_id=claim.seat_id,
            role=claim.role,
        )

    @staticmethod
    def _correlation(cursor: Any, work_order_id: UUID) -> UUID:
        cursor.execute("SELECT correlation_id FROM work_orders WHERE work_order_id=%s", (work_order_id,))
        return cursor.fetchone()[0]

    def heartbeat_fenced(self, identity: AttemptIdentity, lease_seconds: int = 30) -> None:
        """Refresh liveness only when the full active-attempt tuple matches."""
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """UPDATE work_orders SET last_heartbeat_at=now(),
                          lease_expires_at=now()+make_interval(secs=>%s), updated_at=now()
                    WHERE work_order_id=%s AND status IN ('claimed','running')
                      AND active_attempt_id=%s AND lease_generation=%s
                      AND fencing_token=%s AND worker_instance_id=%s""",
                (lease_seconds, identity.work_order_id, identity.attempt_id,
                 identity.lease_generation, identity.fencing_token, identity.worker_instance_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-WRK-0002: Heartbeat was fenced by a newer attempt.")
            cursor.execute(
                """UPDATE work_order_attempts SET last_heartbeat_at=now()
                    WHERE attempt_id=%s AND work_order_id=%s AND lease_generation=%s
                      AND fencing_token=%s AND worker_instance_id=%s""",
                (identity.attempt_id, identity.work_order_id, identity.lease_generation,
                 identity.fencing_token, identity.worker_instance_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-WRK-0002: Attempt heartbeat identity was not found.")

    def heartbeat(self, work_order_id: UUID, worker_id: str, lease_seconds: int = 30) -> None:
        """Compatibility heartbeat resolved to the current exact identity."""
        with connect(self._config) as connection, connection.cursor() as cursor:
            identity = self._lookup_legacy_identity(cursor, work_order_id, worker_id)
        self.heartbeat_fenced(identity, lease_seconds)

    def progress_fenced(self, identity: AttemptIdentity, *, idempotency_key: str,
                        message: str, detail: dict[str, Any] | None = None) -> None:
        """Record one meaningful progress event and increment exactly once."""
        if not idempotency_key.strip() or not message.strip():
            raise ValueError("RIV-WRK-0012: progress requires idempotency_key and message.")
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT correlation_id FROM work_orders
                    WHERE work_order_id=%s AND status IN ('claimed','running')
                      AND active_attempt_id=%s AND lease_generation=%s
                      AND fencing_token=%s AND worker_instance_id=%s
                    FOR UPDATE""",
                (identity.work_order_id, identity.attempt_id, identity.lease_generation,
                 identity.fencing_token, identity.worker_instance_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("RIV-WRK-0002: Progress was fenced by a newer attempt.")
            payload = {"message": message[:240], "detail": detail or {},
                       "attempt_id": str(identity.attempt_id),
                       "worker_instance_id": str(identity.worker_instance_id)}
            cursor.execute(
                """INSERT INTO river_events(
                    event_id,event_type,aggregate_type,aggregate_id,correlation_id,
                    causation_id,idempotency_key,classification,payload,occurred_at)
                   VALUES(%s,'runner.progress','work_order',%s,%s,%s,%s,%s,%s::jsonb,now())
                   ON CONFLICT(idempotency_key) DO NOTHING""",
                (uuid4(), identity.work_order_id, row[0], identity.attempt_id,
                 idempotency_key, Classification.RIVER.value, json.dumps(payload)),
            )
            if cursor.rowcount != 1:
                return
            cursor.execute(
                """UPDATE work_order_attempts SET last_progress_at=now(), progress_count=progress_count+1
                    WHERE attempt_id=%s AND work_order_id=%s AND lease_generation=%s
                      AND fencing_token=%s AND worker_instance_id=%s""",
                (identity.attempt_id, identity.work_order_id, identity.lease_generation,
                 identity.fencing_token, identity.worker_instance_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-WRK-0013: Progress attempt update was fenced.")
            cursor.execute(
                """UPDATE work_orders SET last_progress_at=now(), progress_count=progress_count+1,
                          updated_at=now()
                    WHERE work_order_id=%s AND active_attempt_id=%s AND lease_generation=%s
                      AND fencing_token=%s AND worker_instance_id=%s""",
                (identity.work_order_id, identity.attempt_id, identity.lease_generation,
                 identity.fencing_token, identity.worker_instance_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-WRK-0013: Progress work-order update was fenced.")

    def progress(self, work_order_id: UUID, worker_id: str, *, phase: str, progress_percent: int | None = None, summary: str = "") -> None:
        identity = self._legacy_identity(work_order_id, worker_id)
        self.progress_fenced(identity, idempotency_key=f"legacy-progress:{identity.attempt_id}:{phase}:{summary}",
                             message=summary or phase,
                             detail={"phase": phase[:120], "progress_percent": progress_percent})

    def complete_fenced(self, identity: AttemptIdentity, result: dict[str, Any]) -> None:
        """Persist terminal success only for the currently active exact attempt."""
        rejected = False
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT correlation_id FROM work_orders WHERE work_order_id=%s FOR UPDATE""",
                (identity.work_order_id,),
            )
            row = cursor.fetchone()
            cursor.execute(
                """SELECT 1 FROM work_orders
                    WHERE work_order_id=%s AND status IN ('claimed','running')
                      AND active_attempt_id=%s AND lease_generation=%s
                      AND fencing_token=%s AND worker_instance_id=%s""",
                (identity.work_order_id, identity.attempt_id, identity.lease_generation,
                 identity.fencing_token, identity.worker_instance_id),
            )
            if row is None or cursor.fetchone() is None:
                self._record_late_result(cursor, identity, result, row[0] if row else uuid4())
                rejected = True
            else:
                cursor.execute(
                    """UPDATE work_orders SET status='succeeded', result_report=%s::jsonb,
                          finished_at=now(), lease_expires_at=NULL,
                          active_attempt_id=NULL, lease_generation=NULL, fencing_token=NULL,
                          worker_instance_id=NULL, seat_id=NULL, role=NULL, updated_at=now()
                    WHERE work_order_id=%s AND active_attempt_id=%s AND lease_generation=%s
                      AND fencing_token=%s AND worker_instance_id=%s""",
                    (json.dumps(result), identity.work_order_id, identity.attempt_id,
                     identity.lease_generation, identity.fencing_token, identity.worker_instance_id),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("RIV-WRK-0003: Terminal update lost the active fence.")
                cursor.execute("UPDATE work_order_attempts SET finished_at=now(), terminal_state='succeeded', exit_code=0 WHERE attempt_id=%s", (identity.attempt_id,))
                self._append_event(cursor, event_type="runner.state_transition", work_order_id=identity.work_order_id,
                                   correlation_id=row[0], payload={"from": "running", "to": "succeeded",
                                   "attempt_id": str(identity.attempt_id)},
                                   idempotency_key=f"runner.complete:{identity.attempt_id}")
        if rejected:
            raise RuntimeError("RIV-WRK-0003: Terminal result was late or stale.")

    def assert_fence_current(self, identity: AttemptIdentity) -> None:
        """Validate the exact live attempt before an external side effect.

        The row lock serializes this check with lease expiry/re-claim
        transactions at the authority boundary. Terminal completion remains
        fenced separately after reconciliation succeeds.
        """
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT 1 FROM work_orders
                   WHERE work_order_id=%s AND status IN ('claimed','running')
                     AND active_attempt_id=%s AND lease_generation=%s
                     AND fencing_token=%s AND worker_instance_id=%s
                     AND lease_expires_at > now()
                   FOR UPDATE""",
                (identity.work_order_id, identity.attempt_id, identity.lease_generation,
                 identity.fencing_token, identity.worker_instance_id),
            )
            if cursor.fetchone() is None:
                raise FenceNotCurrentError("RIV-WRK-0003: Attempt fence is not current before reconciliation.")

    @contextmanager
    def reconciliation_authority(self, identity: AttemptIdentity) -> Iterator[FencedReconciliation]:
        """Hold exact work-order authority across reconciliation side effects.

        `expire_leases` uses `FOR UPDATE SKIP LOCKED`, so it cannot expire or
        replace this attempt while the context is active. A process failure
        closes the PostgreSQL transaction, releases the lock, and leaves the
        still-running/expired order recoverable by the normal sweeper.
        """
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT correlation_id FROM work_orders
                   WHERE work_order_id=%s AND status IN ('claimed','running')
                     AND active_attempt_id=%s AND lease_generation=%s
                     AND fencing_token=%s AND worker_instance_id=%s
                     AND lease_expires_at > now()
                   FOR UPDATE""",
                (identity.work_order_id, identity.attempt_id, identity.lease_generation,
                 identity.fencing_token, identity.worker_instance_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise FenceNotCurrentError("RIV-WRK-0003: Attempt fence is not current before reconciliation.")
            yield FencedReconciliation(cursor, identity, row[0])

    def complete(self, work_order_id: UUID, worker_id: str, result: dict[str, Any]) -> None:
        self.complete_fenced(self._legacy_identity(work_order_id, worker_id), result)

    def _lookup_legacy_identity(self, cursor: Any, work_order_id: UUID, worker_id: str) -> AttemptIdentity:
        cursor.execute(
            """SELECT active_attempt_id, lease_generation, fencing_token, worker_instance_id
                 FROM work_orders WHERE work_order_id=%s AND lease_owner=%s
                   AND active_attempt_id IS NOT NULL""", (work_order_id, worker_id))
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("RIV-WRK-0002: No active fenced lease belongs to this worker.")
        return AttemptIdentity(work_order_id, row[0], row[1], row[2], row[3])

    def _legacy_identity(self, work_order_id: UUID, worker_id: str) -> AttemptIdentity:
        with connect(self._config) as connection, connection.cursor() as cursor:
            return self._lookup_legacy_identity(cursor, work_order_id, worker_id)

    def _record_late_result(self, cursor: Any, identity: AttemptIdentity, result: dict[str, Any], correlation_id: UUID) -> None:
        cursor.execute(
            """UPDATE work_order_attempts SET late_or_stale=true, terminal_state='late_result',
                      late_result_ref=%s WHERE attempt_id=%s AND work_order_id=%s""",
            (json.dumps(result)[:4000], identity.attempt_id, identity.work_order_id),
        )
        self._append_event(cursor, event_type="runner.result.late_rejected",
                           work_order_id=identity.work_order_id, correlation_id=correlation_id,
                           payload={"attempt_id": str(identity.attempt_id), "result": result},
                           idempotency_key=f"runner.late-result:{identity.attempt_id}:{uuid4()}")

    def expire_leases(self) -> list[AttemptIdentity]:
        """Fence expired attempts and make retry-safe work eligible again."""
        expired: list[AttemptIdentity] = []
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT work_order_id, active_attempt_id, lease_generation,
                          fencing_token, worker_instance_id, correlation_id
                     FROM work_orders
                    WHERE status IN ('claimed','running')
                      AND active_attempt_id IS NOT NULL
                      AND lease_expires_at < now()
                    FOR UPDATE SKIP LOCKED"""
            )
            for work_order_id, attempt_id, generation, token, instance, correlation in cursor.fetchall():
                identity = AttemptIdentity(work_order_id, attempt_id, generation, token, instance)
                expired.append(identity)
                cursor.execute(
                    """UPDATE work_order_attempts
                          SET terminal_state='timed_out', finished_at=now()
                        WHERE attempt_id=%s AND work_order_id=%s AND lease_generation=%s
                          AND fencing_token=%s AND worker_instance_id=%s""",
                    (attempt_id, work_order_id, generation, token, instance),
                )
                cursor.execute(
                    """UPDATE work_orders SET status='timed_out', error_checkpoint='RIV-WRK-0004',
                              finished_at=now(), active_attempt_id=NULL, lease_generation=NULL,
                              fencing_token=NULL, worker_instance_id=NULL, seat_id=NULL, role=NULL,
                              lease_expires_at=NULL, updated_at=now()
                        WHERE work_order_id=%s AND active_attempt_id=%s AND lease_generation=%s
                          AND fencing_token=%s AND worker_instance_id=%s""",
                    (work_order_id, attempt_id, generation, token, instance),
                )
                self._append_event(cursor, event_type="runner.attempt.timed_out",
                                   work_order_id=work_order_id, correlation_id=correlation,
                                   payload={"attempt_id": str(attempt_id), "lease_generation": generation},
                                   idempotency_key=f"runner.timeout:{attempt_id}")
        return expired

    def requeue_timed_out(self, work_order_id: UUID) -> None:
        """Reopen one timed-out order for a new, newly fenced attempt."""
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """UPDATE work_orders SET status='queued', error_checkpoint=NULL,
                          finished_at=NULL, updated_at=now()
                    WHERE work_order_id=%s AND status='timed_out'
                    RETURNING correlation_id""", (work_order_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("RIV-WRK-0015: Work order is not eligible for retry.")
            self._append_event(cursor, event_type="runner.retry.queued", work_order_id=work_order_id,
                               correlation_id=row[0], payload={"status": "queued"},
                               idempotency_key=f"runner.retry.queued:{work_order_id}")

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
