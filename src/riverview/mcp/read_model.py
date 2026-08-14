"""Bounded PostgreSQL read model for RV-004.4 and RV-008.1.

Version: 0.10.0
"""

from __future__ import annotations

from typing import Any

from riverview.database import connect

MAX_PAGE_SIZE = 200
ALLOWED_RESOURCE_CLASSIFICATIONS = frozenset(("river", "internal"))


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
                "SELECT event_id,checkpoint_id,component,severity,failure_class,summary,evidence_refs AS evidence,recovery_state,occurred_at FROM diagnostic_events ORDER BY occurred_at DESC LIMIT %s",
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

    @staticmethod
    def _resource_args(limit: int, cursor: int, classification: str) -> tuple[int, int, str]:
        bounded_limit = max(1, min(int(limit), MAX_PAGE_SIZE))
        bounded_cursor = max(0, int(cursor))
        if classification not in ALLOWED_RESOURCE_CLASSIFICATIONS:
            raise ValueError("RIV-SEC-0001: resource classification is not permitted.")
        return bounded_limit, bounded_cursor, classification

    def _page(
        self, query: str, values: tuple[Any, ...], limit: int, cursor: int, classification: str
    ) -> dict[str, Any]:
        bounded_limit, bounded_cursor, bounded_classification = self._resource_args(
            limit, cursor, classification
        )
        with connect() as connection, connection.cursor() as db_cursor:
            db_cursor.execute(
                query, values + (bounded_classification, bounded_limit + 1, bounded_cursor)
            )
            rows = self._rows(db_cursor)
        has_more = len(rows) > bounded_limit
        items = rows[:bounded_limit]
        return {
            "authority": "read_only",
            "classification": bounded_classification,
            "items": items,
            "next_cursor": bounded_cursor + bounded_limit if has_more else None,
            "limit": bounded_limit,
        }

    def resource_roadmap(
        self, limit: int = 50, cursor: int = 0, classification: str = "river"
    ) -> dict[str, Any]:
        return self._page(
            """SELECT waypoint_id,parent_waypoint_id,sort_order,title,description,status,
                steward_checkpoint,acceptance_criteria,depends_on,scope_boundary,roadmap_revision,
                completed_at,updated_at,'river' AS classification FROM roadmap_items
                WHERE 'river'=%s ORDER BY sort_order,waypoint_id LIMIT %s OFFSET %s""",
            (),
            limit,
            cursor,
            classification,
        )

    def resource_work(
        self, limit: int = 50, cursor: int = 0, classification: str = "river"
    ) -> dict[str, Any]:
        return self._page(
            """SELECT work_order_id,action_type,action_version,status,requested_by,correlation_id,
                error_checkpoint,created_at,started_at,finished_at,'river' AS classification FROM work_orders
                WHERE 'river'=%s ORDER BY created_at DESC,work_order_id LIMIT %s OFFSET %s""",
            (),
            limit,
            cursor,
            classification,
        )

    def resource_reports(
        self, limit: int = 50, cursor: int = 0, classification: str = "river"
    ) -> dict[str, Any]:
        return self._page(
            """SELECT work_order_id,action_type,status,result_report,correlation_id,finished_at,
                'river' AS classification FROM work_orders
                WHERE status='succeeded' AND result_report IS NOT NULL AND 'river'=%s
                ORDER BY finished_at DESC,work_order_id LIMIT %s OFFSET %s""",
            (),
            limit,
            cursor,
            classification,
        )

    def resource_diagnostics(
        self, limit: int = 50, cursor: int = 0, classification: str = "river"
    ) -> dict[str, Any]:
        return self._page(
            """SELECT event_id,checkpoint_id,component,severity,failure_class,summary,evidence_refs AS evidence,
                recovery_state,occurred_at,'river' AS classification FROM diagnostic_events
                WHERE 'river'=%s ORDER BY occurred_at DESC,event_id LIMIT %s OFFSET %s""",
            (),
            limit,
            cursor,
            classification,
        )

    def resource_cookbook(
        self, limit: int = 50, cursor: int = 0, classification: str = "river"
    ) -> dict[str, Any]:
        return self._page(
            """SELECT checkpoint_id,component,failure_classes,diagnostic_procedure,repair_procedure,
                verification_procedure,applicability,validation_state,validated_at,updated_at,
                'river' AS classification FROM cookbook_entries
                WHERE 'river'=%s ORDER BY checkpoint_id LIMIT %s OFFSET %s""",
            (),
            limit,
            cursor,
            classification,
        )

    def resource_capacity(
        self, limit: int = 50, cursor: int = 0, classification: str = "river"
    ) -> dict[str, Any]:
        return self._page(
            """SELECT worker_id,state,host_name,process_id,last_seen_at,last_notification_at,
                completed_orders,failed_orders,'river' AS classification FROM relay_workers
                WHERE 'river'=%s ORDER BY last_seen_at DESC,worker_id LIMIT %s OFFSET %s""",
            (),
            limit,
            cursor,
            classification,
        )
