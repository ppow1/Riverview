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
