"""Durable Operator history projection; never stores accepted resident canon."""
from __future__ import annotations

import json
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

    def list(self, *, include_archived: bool = False) -> list[dict[str, Any]]:
        if not self.available:
            return list(self.memory.values())
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""SELECT conversation_id,resident_id,room_id,kind,title,classification,archived_at,source_conversation_id,inherited_context_window,inherited_message_count,participants_added FROM operator_conversations
                             WHERE (%s OR archived_at IS NULL) ORDER BY updated_at DESC""", (include_archived,))
            rows = cursor.fetchall()
            return [self._conversation(cursor, row) for row in rows]

    def list_summaries(self, *, include_archived: bool = False, limit: int = 24, offset: int = 0) -> dict[str, Any]:
        """Return a bounded conversation window without hydrating message bodies."""
        bounded_limit = max(1, min(int(limit), 50))
        bounded_offset = max(0, int(offset))
        if not self.available:
            values = [self._summary(item) for item in self.memory.values() if include_archived or not item.get("archived")]
            page = values[bounded_offset:bounded_offset + bounded_limit]
            return {"conversations": page, "offset": bounded_offset, "limit": bounded_limit, "has_more": len(values) > bounded_offset + len(page)}
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""SELECT conversation_id,resident_id,room_id,kind,title,classification,archived_at,
                                      source_conversation_id,inherited_context_window,inherited_message_count,participants_added
                               FROM operator_conversations
                               WHERE (%s OR archived_at IS NULL)
                               ORDER BY updated_at DESC LIMIT %s OFFSET %s""", (include_archived, bounded_limit + 1, bounded_offset))
            rows = cursor.fetchall()
        page = [self._summary_row(row) for row in rows[:bounded_limit]]
        return {"conversations": page, "offset": bounded_offset, "limit": bounded_limit, "has_more": len(rows) > bounded_limit}

    @staticmethod
    def _summary(value: dict[str, Any]) -> dict[str, Any]:
        messages = value.get("messages", [])
        return {key: value.get(key, "") for key in ("id", "resident_id", "resident_name", "room_id", "kind", "title", "classification", "archived", "unread", "source_conversation_id", "inherited_context_window", "inherited_message_count", "participants_added")} | {"preview": value.get("preview", messages[-1].get("text", "")[:180] if messages else ""), "message_count": len(messages), "messages": []}

    def _summary_row(self, row: Any) -> dict[str, Any]:
        conversation_id, resident_id, room_id, kind, title, classification, archived_at, source_id, context_window, inherited_count, participants_added = row
        return {"id": str(conversation_id), "resident_id": resident_id or "", "resident_name": "", "room_id": str(room_id) if room_id else "", "kind": kind, "title": title, "classification": classification, "messages": [], "preview": "", "unread": False, "archived": bool(archived_at), "source_conversation_id": str(source_id) if source_id else "", "inherited_context_window": context_window or "", "inherited_message_count": inherited_count or 0, "participants_added": participants_added or [], "message_count": 0}

    def search(self, query: str, *, limit: int = 25, include_archived: bool = True) -> list[dict[str, Any]]:
        """Search durable conversation/message bodies without loading history into the browser."""
        term = query.strip()
        if not term:
            return []
        bounded_limit = max(1, min(limit, 100))
        if not self.available:
            lowered = term.casefold()
            return [{"id": str(item["id"]), "title": item["title"], "resident_id": item.get("resident_id", ""), "room_id": item.get("room_id", ""), "kind": item.get("kind", "conversation"), "archived": bool(item.get("archived")), "snippet": message["text"][:240], "message_index": index, "occurred_at": "unavailable"} for item in self.memory.values() if include_archived or not item.get("archived") for index, message in enumerate(item.get("messages", ())) if lowered in message.get("text", "").casefold()][:bounded_limit]
        with connect() as connection, connection.cursor() as cursor:
            pattern = f"%{term}%"
            cursor.execute("""SELECT c.conversation_id,c.title,c.resident_id,c.room_id,c.kind,c.archived_at,m.body,m.occurred_at,m.turn_order
                             FROM operator_conversations c JOIN LATERAL (
                               SELECT body,occurred_at,turn_order FROM operator_messages
                               WHERE conversation_id=c.conversation_id AND body ILIKE %s
                               ORDER BY occurred_at DESC LIMIT 1
                             ) m ON TRUE
                             WHERE (%s OR c.archived_at IS NULL)
                             ORDER BY c.updated_at DESC LIMIT %s""", (pattern, include_archived, bounded_limit))
            return [{"id": str(row[0]), "title": row[1], "resident_id": row[2] or "", "room_id": str(row[3]) if row[3] else "", "kind": row[4], "archived": bool(row[5]), "snippet": row[6][:240], "occurred_at": row[7], "message_index": row[8]} for row in cursor.fetchall()]

    def _conversation(self, cursor: Any, row: Any) -> dict[str, Any]:
        conversation_id, resident_id, room_id, kind, title, classification, *extra = row
        cursor.execute("""SELECT role,speaker_id,speaker_name,body,metadata FROM operator_messages
                         WHERE conversation_id=%s ORDER BY turn_order""", (conversation_id,))
        messages = [{"role": r[0], "speaker_id": r[1], "speaker": r[2], "text": r[3], "details": r[4]} for r in cursor.fetchall()]
        archived_at, source_id, context_window, inherited_count, participants_added = (extra + [None] * 5)[:5]
        return {"id": str(conversation_id), "resident_id": resident_id or "", "resident_name": "", "room_id": str(room_id) if room_id else "", "kind": kind, "title": title, "classification": classification, "messages": messages, "preview": messages[-1]["text"][:180] if messages else "", "unread": False, "archived": bool(archived_at), "source_conversation_id": str(source_id) if source_id else "", "inherited_context_window": context_window or "", "inherited_message_count": inherited_count or 0, "participants_added": participants_added or []}

    def create(self, *, resident_id: str, title: str, kind: str = "conversation", room_id: UUID | None = None, classification: str = "operational", source_conversation_id: UUID | None = None, inherited_context_window: str = "", inherited_message_count: int = 0, participants_added: list[str] | None = None) -> dict[str, Any]:
        conversation_id = uuid4()
        value = {"id": str(conversation_id), "resident_id": resident_id, "resident_name": "", "room_id": str(room_id) if room_id else "", "kind": kind, "title": title[:160], "classification": classification, "messages": [], "preview": "", "unread": False, "source_conversation_id": str(source_conversation_id) if source_conversation_id else "", "inherited_context_window": inherited_context_window, "inherited_message_count": inherited_message_count, "participants_added": participants_added or []}
        if not self.available:
            self.memory[conversation_id] = value
            return value
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""INSERT INTO operator_conversations(conversation_id,resident_id,room_id,kind,title,classification,source_conversation_id,inherited_context_window,inherited_message_count,participants_added)
                             VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""", (conversation_id, resident_id or None, room_id, kind, title[:160], classification, source_conversation_id, inherited_context_window, inherited_message_count, json.dumps(participants_added or [])))
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

    def refresh(self, conversation_id: UUID, *, include_archived: bool = False) -> dict[str, Any] | None:
        if not self.available:
            return self.memory.get(conversation_id)
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT conversation_id,resident_id,room_id,kind,title,classification,archived_at,source_conversation_id,inherited_context_window,inherited_message_count,participants_added FROM operator_conversations WHERE conversation_id=%s AND (%s OR archived_at IS NULL)", (conversation_id, include_archived))
            row = cursor.fetchone()
            return self._conversation(cursor, row) if row else None

    def set_archived(self, conversation_id: UUID, archived: bool) -> dict[str, Any] | None:
        if not self.available:
            item = self.memory.get(conversation_id)
            if item is not None:
                item["archived"] = archived
            return item
        with connect() as connection, connection.cursor() as cursor:
            if archived:
                cursor.execute("UPDATE operator_conversations SET archived_at=now(),updated_at=now() WHERE conversation_id=%s", (conversation_id,))
            else:
                cursor.execute("UPDATE operator_conversations SET archived_at=NULL,updated_at=now() WHERE conversation_id=%s", (conversation_id,))
            if cursor.rowcount == 0:
                return None
            cursor.execute("SELECT conversation_id,resident_id,room_id,kind,title,classification,archived_at,source_conversation_id,inherited_context_window,inherited_message_count,participants_added FROM operator_conversations WHERE conversation_id=%s", (conversation_id,))
            return self._conversation(cursor, cursor.fetchone())

    def assign_resident(self, conversation_id: UUID, resident_id: str, title: str) -> dict[str, Any] | None:
        """Assign the initial resident exactly once on a neutral conversation."""
        if not resident_id.strip():
            return self.refresh(conversation_id)
        if not self.available:
            item = self.memory.get(conversation_id)
            if item is None or item.get("resident_id"):
                return None
            item["resident_id"] = resident_id
            item["title"] = title[:160]
            return item
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE operator_conversations SET resident_id=%s,title=%s,updated_at=now() WHERE conversation_id=%s AND resident_id IS NULL AND kind='conversation'", (resident_id, title[:160], conversation_id))
            if cursor.rowcount != 1:
                return None
        return self.refresh(conversation_id)
