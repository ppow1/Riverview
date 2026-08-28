"""Read-only multi-root projection for the future Now workspace."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from riverview.database import connect
from .binding import GovernanceBindingStore
from .tracer import TracerStore


def _result_fields(result: dict[str, Any] | None, binding: dict[str, Any]) -> dict[str, Any]:
    result = result or {}
    adapter = str(result.get("adapter_id") or "")
    work_class = "integration_acceptance" if "campaign" in adapter or adapter.startswith("hermes:") else "production"
    return {
        "latest_result_id": result.get("result_id"),
        "semantic_outcome": result.get("semantic_outcome"),
        "latest_result_summary": result.get("summary"),
        "latest_result_at": result.get("created_at"),
        "current_executor": result.get("provider_id") or binding.get("worker_id"),
        "resource": result.get("resource_class_ref") or result.get("resource") or binding.get("resource_claim_id"),
        "work_class": work_class,
        "attention_required": result.get("semantic_outcome") in {"READY_FOR_STEWARD_REVIEW", "BLOCKED_REQUIRES_STEWARD", "STEWARD_DECISION_REQUIRED"},
    }


def read_now_roots(*, store: TracerStore | None = None, bindings: GovernanceBindingStore | None = None) -> dict[str, Any]:
    generated_at = datetime.now(UTC).isoformat()
    if store is not None and store._memory:
        binding_store = bindings or GovernanceBindingStore.memory()
        items = []
        for root_id, root in store._roots.items():
            binding = binding_store.joined_projection(UUID(root_id))
            items.append({"root_task_id": root_id, "title": root["objective"], "objective": root["objective"], "state": store._states.get(root_id, root["state"]), "completed_checkpoints": 0, "total_checkpoints": 4, "current_checkpoint": root.get("current_checkpoint_id"), "current_actor": "grace", "current_executor": binding.get("worker_id"), "resource_claim_id": binding.get("resource_claim_id"), "started_at": None, "current_checkpoint_started_at": None, "attention_state": root.get("attention_state", "none"), "last_activity": None, "binding_state": binding["binding_state"], "execution_eligible": binding["execution_eligible"], **_result_fields(store.read_projection(root_id), binding)})
        return {"source": "memory:test-seam", "generated_at": generated_at, "freshness": {"state": "fresh", "generated_at": generated_at, "last_successful_hydration": generated_at}, "items": items}
    with connect() as conn, conn.cursor() as cur:
        cur.execute("""SELECT t.root_task_id,t.objective,t.state,t.current_checkpoint_id,t.attention_state,t.created_at,t.updated_at,b.state,b.work_order_id,b.worker_id,b.resource_claim_id,latest.result_id,latest.semantic_outcome,latest.summary,latest.created_at,latest.adapter_id,latest.provider_id,latest.resource_class_ref FROM autonomous_root_tasks t LEFT JOIN autonomous_governance_bindings b ON b.root_task_id=t.root_task_id LEFT JOIN LATERAL (SELECT x.result_id,x.semantic_outcome,x.summary,x.created_at,x.adapter_id,x.provider_id,x.resource_class_ref FROM autonomous_tracer_results x WHERE x.root_task_id=t.root_task_id ORDER BY x.created_at DESC LIMIT 1) latest ON true ORDER BY t.updated_at DESC""")
        rows = cur.fetchall()
    items = []
    for r in rows:
        binding = {"worker_id": r[9], "resource_claim_id": str(r[10]) if r[10] else None}
        result = {"result_id": str(r[11]) if r[11] else None, "semantic_outcome": r[12], "summary": r[13], "created_at": r[14], "adapter_id": r[15], "provider_id": r[16], "resource_class_ref": r[17]} if r[11] else None
        items.append({"root_task_id": str(r[0]), "title": r[1], "objective": r[1], "state": r[2], "current_checkpoint": r[3], "current_actor": r[9] or "grace", "resource_claim_id": binding["resource_claim_id"], "started_at": r[5], "current_checkpoint_started_at": None, "attention_state": r[4], "last_activity": r[6], "binding_state": r[7] or "UNBOUND", "execution_eligible": (r[7] == "EXECUTABLE"), **_result_fields(result, binding)})
    return {"source": "postgresql:autonomous_root_tasks", "generated_at": generated_at, "freshness": {"state": "fresh", "generated_at": generated_at, "last_successful_hydration": generated_at}, "items": items}
