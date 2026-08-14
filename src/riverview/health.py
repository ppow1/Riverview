"""Executable health and event-store smoke checks.

Version: 0.2.0
"""

from __future__ import annotations

import argparse
import json
from uuid import uuid4

from riverview.database import connect
from riverview.river import EventStore, RiverEvent


def database_health() -> dict[str, object]:
    """Verify identity, migration, and required table visibility."""

    required = {"schema_migrations", "river_events", "diagnostic_events", "cookbook_entries"}
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), current_user")
        database, user = cursor.fetchone()
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        tables = {row[0] for row in cursor.fetchall()}
        cursor.execute("SELECT migration_id FROM schema_migrations ORDER BY migration_id")
        migrations = [row[0] for row in cursor.fetchall()]
    missing = sorted(required - tables)
    if missing:
        raise RuntimeError(f"RIV-DB-0005: Required tables are missing: {', '.join(missing)}")
    return {"status": "healthy", "database": database, "user": user, "migrations": migrations}


def event_smoke() -> dict[str, object]:
    """Append, idempotently replay, and read one acceptance event."""

    aggregate_id = uuid4()
    key = f"acceptance:{uuid4()}"
    event = RiverEvent(
        event_type="riverview.acceptance.probe",
        aggregate_type="acceptance_probe",
        aggregate_id=aggregate_id,
        idempotency_key=key,
        payload={"tool_version": "0.2.0"},
    )
    store = EventStore()
    first = store.append(event)
    replay = store.append(event)
    stream = store.read_aggregate("acceptance_probe", aggregate_id)
    if not first.inserted or replay.inserted or len(stream) != 1:
        raise RuntimeError("RIV-EVT-0004: Event acceptance invariant failed.")
    return {
        "status": "healthy",
        "sequence_id": first.sequence_id,
        "idempotent_replay": True,
        "stream_length": len(stream),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Riverview runtime acceptance")
    parser.add_argument("check", choices=("database", "event"))
    args = parser.parse_args()
    result = database_health() if args.check == "database" else event_smoke()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()