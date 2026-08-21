"""Bounded read projection for meaningful Riverview activity."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from riverview.database import connect


_ACCENTS = ("cyan", "violet", "amber", "teal", "rose", "lime", "blue", "orange")


def _work_title(instruction: str | None, objective_title: str | None, stage_title: str | None) -> str:
    value = " ".join(str(instruction or "").split()).lower()
    if "spatial test room 001" in value:
        return "SPATIAL TEST ROOM 001"
    if "human-readable persistent work-package identity" in value:
        return "READABLE OPERATOR ACTIVITY"
    for candidate in (objective_title, stage_title):
        cleaned = " ".join(str(candidate or "").split())
        if cleaned and cleaned.casefold() != "steward seed draft":
            return cleaned[:120]
    return "ENGINEERING WORK PACKAGE"


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

            correlations = list({row["correlation_id"] for row in rows if row["correlation_id"]})
            lineage: dict[str, dict[str, Any]] = {}
            if correlations:
                db.execute(
                    """SELECT w.work_order_id,w.correlation_id,w.status,w.action_type,w.started_at,w.finished_at,
                              w.last_heartbeat_at,w.result_report,w.error_checkpoint,o.title,s.title,i.bounded_instruction,
                              cap.provider_id,e.status,a.worker_id
                       FROM work_orders w
                       LEFT JOIN objectives o ON o.correlation_id=w.correlation_id
                       LEFT JOIN objective_stages s ON s.objective_id=o.objective_id
                       LEFT JOIN engineering_intents i ON i.objective_id=o.objective_id
                       LEFT JOIN execution_envelopes e ON e.work_order_id=w.work_order_id
                       LEFT JOIN capabilities cap ON cap.capability_name=e.capability_name
                       LEFT JOIN LATERAL (
                           SELECT worker_id FROM work_order_attempts
                           WHERE work_order_id=w.work_order_id ORDER BY attempt DESC LIMIT 1
                       ) a ON TRUE
                       WHERE w.correlation_id = ANY(%s)
                       ORDER BY w.created_at DESC""",
                    (correlations,),
                )
                for item in db.fetchall():
                    key = str(item[1])
                    if key not in lineage:
                        lineage[key] = {
                            "work_order_id": str(item[0]), "correlation_id": key, "status": str(item[2]),
                            "action_type": str(item[3]), "started_at": item[4], "finished_at": item[5],
                            "last_heartbeat_at": item[6], "result_report": item[7] if isinstance(item[7], dict) else {},
                            "error_checkpoint": item[8], "objective_title": item[9], "stage_title": item[10],
                            "instruction": item[11], "provider_id": item[12], "execution_status": item[13],
                            "worker_id": item[14],
                        }

        items: list[dict[str, Any]] = []
        for row in rows:
            event_category = _category(str(row["event_type"]), str(row["aggregate_type"]))
            if category and category != event_category:
                continue
            payload = row["payload"] if isinstance(row["payload"], dict) else {}
            context = lineage.get(str(row["correlation_id"]), {})
            title = _work_title(context.get("instruction"), context.get("objective_title"), context.get("stage_title")) if context else ""
            base_summary = _summary(str(row["event_type"]), str(row["aggregate_type"]), payload)
            summary = f"{title} · {base_summary}" if title else base_summary
            status = str(context.get("status", payload.get("state") or payload.get("status") or "observed"))
            heartbeat = context.get("last_heartbeat_at")
            now = datetime.now(UTC)
            heartbeat_age = max(0, int((now - heartbeat).total_seconds())) if isinstance(heartbeat, datetime) else None
            if status in {"succeeded", "reconciled"}:
                liveness = "COMPLETED"
            elif status in {"failed", "timed_out"}:
                liveness = "FAILED"
            elif status == "queued":
                liveness = "WAITING"
            elif status in {"claimed", "running"}:
                liveness = "STALLED" if heartbeat_age is not None and heartbeat_age > 300 else "ACTIVE"
            else:
                liveness = str(payload.get("liveness_state") or "WAITING")
            report = context.get("result_report") or {}
            started = context.get("started_at")
            ended = context.get("finished_at") or now
            elapsed = max(0, int((ended - started).total_seconds())) if isinstance(started, datetime) and isinstance(ended, datetime) else None
            phase = str(report.get("phase") or ("queued" if status == "queued" else "testing" if status in {"claimed", "running"} else status))
            progress = report.get("progress_percent")
            if not isinstance(progress, int):
                progress = {"queued": 0, "claimed": 25, "running": 50, "failed": 100, "timed_out": 100, "succeeded": 100, "reconciled": 100}.get(status)
            detail = _bounded_details(payload)
            if context:
                detail.update({
                    "work_order_id": context["work_order_id"], "work_package_title": title,
                    "executor_provider": context.get("provider_id") or "codex-cli-local",
                    "codex_worker": context.get("worker_id"), "phase": phase,
                    "last_concrete_activity": report.get("last_activity") or base_summary,
                    "last_progress_at": _iso(heartbeat), "elapsed_seconds": elapsed,
                    "heartbeat_age_seconds": heartbeat_age, "blocked": liveness == "WAITING",
                    "estimated_progress_percent": progress, "liveness_state": liveness,
                    "accent_identity": _ACCENTS[int(hashlib.sha256(str(row["correlation_id"]).encode()).hexdigest()[:8], 16) % len(_ACCENTS)],
                })
            items.append(
                {
                    "activity_id": int(row["sequence_id"]),
                    "event_id": str(row["event_id"]),
                    "river_sequence": int(row["sequence_id"]),
                    "occurred_at": _iso(row["occurred_at"]),
                    "category": event_category,
                    "event_type": row["event_type"],
                    "summary": summary,
                    "state": liveness if context else payload.get("state") or payload.get("status") or "observed",
                    "source": row["aggregate_type"],
                    "correlation_id": str(row["correlation_id"]) if row["correlation_id"] else None,
                    "causation_id": str(row["causation_id"]) if row["causation_id"] else None,
                    "aggregate_id": str(row["aggregate_id"]),
                    "checkpoint": payload.get("checkpoint") or payload.get("checkpoint_id"),
                    "attention_required": bool(payload.get("steward_attention_required") or payload.get("attention_required")),
                    "severity": payload.get("severity") or "info",
                    "details": detail,
                }
            )
        return {"items": items, "next_cursor": latest, "has_more": len(rows) >= bounded_limit}
