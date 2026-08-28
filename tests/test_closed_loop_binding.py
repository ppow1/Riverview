from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytest

from riverview.closed_loop.binding import BindingState, GovernanceBinding, GovernanceBindingStore


def test_binding_represents_prepared_and_refuses_execution_without_authority():
    binding = GovernanceBinding(root_task_id=uuid4(), correlation_id=uuid4(), specification_id=uuid4(), state=BindingState.PREPARED)
    store = GovernanceBindingStore.memory()
    store.save(binding)
    assert store.read(binding.root_task_id).state is BindingState.PREPARED
    with pytest.raises(PermissionError, match="not executable"):
        store.require_executable(binding.root_task_id)


def test_binding_requires_exact_root_correlation_and_work_lineage():
    store = GovernanceBindingStore.memory()
    root, correlation = uuid4(), uuid4()
    binding = GovernanceBinding(root_task_id=root, correlation_id=correlation, objective_id=uuid4(), stage_id=uuid4(), authority_id=uuid4(), work_order_id=uuid4(), state=BindingState.EXECUTABLE)
    store.save(binding)
    assert store.require_executable(root).work_order_id == binding.work_order_id
    with pytest.raises(ValueError, match="correlation"):
        store.bind_work(root, uuid4(), binding.work_order_id)


def test_binding_states_are_root_scoped():
    store = GovernanceBindingStore.memory()
    a, b = uuid4(), uuid4()
    store.save(GovernanceBinding(a, uuid4(), state=BindingState.AWAITING_AUTHORITY))
    store.save(GovernanceBinding(b, uuid4(), state=BindingState.EXECUTABLE, objective_id=uuid4(), stage_id=uuid4(), authority_id=uuid4(), work_order_id=uuid4()))
    assert store.read(a).state is BindingState.AWAITING_AUTHORITY
    assert store.read(b).state is BindingState.EXECUTABLE
