"""Persistent LISTEN/NOTIFY worker for Riverview Relay.

Version: 0.6.1
"""

from __future__ import annotations

import json
import os
import signal
import socket
import threading
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any
from uuid import UUID, uuid4

import psycopg

from riverview.database import connect
from riverview.database.connection import load_database_config
from riverview.runner import RestrictedRunner


@dataclass(slots=True)
class WorkerStatistics:
    cycles: int = 0
    notifications: int = 0
    completed: int = 0
    failed: int = 0


class RelayWorker:
    """Wake on PostgreSQL notifications and recover with bounded polling."""

    def __init__(self, repository: Path, worker_id: str, poll_seconds: float = 5.0) -> None:
        if poll_seconds <= 0:
            raise ValueError("RIV-WRK-0005: poll_seconds must be positive.")
        self.repository = repository.resolve()
        self.worker_id = worker_id
        self.worker_instance_id = uuid4()
        self.seat_id = "C1"
        self.supported_roles = ("writer",)
        self.poll_seconds = poll_seconds
        self.runner = RestrictedRunner(self.repository, worker_id)
        self.runner.worker_instance_id = self.worker_instance_id
        self.statistics = WorkerStatistics()
        self.progress_interval_seconds = 120.0
        self._last_progress_at = 0.0

    def _record(self, state: str, work_order_id: Any = None) -> None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO relay_workers(worker_id,worker_instance_id,seat_id,supported_roles,
                   state,process_id,host_name,last_work_order_id)
                   VALUES(%s,%s,%s,%s::jsonb,%s,%s,%s,%s)
                   ON CONFLICT(worker_id) DO UPDATE SET state=EXCLUDED.state,process_id=EXCLUDED.process_id,
                   worker_instance_id=EXCLUDED.worker_instance_id,seat_id=EXCLUDED.seat_id,
                   supported_roles=EXCLUDED.supported_roles,host_name=EXCLUDED.host_name,
                   last_seen_at=now(),stale=false,
                   last_work_order_id=COALESCE(EXCLUDED.last_work_order_id,relay_workers.last_work_order_id),
                   updated_at=now()""",
                (self.worker_id, self.worker_instance_id, self.seat_id,
                 json.dumps(list(self.supported_roles)), state, os.getpid(), socket.gethostname(), work_order_id),
            )

    def _record_notification(self) -> None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE relay_workers SET last_notification_at=now(),last_seen_at=now(),updated_at=now() WHERE worker_id=%s",(self.worker_id,))

    def _record_result(self, result: dict[str, Any]) -> None:
        succeeded = result.get("status") == "succeeded"
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE relay_workers SET state='idle',last_seen_at=now(),completed_orders=completed_orders+%s,failed_orders=failed_orders+%s,updated_at=now() WHERE worker_id=%s",(1 if succeeded else 0,0 if succeeded else 1,self.worker_id))
        if succeeded:
            self.statistics.completed += 1
        else:
            self.statistics.failed += 1

    def _next_closed_loop_work_order(self) -> UUID | None:
        """Select only an exact executable root-bound order for internal actions."""
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""SELECT w.work_order_id
                               FROM work_orders w
                               JOIN autonomous_governance_bindings b
                                 ON b.work_order_id=w.work_order_id
                                AND b.root_task_id=CASE WHEN w.parameters->>'root_task_id' ~ '^[0-9a-fA-F-]{36}$' THEN (w.parameters->>'root_task_id')::uuid ELSE NULL END
                                AND b.correlation_id=w.correlation_id
                                AND b.objective_id=w.objective_id
                                AND b.stage_id=w.stage_id
                              WHERE w.status='queued' AND w.active_attempt_id IS NULL
                                AND w.parameters ? 'root_task_id'
                                AND w.parameters->>'root_task_id' ~ '^[0-9a-fA-F-]{36}$'
                                AND b.state='EXECUTABLE'
                              ORDER BY w.created_at
                              LIMIT 1""")
            row = cursor.fetchone()
        return UUID(str(row[0])) if row else None

    def drain(self, limit: int = 25) -> int:
        processed = 0
        while processed < limit:
            self._record("running")
            target = self._next_closed_loop_work_order()
            result = self.runner.run_once(target_work_order_id=target) if target is not None else self.runner.run_once()
            if result is None:
                self._record("idle")
                break
            self._record_result(result)
            self._last_progress_at = monotonic()
            processed += 1
        return processed

    def serve(self, stop: threading.Event, ready: threading.Event | None = None) -> WorkerStatistics:
        config = load_database_config()
        self._record("starting")
        try:
            with psycopg.connect(host=config.host,port=config.port,dbname=config.database,user=config.user,password=config.password,autocommit=True) as listener:
                listener.execute("LISTEN riverview_work_orders")
                self._record("idle")
                self.drain()
                if ready is not None:
                    ready.set()
                while not stop.is_set():
                    self.statistics.cycles += 1
                    began = monotonic()
                    notification = next(listener.notifies(timeout=self.poll_seconds, stop_after=1), None)
                    if notification is not None:
                        self.statistics.notifications += 1
                        self._record_notification()
                    self.drain()
                    remaining = self.poll_seconds - (monotonic() - began)
                    if notification is None and remaining > 0:
                        stop.wait(min(remaining, self.poll_seconds))
        except (OSError, RuntimeError, psycopg.Error) as exc:
            self._record("failed")
            raise RuntimeError(f"RIV-WRK-0006: Relay worker failed: {exc}") from exc
        finally:
            if ready is not None:
                ready.set()
            self._record("stopped")
        return self.statistics


def main() -> None:
    """Run the durable Relay consumer under the repository-owned lifecycle."""
    stop = threading.Event()

    def shutdown(_signum: int, _frame: object) -> None:
        stop.set()

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)
    RelayWorker(Path.cwd(), "relay.primary", poll_seconds=1.0).serve(stop)


if __name__ == "__main__":
    main()
