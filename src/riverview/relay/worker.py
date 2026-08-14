"""Persistent LISTEN/NOTIFY worker for Riverview Relay.

Version: 0.6.1
"""

from __future__ import annotations

import os
import socket
import threading
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any

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
        self.poll_seconds = poll_seconds
        self.runner = RestrictedRunner(self.repository, worker_id)
        self.statistics = WorkerStatistics()

    def _record(self, state: str, work_order_id: Any = None) -> None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO relay_workers(worker_id,state,process_id,host_name,last_work_order_id)
                   VALUES(%s,%s,%s,%s,%s)
                   ON CONFLICT(worker_id) DO UPDATE SET state=EXCLUDED.state,process_id=EXCLUDED.process_id,
                   host_name=EXCLUDED.host_name,last_seen_at=now(),last_work_order_id=COALESCE(EXCLUDED.last_work_order_id,relay_workers.last_work_order_id),updated_at=now()""",
                (self.worker_id, state, os.getpid(), socket.gethostname(), work_order_id),
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

    def drain(self, limit: int = 25) -> int:
        processed = 0
        while processed < limit:
            self._record("running")
            result = self.runner.run_once()
            if result is None:
                self._record("idle")
                break
            self._record_result(result)
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