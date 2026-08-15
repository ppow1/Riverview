"""Hash/provenance-only inventory; originals remain immutable outside source control."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from riverview.database import connect


@dataclass(frozen=True, slots=True)
class ExportRecord:
    export_id: UUID
    source_path: str
    content_sha256: str
    byte_size: int
    source_kind: str
    classification: str
    provenance: dict[str, str]


def inventory_file(path: Path, *, source_kind: str, classification: str, provenance: dict[str, str]) -> ExportRecord:
    if not path.is_file() or not path.is_absolute():
        raise ValueError("RIV-KNW-0001: source export must be an existing absolute file.")
    if classification not in {"public", "operational", "private", "sensitive"}:
        raise ValueError("RIV-SEC-0001: export classification is closed.")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return ExportRecord(uuid4(), str(path), digest, path.stat().st_size, source_kind, classification, dict(provenance))


class KnowledgeExportStore:
    def persist(self, record: ExportRecord) -> UUID:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO knowledge_exports(export_id,source_path,content_sha256,byte_size,source_kind,classification,provenance,status)
                   VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,'inventoried')
                   ON CONFLICT(source_path,content_sha256) DO NOTHING""",
                (record.export_id, record.source_path, record.content_sha256, record.byte_size, record.source_kind,
                 record.classification, json.dumps(record.provenance)),
            )
            cursor.execute("SELECT export_id FROM knowledge_exports WHERE source_path=%s AND content_sha256=%s", (record.source_path, record.content_sha256))
            return cursor.fetchone()[0]
