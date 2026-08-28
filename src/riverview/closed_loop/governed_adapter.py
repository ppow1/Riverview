"""Closed-loop adapter boundary for existing Campaign Runner entrypoints."""
from __future__ import annotations
from typing import Any, Callable
from uuid import UUID
from .binding import GovernanceBindingStore


class GovernedClosedLoopAdapter:
    adapter_id = "hermes.campaign_runner.v1"

    def __init__(self, bindings: GovernanceBindingStore, campaign_runner: Callable[[UUID], dict[str, Any]]) -> None:
        self.bindings = bindings
        self.campaign_runner = campaign_runner

    def execute(self, request: dict[str, Any], *, run_id: str) -> dict[str, Any]:
        root_id = UUID(str(request["root_task_id"]))
        binding = self.bindings.require_executable(root_id)
        result = self.campaign_runner(binding.work_order_id)
        if not isinstance(result, dict) or result.get("work_order_id") != str(binding.work_order_id):
            raise RuntimeError("RIV-LOOP-0011: Campaign Runner result does not match bound work order.")
        return {"adapter_id": self.adapter_id, "run_id": run_id, "work_order_id": str(binding.work_order_id), "summary": str(result.get("summary", ""))[:8000], "evidence": list(result.get("evidence", ())), "semantic_outcome": str(result.get("semantic_outcome", "COMPLETED_NO_ATTENTION")), "resulting_sha": result.get("resulting_sha")}
