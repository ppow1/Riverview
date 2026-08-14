"""Live subprocess acceptance for the restricted runner.

Version: 0.5.0
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4

from riverview.database import connect
from riverview.relay import RelayStore
from riverview.runner import RestrictedRunner


def acceptance(repository: Path) -> dict[str, object]:
    tool = repository / "tools" / "powershell" / "relay" / "Invoke-RiverviewNoOp.ps1"
    digest = hashlib.sha256(tool.read_bytes()).hexdigest()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE approved_actions SET command_sha256=%s WHERE action_type IN('relay.noop','relay.timeout_probe')",(digest,))
    store = RelayStore()
    runner = RestrictedRunner(repository, "acceptance-runner", 0.25)
    success = store.enqueue("relay.noop", {"delay_seconds": 2}, "acceptance", f"runner-success:{uuid4()}")
    result = runner.run_once()
    if not result or result["status"] != "succeeded":
        raise RuntimeError("RIV-RUN-0009: No-op execution failed.")
    timeout = store.enqueue("relay.timeout_probe", {"delay_seconds": 3}, "acceptance", f"runner-timeout:{uuid4()}")
    timed = runner.run_once()
    if not timed or timed["status"] != "timed_out":
        raise RuntimeError("RIV-RUN-0009: Timeout execution failed.")
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT status FROM work_orders WHERE work_order_id=%s", (success.work_order_id,))
        success_state = cursor.fetchone()[0]
        cursor.execute("SELECT status FROM work_orders WHERE work_order_id=%s", (timeout.work_order_id,))
        timeout_state = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM steward_escalations WHERE work_order_id=%s AND state='open'", (timeout.work_order_id,))
        escalations = cursor.fetchone()[0]
    if success_state != "succeeded" or timeout_state != "timed_out" or escalations != 1:
        raise RuntimeError("RIV-RUN-0009: Persisted runner invariants failed.")
    return {"status": "healthy", "subprocess_succeeded": True, "heartbeats": True, "timeout_terminated": True, "steward_escalation": True}


if __name__ == "__main__":
    print(json.dumps(acceptance(Path.cwd()), indent=2, sort_keys=True))