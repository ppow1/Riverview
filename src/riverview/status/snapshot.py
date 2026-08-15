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
        cursor.execute("""SELECT o.objective_id,o.objective_key,o.status,s.stage_key,s.readiness,
                                 s.steward_checkpoint,o.correlation_id
                          FROM objectives o JOIN objective_stages s ON s.objective_id=o.objective_id
                          WHERE o.status IN ('ready','active') AND s.status<>'completed'
                          ORDER BY o.updated_at DESC LIMIT 32""")
        active_objectives = _rows(cursor)
        cursor.execute("""SELECT c.capability_name,c.provider_id,c.health_status,cc.available,
                                 cc.concurrency_limit,cc.current_load,cc.backoff_until,cc.observed_at
                          FROM capabilities c LEFT JOIN capability_capacity cc ON cc.capability_id=c.capability_id
                          ORDER BY c.capability_name LIMIT 32""")
        capacity = _rows(cursor)
        cursor.execute("SELECT lane_id,lane_key,owner_id,allowed_paths,state,correlation_id FROM execution_lanes WHERE state='active' ORDER BY created_at LIMIT 32")
        lanes = _rows(cursor)
        cursor.execute("SELECT binding_id,role,application_ref,contract_version,conversation_id,status,verification_state,consumer_id FROM comms_bindings ORDER BY updated_at DESC LIMIT 16")
        bindings = _rows(cursor)
        cursor.execute("SELECT recovery_id,request_id,correlation_id,operation,state,failure_class,attempt_count,max_attempts,escalation_id,updated_at FROM bridge_recovery_attempts ORDER BY updated_at DESC LIMIT 16")
        recoveries = _rows(cursor)
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
        "active_objectives": active_objectives,
        "capacity": capacity,
        "lanes": lanes,
        "comms_bindings": bindings,
        "bridge_recoveries": recoveries,
        "migrations": migrations,
    }
