"""Bounded read projection for meaningful Riverview activity."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from riverview.database import connect


def _category(event_type: str, aggregate_type: str) -> str:
    value = f"{event_type} {aggregate_type}".lower()
    if any(token in value for token in ("comms", "mcp", "seed", "specification")):
        return "comms"
    if "grace" in value or "evaluation" in value:
        return "grace"
    if "cme" in value or "momentum" in value:
        return "cme"
    if "objective" in value or "stage" in value:
        return "objectives"
    if "work" in value or "execution" in value or "relay" in value:
        return "work"
    if "notification" in value or "attention" in value:
        return "notifications"
    return "river"


def _summary(event_type: str, aggregate_type: str, payload: dict[str, Any]) -> str:
    supplied = str(payload.get("summary") or payload.get("description") or "").strip()
    if supplied:
        return supplied[:240]
    membership_labels = {
        "room.participant.added": "Room participant added",
        "room.participant.removed": "Room participant removed",
        "room.administrator.granted": "Room Administrator granted",
        "room.administrator.revoked": "Room Administrator revoked",
        "room.administrator.left": "Room Administrator left",
        "room.renamed": "Room renamed",
        "room.derived": "Room derived from conversation",
    }
    if event_type in membership_labels:
        target = payload.get("resident_id") or payload.get("administrator_id")
        return f"{membership_labels[event_type]}{': ' + str(target) if target else ''}"[:240]
    words = event_type.replace(".", " ").replace("_", " ").strip()
    return f"{words[:1].upper() + words[1:]} ({aggregate_type})"[:240]


def _iso(value: Any) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else str(value) if value is not None else None


def _bounded_details(payload: dict[str, Any]) -> dict[str, Any]:
    blocked = {"token", "authorization", "credential", "secret", "password", "raw_audio", "content_bytes", "protected_payload"}
    result: dict[str, Any] = {}
    for key, value in payload.items():
        if key.casefold() in blocked or any(part in key.casefold() for part in ("secret", "credential", "authorization")):
            continue
        if isinstance(value, str):
            result[key] = value[:500]
        elif isinstance(value, (int, float, bool)) or value is None:
            result[key] = value
        else:
            result[key] = str(value)[:500]
    return result


class ActivityProjection:
    """Read-only projection over River's durable event sequence."""

    def list(self, *, after: int = 0, limit: int = 50, category: str = "") -> dict[str, Any]:
        bounded_limit = max(1, min(int(limit), 100))
        cursor = max(0, int(after))
        with connect() as connection, connection.cursor() as db:
            order = "DESC" if cursor == 0 else "ASC"
            db.execute(
                f"""SELECT sequence_id,event_id,event_type,aggregate_type,aggregate_id,
                           correlation_id,causation_id,classification,payload,occurred_at
                    FROM river_events
                    WHERE sequence_id > %s
                    ORDER BY sequence_id {order}
                    LIMIT %s""",
                (cursor, bounded_limit),
            )
            names = [item.name for item in db.description]
            rows = [dict(zip(names, row, strict=True)) for row in db.fetchall()]
            if cursor == 0:
                rows.reverse()
            db.execute("SELECT COALESCE(MAX(sequence_id), %s) FROM river_events", (cursor,))
            latest = int(db.fetchone()[0])

        items: list[dict[str, Any]] = []
        for row in rows:
            event_category = _category(str(row["event_type"]), str(row["aggregate_type"]))
            if category and category != event_category:
                continue
            payload = row["payload"] if isinstance(row["payload"], dict) else {}
            items.append(
                {
                    "activity_id": int(row["sequence_id"]),
                    "event_id": str(row["event_id"]),
                    "river_sequence": int(row["sequence_id"]),
                    "occurred_at": _iso(row["occurred_at"]),
                    "category": event_category,
                    "event_type": row["event_type"],
                    "summary": _summary(str(row["event_type"]), str(row["aggregate_type"]), payload),
                    "state": payload.get("state") or payload.get("status") or "observed",
                    "source": row["aggregate_type"],
                    "correlation_id": str(row["correlation_id"]) if row["correlation_id"] else None,
                    "causation_id": str(row["causation_id"]) if row["causation_id"] else None,
                    "aggregate_id": str(row["aggregate_id"]),
                    "checkpoint": payload.get("checkpoint") or payload.get("checkpoint_id"),
                    "attention_required": bool(payload.get("steward_attention_required") or payload.get("attention_required")),
                    "severity": payload.get("severity") or "info",
                    "details": _bounded_details(payload),
                }
            )
        return {"items": items, "next_cursor": latest, "has_more": len(rows) >= bounded_limit}
