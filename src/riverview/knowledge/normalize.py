"""Normalize approved message-shaped exports without guessing attribution."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from riverview.database import connect


def normalize_message_export(path: Path, *, source_export_id: UUID, classification: str = "operational") -> tuple[UUID, int]:
    if classification not in {"public", "operational", "private", "sensitive"}:
        raise ValueError("RIV-SEC-0001: normalized export classification is closed.")
    messages = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(messages, list) or not messages:
        raise ValueError("RIV-KNW-0002: message export is not a bounded non-empty list.")
    ordered = sorted(messages, key=lambda item: item.get("createdAtUtc", item.get("created_at_utc", "")))
    conversation_id = uuid4()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("""INSERT INTO knowledge_conversations(conversation_id,source_export_id,source_ref,classification,provenance)
                        VALUES(%s,%s,%s,%s,%s::jsonb) ON CONFLICT(source_export_id) DO NOTHING""",
                       (conversation_id, source_export_id, str(path), classification, json.dumps({"normalizer":"rv-009.2-v1"})))
        cursor.execute("SELECT conversation_id FROM knowledge_conversations WHERE source_export_id=%s", (source_export_id,))
        conversation_id = cursor.fetchone()[0]
        for order, message in enumerate(ordered):
            source_id = str(message.get("messageId") or message.get("message_id") or f"ordinal-{order}")
            created = message.get("createdAtUtc") or message.get("created_at_utc")
            occurred = datetime.fromisoformat(created) if created else None
            speaker = str(message.get("createdBy") or message.get("from_lane") or "unknown")
            cursor.execute("""INSERT INTO knowledge_turns(turn_id,conversation_id,source_message_id,speaker,occurred_at,body,classification,provenance,uncertain_attribution,turn_order)
                            VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s) ON CONFLICT(conversation_id,source_message_id) DO NOTHING""",
                           (uuid4(), conversation_id, source_id, speaker, occurred, str(message.get("body", "")), classification,
                            json.dumps({"source_path":str(path),"source_message_id":source_id}), speaker == "unknown", order))
    return conversation_id, len(ordered)
