"""Transactional PostgreSQL event store.

Version: 0.2.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from riverview.database import DatabaseConfig, connect
from riverview.river.events import RiverEvent


@dataclass(frozen=True, slots=True)
class AppendResult:
    """Stable acknowledgement for accepted or previously accepted events."""

    sequence_id: int
    event_id: UUID
    inserted: bool


class EventStore:
    """Append and read River events without leaking connection mechanics."""

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def append(self, event: RiverEvent) -> AppendResult:
        """Append once by idempotency key and return the canonical event identity."""

        statement = """
            INSERT INTO river_events (
                event_id, event_type, aggregate_type, aggregate_id, correlation_id,
                causation_id, idempotency_key, classification, payload, occurred_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING sequence_id, event_id
        """
        try:
            with connect(self._config) as connection, connection.cursor() as cursor:
                cursor.execute(
                    statement,
                    (
                        event.event_id,
                        event.event_type,
                        event.aggregate_type,
                        event.aggregate_id,
                        event.correlation_id,
                        event.causation_id,
                        event.idempotency_key,
                        event.classification.value,
                        json.dumps(dict(event.payload)),
                        event.occurred_at,
                    ),
                )
                row = cursor.fetchone()
                if row:
                    return AppendResult(sequence_id=row[0], event_id=row[1], inserted=True)
                cursor.execute(
                    "SELECT sequence_id, event_id FROM river_events WHERE idempotency_key = %s",
                    (event.idempotency_key,),
                )
                existing = cursor.fetchone()
                if not existing:
                    raise RuntimeError("RIV-EVT-0002: Idempotency reconciliation found no event.")
                return AppendResult(sequence_id=existing[0], event_id=existing[1], inserted=False)
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"RIV-EVT-0001: Event append failed: {exc}") from exc

    def append_in_transaction(self, cursor: Any, event: RiverEvent) -> AppendResult:
        """Append using a caller-owned transaction."""
        cursor.execute(
            """INSERT INTO river_events(
                   event_id,event_type,aggregate_type,aggregate_id,correlation_id,
                   causation_id,idempotency_key,classification,payload,occurred_at)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
               ON CONFLICT(idempotency_key) DO NOTHING
               RETURNING sequence_id,event_id""",
            (event.event_id, event.event_type, event.aggregate_type, event.aggregate_id,
             event.correlation_id, event.causation_id, event.idempotency_key,
             event.classification.value, json.dumps(dict(event.payload)), event.occurred_at),
        )
        row = cursor.fetchone()
        if row:
            return AppendResult(sequence_id=row[0], event_id=row[1], inserted=True)
        cursor.execute("SELECT sequence_id,event_id FROM river_events WHERE idempotency_key=%s", (event.idempotency_key,))
        existing = cursor.fetchone()
        if not existing:
            raise RuntimeError("RIV-EVT-0002: Idempotency reconciliation found no event.")
        return AppendResult(sequence_id=existing[0], event_id=existing[1], inserted=False)

    def read_aggregate(self, aggregate_type: str, aggregate_id: UUID) -> list[dict[str, Any]]:
        """Read an aggregate stream in authoritative sequence order."""

        try:
            with connect(self._config) as connection, connection.cursor() as cursor:
                cursor.execute(
                    """SELECT sequence_id, event_id, event_type, payload, occurred_at
                       FROM river_events
                       WHERE aggregate_type = %s AND aggregate_id = %s
                       ORDER BY sequence_id""",
                    (aggregate_type, aggregate_id),
                )
                return [
                    {
                        "sequence_id": row[0],
                        "event_id": str(row[1]),
                        "event_type": row[2],
                        "payload": row[3],
                        "occurred_at": row[4].isoformat(),
                    }
                    for row in cursor.fetchall()
                ]
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"RIV-EVT-0003: Aggregate read failed: {exc}") from exc
