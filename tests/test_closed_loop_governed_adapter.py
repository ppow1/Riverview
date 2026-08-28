from uuid import uuid4
import pytest
from riverview.closed_loop.binding import BindingState, GovernanceBinding, GovernanceBindingStore
from riverview.closed_loop.governed_adapter import GovernedClosedLoopAdapter


def test_governed_adapter_requires_executable_binding_and_preserves_work_order():
    store = GovernanceBindingStore.memory()
    root = uuid4(); work = uuid4()
    store.save(GovernanceBinding(root, uuid4(), objective_id=uuid4(), stage_id=uuid4(), authority_id=uuid4(), work_order_id=work, state=BindingState.EXECUTABLE))
    seen = []
    adapter = GovernedClosedLoopAdapter(store, lambda value: seen.append(value) or {"work_order_id": str(work), "summary": "real entry seam", "evidence": ["runner"], "semantic_outcome": "COMPLETED_NO_ATTENTION"})
    result = adapter.execute({"root_task_id": str(root)}, run_id=str(uuid4()))
    assert seen == [work]
    assert result["adapter_id"] == "hermes.campaign_runner.v1"
    assert result["work_order_id"] == str(work)


def test_governed_adapter_refuses_prepared_root():
    store = GovernanceBindingStore.memory(); root = uuid4()
    store.save(GovernanceBinding(root, uuid4(), specification_id=uuid4(), state=BindingState.PREPARED))
    with pytest.raises(PermissionError):
        GovernedClosedLoopAdapter(store, lambda _: {}).execute({"root_task_id": str(root)}, run_id=str(uuid4()))
