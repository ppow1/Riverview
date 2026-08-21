"""PostgreSQL diagnostic persistence with a bounded local evidence fallback.

Version: 0.3.2
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from riverview.database import DatabaseConfig, connect
from riverview.diagnostics.models import DiagnosticEvent

DEFAULT_SPOOL = Path(r"A:\Riverview\runtime\diagnostics\spool")


@dataclass(frozen=True, slots=True)
class PersistenceResult:
    """Where diagnostic evidence was durably written."""

    destination: str
    event_id: str
    checkpoint_id: str
    fallback_path: str | None = None


class DiagnosticStore:
    """Persist diagnostics to PostgreSQL or an append-only emergency spool."""

    def __init__(
        self,
        config: DatabaseConfig | None = None,
        spool_root: Path = DEFAULT_SPOOL,
        connection_factory: Callable[..., AbstractContextManager[Any]] = connect,
    ) -> None:
        self._config = config
        self._spool_root = spool_root
        self._connection_factory = connection_factory

    def emit(self, event: DiagnosticEvent) -> PersistenceResult:
        """Write a diagnostic once; fall back locally when PostgreSQL cannot accept it."""

        record = event.as_record()
        try:
            with self._connection_factory(self._config) as connection, connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO diagnostic_events (
                        event_id, checkpoint_id, component, operation, workflow_id, attempt,
                        severity, failure_class, summary, evidence_refs, dependency_state,
                        cookbook_entry, recovery_state, occurred_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING""",
                    (
                        record["event_id"], record["checkpoint_id"], record["component"],
                        record["operation"], record["workflow_id"], record["attempt"],
                        record["severity"], record["failure_class"], record["summary"],
                        json.dumps(record["evidence_refs"]), json.dumps(record["dependency_state"]),
                        record["cookbook_entry"], record["recovery_state"], record["occurred_at"],
                    ),
                )
                if record["severity"] in {"error", "critical"} or record["recovery_state"] == "escalated":
                    notification_type = "critical_failure" if record["severity"] == "critical" else "steward_checkpoint"
                    cursor.execute(
                        """INSERT INTO steward_notifications(notification_id,idempotency_key,notification_type,checkpoint_id,summary,evidence_refs,state)
                           VALUES(%s,%s,%s,%s,%s,%s::jsonb,'queued') ON CONFLICT(idempotency_key) DO NOTHING""",
                        (uuid4(), f"diagnostic:{record['event_id']}", notification_type, record["checkpoint_id"], record["summary"][:1000], json.dumps([record["event_id"], *record["evidence_refs"]])),
                    )
            return PersistenceResult("postgresql", record["event_id"], record["checkpoint_id"])
        except (RuntimeError, OSError, TypeError, ValueError) as database_error:
            return self._spool(event, database_error)

    def _spool(self, event: DiagnosticEvent, database_error: Exception) -> PersistenceResult:
        """Append emergency evidence without treating it as authoritative state."""

        try:
            self._spool_root.mkdir(parents=True, exist_ok=True)
            path = self._spool_root / f"diagnostics-{datetime.now(UTC):%Y%m%d}.ndjson"
            envelope = {
                "spool_version": "0.3.0",
                "authoritative": False,
                "spooled_at": datetime.now(UTC).isoformat(),
                "database_failure": type(database_error).__name__,
                "diagnostic": event.as_record(),
            }
            line = json.dumps(envelope, sort_keys=True, separators=(",", ":")) + os.linesep
            with path.open("a", encoding="utf-8", newline="") as stream:
                stream.write(line)
                stream.flush()
                os.fsync(stream.fileno())
            return PersistenceResult("emergency_spool", str(event.event_id), event.checkpoint_id, str(path))
        except Exception as spool_error:
            raise RuntimeError(f"RIV-DIA-0002: Database and emergency spool both failed: {spool_error}") from spool_error
