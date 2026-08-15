"""Durable, bounded bridge replay and recovery for RV-008.6."""

from __future__ import annotations

import json
from collections.abc import Iterable
from uuid import UUID, uuid4

from riverview.database import connect

CHECKPOINT = "RIV-0086-0001"
ALLOWED_OPERATIONS = frozenset({"wake", "mcp"})


class BridgeRecoveryStore:
    """Persist one bounded recovery state machine per request/correlation/operation."""

    def begin(
        self,
        request_id: UUID,
        correlation_id: UUID,
        *,
        operation: str = "wake",
        max_attempts: int = 2,
    ) -> UUID:
        if operation not in ALLOWED_OPERATIONS:
            raise ValueError(f"{CHECKPOINT}: unsupported bridge operation")
        if not 1 <= max_attempts <= 3:
            raise ValueError(f"{CHECKPOINT}: max_attempts must be between 1 and 3")
        recovery_id = uuid4()
        key = f"bridge:{operation}:{request_id}:{correlation_id}"
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO bridge_recovery_attempts(
                    recovery_id,request_id,correlation_id,operation,attempt_key,state,max_attempts
                ) VALUES(%s,%s,%s,%s,%s,'pending',%s)
                ON CONFLICT(attempt_key) DO NOTHING""",
                (recovery_id, request_id, correlation_id, operation, key, max_attempts),
            )
            cursor.execute(
                "SELECT recovery_id FROM bridge_recovery_attempts WHERE attempt_key=%s",
                (key,),
            )
            return cursor.fetchone()[0]

    def record_failure(
        self,
        recovery_id: UUID,
        *,
        failure_class: str,
        evidence_refs: Iterable[str] = (),
    ) -> dict[str, object]:
        if not failure_class.strip():
            raise ValueError(f"{CHECKPOINT}: failure_class is required")
        refs = self._refs(evidence_refs)
        with connect() as connection, connection.cursor() as cursor:
            row = self._lock(cursor, recovery_id)
            if row["state"] in {"recovered", "escalated"}:
                return row
            attempts = int(row["attempt_count"]) + 1
            terminal = attempts >= int(row["max_attempts"])
            state = "escalated" if terminal else "retryable"
            escalation_id = row["escalation_id"]
            if terminal and escalation_id is None:
                escalation_id = uuid4()
                cursor.execute(
                    """INSERT INTO steward_escalations(
                        escalation_id,checkpoint_id,reason,state,evidence_refs
                    ) VALUES(%s,%s,%s,'open',%s::jsonb)""",
                    (escalation_id, CHECKPOINT, f"Bridge {row['operation']} recovery exhausted bounded retries.", json.dumps(refs)),
                )
            cursor.execute(
                """UPDATE bridge_recovery_attempts
                   SET state=%s,failure_class=%s,attempt_count=%s,evidence_refs=%s::jsonb,
                       escalation_id=%s,updated_at=now(),resolved_at=CASE WHEN %s THEN now() ELSE resolved_at END
                 WHERE recovery_id=%s""",
                (state, failure_class, attempts, json.dumps(refs), escalation_id, terminal, recovery_id),
            )
            self._event(cursor, row, "bridge.recovery.failed", {"failure_class": failure_class, "state": state, "attempt_count": attempts})
            return self._snapshot(cursor, recovery_id)

    def record_success(self, recovery_id: UUID, *, evidence_refs: Iterable[str] = ()) -> dict[str, object]:
        refs = self._refs(evidence_refs)
        with connect() as connection, connection.cursor() as cursor:
            row = self._lock(cursor, recovery_id)
            if row["state"] == "escalated":
                raise RuntimeError(f"{CHECKPOINT}: escalated recovery cannot be silently resumed")
            if row["state"] == "recovered":
                return row
            cursor.execute(
                """UPDATE bridge_recovery_attempts
                   SET state='recovered',evidence_refs=%s::jsonb,updated_at=now(),resolved_at=now()
                 WHERE recovery_id=%s""",
                (json.dumps(refs), recovery_id),
            )
            self._event(cursor, row, "bridge.recovery.recovered", {"evidence_refs": refs})
            return self._snapshot(cursor, recovery_id)

    def snapshot(self, recovery_id: UUID) -> dict[str, object]:
        with connect() as connection, connection.cursor() as cursor:
            return self._snapshot(cursor, recovery_id)

    @staticmethod
    def _refs(refs: Iterable[str]) -> list[str]:
        result = list(dict.fromkeys(refs))
        if len(result) > 8 or any(not ref.strip() or len(ref) > 240 for ref in result):
            raise ValueError(f"{CHECKPOINT}: evidence references exceed bounded limits")
        return result

    @staticmethod
    def _lock(cursor, recovery_id: UUID) -> dict[str, object]:
        cursor.execute(
            """SELECT recovery_id,request_id,correlation_id,operation,state,failure_class,
                      attempt_count,max_attempts,evidence_refs,escalation_id
                 FROM bridge_recovery_attempts WHERE recovery_id=%s FOR UPDATE""",
            (recovery_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError(f"{CHECKPOINT}: recovery identity not found")
        names = [item.name for item in cursor.description]
        return dict(zip(names, row, strict=True))

    @staticmethod
    def _snapshot(cursor, recovery_id: UUID) -> dict[str, object]:
        cursor.execute(
            """SELECT recovery_id,request_id,correlation_id,operation,state,failure_class,
                      attempt_count,max_attempts,evidence_refs,escalation_id,created_at,updated_at,resolved_at
                 FROM bridge_recovery_attempts WHERE recovery_id=%s""",
            (recovery_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError(f"{CHECKPOINT}: recovery identity not found")
        names = [item.name for item in cursor.description]
        return dict(zip(names, row, strict=True))

    @staticmethod
    def _event(cursor, row: dict[str, object], event_type: str, payload: dict[str, object]) -> None:
        cursor.execute(
            """INSERT INTO river_events(
                event_id,event_type,aggregate_type,aggregate_id,correlation_id,causation_id,
                idempotency_key,classification,payload,occurred_at
            ) VALUES(%s,%s,'bridge_recovery',%s,%s,%s,%s,'river',%s::jsonb,now())
            ON CONFLICT(idempotency_key) DO NOTHING""",
            (
                uuid4(), event_type, row["recovery_id"], row["correlation_id"], None,
                f"{event_type}:{row['recovery_id']}:{row['attempt_count']}", json.dumps(payload),
            ),
        )
