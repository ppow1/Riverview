"""Durable Operator history projection; never stores accepted resident canon."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect


class OperatorProjection:
    def __init__(self) -> None:
        self.available = True
        self.memory: dict[UUID, dict[str, Any]] = {}
        try:
            with connect() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM operator_conversations LIMIT 1")
        except (RuntimeError, OSError, ValueError):
            self.available = False

    def list(self) -> list[dict[str, Any]]:
        if not self.available:
            return list(self.memory.values())
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""SELECT conversation_id,resident_id,room_id,kind,title,classification FROM operator_conversations
                             WHERE archived_at IS NULL ORDER BY updated_at DESC""")
            rows = cursor.fetchall()
            return [self._conversation(cursor, row) for row in rows]

    def _conversation(self, cursor: Any, row: Any) -> dict[str, Any]:
        conversation_id, resident_id, room_id, kind, title, classification = row
        cursor.execute("""SELECT role,speaker_id,speaker_name,body,metadata FROM operator_messages
                         WHERE conversation_id=%s ORDER BY turn_order""", (conversation_id,))
        messages = [{"role": r[0], "speaker_id": r[1], "speaker": r[2], "text": r[3], "details": r[4]} for r in cursor.fetchall()]
        return {"id": str(conversation_id), "resident_id": resident_id or "", "resident_name": "", "room_id": str(room_id) if room_id else "", "kind": kind, "title": title, "classification": classification, "messages": messages, "preview": messages[-1]["text"][:180] if messages else "", "unread": False}

    def create(self, *, resident_id: str, title: str, kind: str = "conversation", room_id: UUID | None = None, classification: str = "operational") -> dict[str, Any]:
        conversation_id = uuid4()
        value = {"id": str(conversation_id), "resident_id": resident_id, "resident_name": "", "room_id": str(room_id) if room_id else "", "kind": kind, "title": title[:160], "classification": classification, "messages": [], "preview": "", "unread": False}
        if not self.available:
            self.memory[conversation_id] = value
            return value
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""INSERT INTO operator_conversations(conversation_id,resident_id,room_id,kind,title,classification)
                             VALUES(%s,%s,%s,%s,%s,%s)""", (conversation_id, resident_id or None, room_id, kind, title[:160], classification))
        return value

    def append(self, conversation_id: UUID, *, role: str, text: str, speaker_id: str | None, speaker: str, details: dict[str, Any]) -> None:
        if not self.available:
            item = self.memory[conversation_id]
            item["messages"].append({"role": role, "speaker_id": speaker_id, "speaker": speaker, "text": text, "details": details})
            item["preview"] = text[:180]
            return
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(turn_order),-1)+1 FROM operator_messages WHERE conversation_id=%s", (conversation_id,))
            order = cursor.fetchone()[0]
            cursor.execute("""INSERT INTO operator_messages(message_id,conversation_id,turn_order,role,speaker_id,speaker_name,body,metadata)
                             VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""", (uuid4(), conversation_id, order, role, speaker_id, speaker, text, json.dumps(details, default=str)))
            cursor.execute("UPDATE operator_conversations SET updated_at=now() WHERE conversation_id=%s", (conversation_id,))

    def refresh(self, conversation_id: UUID) -> dict[str, Any] | None:
        if not self.available:
            return self.memory.get(conversation_id)
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT conversation_id,resident_id,room_id,kind,title,classification FROM operator_conversations WHERE conversation_id=%s AND archived_at IS NULL", (conversation_id,))
            row = cursor.fetchone()
            return self._conversation(cursor, row) if row else None
