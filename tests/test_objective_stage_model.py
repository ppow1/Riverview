"""Contract tests for RV-005.2 objective/stage model.

Version: 0.2.0
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from riverview.grace.objectives import ObjectiveStore, StageSpec


def unique_key(name: str) -> str:
    return f"test.rv0052.{name}.{uuid4()}"


def test_dependencies_persist_and_gate_readiness() -> None:
    key=unique_key("dependency")
    store=ObjectiveStore()
    store.create(
        key,
        "Dependency test",
        "Dependency readiness",
        [
            StageSpec("first","First","First stage"),
            StageSpec("second","Second","Second stage",depends_on=("first",)),
        ],
        requested_by="pytest",
    )
    state=store.load(key)
    assert state["stages"][0]["readiness"]=="ready"
    assert state["stages"][1]["readiness"]=="waiting"
    assert state["stages"][1]["depends_on"]==["first"]


def test_required_evidence_cannot_be_bypassed() -> None:
    key=unique_key("evidence")
    store=ObjectiveStore()
    store.create(
        key,
        "Evidence test",
        "Required evidence",
        [StageSpec("only","Only","Only stage",required_evidence=("proof:required",))],
        requested_by="pytest",
    )
    with pytest.raises(RuntimeError,match="missing required evidence"):
        store.complete_stage(key,"only",{"bad":True})


def test_final_output_requires_all_stages_complete() -> None:
    key=unique_key("final")
    store=ObjectiveStore()
    store.create(
        key,
        "Final test",
        "Final output",
        [StageSpec("only","Only","Only stage")],
        requested_by="pytest",
    )
    with pytest.raises(RuntimeError,match="incomplete stages"):
        store.finalize(key,{"bad":True})


def test_unknown_dependency_is_rejected_transactionally() -> None:
    key=unique_key("unknown")
    store=ObjectiveStore()
    with pytest.raises(ValueError,match="depends on unknown stage"):
        store.create(
            key,
            "Unknown dependency",
            "Reject invalid graph",
            [StageSpec("only","Only","Only",depends_on=("missing",))],
            requested_by="pytest",
        )
    with pytest.raises(RuntimeError,match="not found"):
        store.load(key)