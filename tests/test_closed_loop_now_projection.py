from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from riverview.closed_loop.tracer import TracerStore
from riverview.closed_loop.binding import GovernanceBinding, GovernanceBindingStore, BindingState
from riverview.closed_loop.now_projection import read_now_roots


def test_now_projection_is_root_scoped_and_reports_freshness():
    with TemporaryDirectory() as temporary:
        store = TracerStore.memory(artifact_root=Path(temporary))
        root = store.create("Now projection test")
        binding = GovernanceBinding(UUID(root["root_task_id"]), UUID(root["correlation_id"]), state=BindingState.PREPARED)
        bindings = GovernanceBindingStore.memory()
        bindings.save(binding)
        projection = read_now_roots(store=store, bindings=bindings)
        assert projection["source"] == "memory:test-seam"
        assert projection["freshness"]["state"] == "fresh"
        assert projection["items"][0]["root_task_id"] == root["root_task_id"]
        assert projection["items"][0]["binding_state"] == "PREPARED"
        assert projection["items"][0]["execution_eligible"] is False


def test_now_projection_summarizes_latest_result_executor_resource_and_class():
    with TemporaryDirectory() as temporary:
        store = TracerStore.memory(artifact_root=Path(temporary))
        request = store.dispatch("Novel operations root", "grace")
        root = request
        binding = GovernanceBinding(UUID(root["root_task_id"]), UUID(root["correlation_id"]), objective_id=UUID(int=10), stage_id=UUID(int=11), authority_id=UUID(int=12), work_order_id=UUID(int=13), state=BindingState.RESULT_AVAILABLE, worker_id="relay.primary", resource_claim_id=UUID(int=1))
        bindings = GovernanceBindingStore.memory(); bindings.save(binding)
        claimed = store.claim(request["request_id"], "relay.primary")
        result = store.record_external_result({"root_task_id": root["root_task_id"], "correlation_id": root["correlation_id"], "request_id": request["request_id"], "run_id": str(UUID(int=2)), "work_order_id": str(UUID(int=3)), "attempt_id": str(UUID(int=4)), "semantic_outcome": "READY_FOR_STEWARD_REVIEW", "summary": "bounded result", "evidence": ["evidence:result"], "adapter_id": "hermes.campaign_runner.v1", "external_reconciliation": True})
        projection = read_now_roots(store=store, bindings=bindings)
        item = projection["items"][0]
        assert item["latest_result_id"] == result["result_id"]
        assert item["semantic_outcome"] == "READY_FOR_STEWARD_REVIEW"
        assert item["work_class"] == "integration_acceptance"
