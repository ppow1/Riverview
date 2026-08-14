"""PostgreSQL projection for the Steward status surface.

Version: 0.7.1
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from riverview.database import connect


def _rows(cursor: Any) -> list[dict[str, Any]]:
    names = [column.name for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def status_snapshot() -> dict[str, Any]:
    """Return one bounded, read-only operational projection."""

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """SELECT
                   i.waypoint_id,
                   i.parent_waypoint_id,
                   i.sort_order,
                   i.title,
                   i.status,
                   i.steward_checkpoint,
                   COALESCE(
                       t.occurred_at,
                       CASE WHEN i.status='completed' THEN i.completed_at END
                   ) AS status_changed_at
               FROM roadmap_items i
               LEFT JOIN LATERAL (
                   SELECT rt.occurred_at
                   FROM roadmap_transitions rt
                   WHERE rt.waypoint_id=i.waypoint_id
                   ORDER BY rt.occurred_at DESC
                   LIMIT 1
               ) t ON TRUE
               ORDER BY COALESCE(i.parent_waypoint_id,i.waypoint_id),i.sort_order"""
        )
        roadmap = _rows(cursor)
        cursor.execute("SELECT worker_id,state,host_name,process_id,last_seen_at,last_notification_at,completed_orders,failed_orders FROM relay_workers ORDER BY last_seen_at DESC LIMIT 20")
        workers = _rows(cursor)
        cursor.execute("SELECT status,count(*) AS count FROM work_orders GROUP BY status ORDER BY status")
        work_counts = _rows(cursor)
        cursor.execute("SELECT work_order_id,action_type,status,requested_by,error_checkpoint,created_at,finished_at FROM work_orders ORDER BY created_at DESC LIMIT 20")
        recent_work = _rows(cursor)
        cursor.execute("SELECT escalation_id,work_order_id,checkpoint_id,reason,state,created_at FROM steward_escalations WHERE state IN('open','acknowledged') ORDER BY created_at DESC LIMIT 20")
        escalations = _rows(cursor)
        cursor.execute("SELECT event_id,checkpoint_id,component,severity,failure_class,summary,recovery_state,occurred_at FROM diagnostic_events ORDER BY occurred_at DESC LIMIT 20")
        diagnostics = _rows(cursor)
        cursor.execute("SELECT migration_id,version,applied_at FROM schema_migrations ORDER BY migration_id")
        migrations = _rows(cursor)
    return {
        "generated_at": datetime.now(UTC),
        "status": "healthy",
        "authority": "read_only",
        "roadmap": roadmap,
        "workers": workers,
        "work_counts": work_counts,
        "recent_work": recent_work,
        "escalations": escalations,
        "diagnostics": diagnostics,
        "migrations": migrations,
    }