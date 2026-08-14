"""Small, ordered PostgreSQL migration runner.

Version: 0.3.0
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from riverview.database.connection import connect


def apply_migration(path: Path, migration_id: str, version: str) -> bool:
    """Apply an unapplied migration and record its exact checksum."""

    sql = path.read_text(encoding="utf-8-sig")
    checksum = hashlib.sha256(sql.encode()).hexdigest()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT checksum_sha256 FROM schema_migrations WHERE migration_id = %s", (migration_id,))
        row = cursor.fetchone()
        if row:
            if row[0] != checksum:
                raise RuntimeError(f"RIV-DB-0006: Applied migration {migration_id} checksum differs from source.")
            return False
        cursor.execute(sql)
        cursor.execute(
            "INSERT INTO schema_migrations (migration_id, version, checksum_sha256) VALUES (%s, %s, %s)",
            (migration_id, version, checksum),
        )
    return True