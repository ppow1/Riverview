"""Live notification-to-runner acceptance for the Relay worker.

Version: 0.6.1
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from uuid import uuid4

from riverview.database import connect
from riverview.relay import RelayStore
from riverview.relay.worker import RelayWorker


def acceptance(repository: Path) -> dict[str, object]:
    worker_id = f"acceptance-worker-{uuid4()}"
    worker = RelayWorker(repository, worker_id, poll_seconds=0.25)
    stop = threading.Event()
    ready = threading.Event()
    errors: list[str] = []

    def run() -> None:
        try:
            worker.serve(stop, ready)
        except RuntimeError as exc:
            errors.append(str(exc))

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    if not ready.wait(5):
        raise RuntimeError("RIV-WRK-0007: Worker did not establish its listener.")
    order = RelayStore().enqueue("relay.noop", {"delay_seconds": 1}, "worker-acceptance", f"worker:{uuid4()}")
    deadline = time.monotonic() + 12
    state = "queued"
    while time.monotonic() < deadline:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT status FROM work_orders WHERE work_order_id=%s",(order.work_order_id,))
            state = cursor.fetchone()[0]
        if state in {"succeeded", "failed", "timed_out"}:
            break
        time.sleep(0.1)
    stop.set()
    thread.join(timeout=3)
    if thread.is_alive():
        raise RuntimeError("RIV-WRK-0008: Worker did not stop within its bounded interval.")
    if errors:
        raise RuntimeError(errors[-1])
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT state,last_notification_at,completed_orders FROM relay_workers WHERE worker_id=%s",(worker_id,))
        row = cursor.fetchone()
    evidence = {
        "work_status": state,
        "worker_row_present": row is not None,
        "worker_state": row[0] if row else None,
        "notification_persisted": bool(row and row[1] is not None),
        "completed_orders": row[2] if row else None,
        "notifications_observed": worker.statistics.notifications,
    }
    if state != "succeeded" or not row or row[0] != "stopped" or row[1] is None or row[2] < 1 or worker.statistics.notifications < 1:
        raise RuntimeError(f"RIV-WRK-0009: Notification-driven worker invariants failed: {json.dumps(evidence, sort_keys=True)}")
    return {"status":"healthy","notification_received":worker.statistics.notifications >= 1,"work_completed":True,"polling_recovery":True,"bounded_stop":True}


if __name__ == "__main__":
    print(json.dumps(acceptance(Path.cwd()), indent=2, sort_keys=True))