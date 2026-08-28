"""Read-only multi-root projection for the future Now workspace."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from riverview.database import connect
from .binding import GovernanceBindingStore
from .tracer import TracerStore


def read_now_roots(*, store: TracerStore | None = None, bindings: GovernanceBindingStore | None = None) -> dict[str, Any]:
    generated_at = datetime.now(UTC).isoformat()
    if store is not None and store._memory:
        binding_store = bindings or GovernanceBindingStore.memory()
        items = []
        for root_id, root in store._roots.items():
            binding = binding_store.joined_projection(UUID(root_id))
            items.append({"root_task_id": root_id, "title": root["objective"], "objective": root["objective"], "state": store._states.get(root_id, root["state"]), "completed_checkpoints": 0, "total_checkpoints": 4, "current_checkpoint": root.get("current_checkpoint_id"), "current_actor": "grace", "current_executor": binding.get("worker_id"), "resource_claim_id": binding.get("resource_claim_id"), "started_at": None, "current_checkpoint_started_at": None, "attention_state": root.get("attention_state", "none"), "last_activity": None, "binding_state": binding["binding_state"], "execution_eligible": binding["execution_eligible"]})
        return {"source": "memory:test-seam", "generated_at": generated_at, "freshness": {"state": "fresh", "generated_at": generated_at, "last_successful_hydration": generated_at}, "items": items}
    with connect() as conn, conn.cursor() as cur:
        cur.execute("""SELECT t.root_task_id,t.objective,t.state,t.current_checkpoint_id,t.attention_state,t.created_at,t.updated_at,b.state,b.work_order_id,b.worker_id,b.resource_claim_id FROM autonomous_root_tasks t LEFT JOIN autonomous_governance_bindings b ON b.root_task_id=t.root_task_id ORDER BY t.updated_at DESC""")
        rows = cur.fetchall()
    items = [{"root_task_id": str(r[0]), "title": r[1], "objective": r[1], "state": r[2], "completed_checkpoints": None, "total_checkpoints": None, "current_checkpoint": r[3], "current_actor": r[9] or "grace", "current_executor": r[9], "resource_claim_id": str(r[10]) if r[10] else None, "started_at": r[5], "current_checkpoint_started_at": None, "attention_state": r[4], "last_activity": r[6], "binding_state": r[7] or "UNBOUND", "execution_eligible": (r[7] == "EXECUTABLE")} for r in rows]
    return {"source": "postgresql:autonomous_root_tasks", "generated_at": generated_at, "freshness": {"state": "fresh", "generated_at": generated_at, "last_successful_hydration": generated_at}, "items": items}
