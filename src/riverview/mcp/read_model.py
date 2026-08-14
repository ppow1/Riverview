"""Bounded PostgreSQL read model for RV-004.4.

Version: 0.9.14
"""

from __future__ import annotations

from typing import Any

from riverview.database import connect


class ReadOnlyRelay:
    """Expose only fixed, bounded read queries. Caller-supplied SQL is never accepted."""

    @staticmethod
    def _rows(cursor: Any) -> list[dict[str, Any]]:
        names = [column.name for column in cursor.description]
        return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]

    def roadmap_revision(self) -> dict[str, Any] | None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT revision_id,content_sha256,waypoint_count,source_path,applied_at "
                "FROM roadmap_revisions ORDER BY applied_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row is None:
                return None
            names = [column.name for column in cursor.description]
            return dict(zip(names, row, strict=True))

    def waypoints(self, limit: int = 200) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT waypoint_id,parent_waypoint_id,sort_order,title,description,status,"
                "steward_checkpoint,acceptance_criteria,depends_on,governing_refs,scope_boundary,"
                "roadmap_revision,completed_at,updated_at FROM roadmap_items "
                "ORDER BY COALESCE(parent_waypoint_id,waypoint_id),sort_order LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)

    def current_position(self) -> dict[str, Any]:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT waypoint_id,title,status,steward_checkpoint,depends_on,scope_boundary,"
                "roadmap_revision FROM roadmap_items WHERE status IN ('active','pending','blocked') "
                "ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'pending' THEN 1 ELSE 2 END,"
                "COALESCE(parent_waypoint_id,waypoint_id),sort_order LIMIT 25"
            )
            return {"authority": "read_only", "items": self._rows(cursor)}

    def workers(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 50))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT worker_id,state,host_name,process_id,last_seen_at,last_notification_at,"
                "completed_orders,failed_orders FROM relay_workers ORDER BY last_seen_at DESC LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)

    def work_orders(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 50))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT work_order_id,action_type,action_version,status,requested_by,correlation_id,"
                "error_checkpoint,created_at,started_at,finished_at FROM work_orders "
                "ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)

    def completed_reports(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 50))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT work_order_id,action_type,status,result_report,correlation_id,finished_at "
                "FROM work_orders WHERE status='succeeded' AND result_report IS NOT NULL "
                "ORDER BY finished_at DESC LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)

    def escalations(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 50))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT escalation_id,work_order_id,checkpoint_id,reason,state,evidence_refs,"
                "created_at,acknowledged_at,resolved_at FROM steward_escalations "
                "WHERE state IN('open','acknowledged') ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)

    def diagnostics(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 100))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                'SELECT event_id,checkpoint_id,component,severity,failure_class,summary,evidence_refs AS evidence,recovery_state,occurred_at FROM diagnostic_events ORDER BY occurred_at DESC LIMIT %s',
                (limit,),
            )
            return self._rows(cursor)

    def cookbook(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 100))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    checkpoint_id,
                    applicability->>'title' AS title,
                    applicability->>'summary' AS summary,
                    failure_classes,
                    diagnostic_procedure AS distinguishing_probes,
                    repair_procedure,
                    verification_procedure,
                    applicability->>'source_path' AS source_path,
                    applicability, validation_state, validated_at, updated_at
                FROM cookbook_entries
                ORDER BY checkpoint_id
                LIMIT %s
                """,
                (limit,),
            )
            return self._rows(cursor)