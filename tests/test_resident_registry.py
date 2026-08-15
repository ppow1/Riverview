from __future__ import annotations

from dataclasses import replace

import pytest

from riverview.residents.registry import ResidentRecord, ResidentRegistry
from riverview.residents.roles import build_role_context


def test_registry_preserves_provenance_and_unknowns() -> None:
    registry = ResidentRegistry()
    record = ResidentRecord(
        "fixture:resident-1",
        "estate://resident/fixture-1",
        None,
        "fixture://authoritative-test-record",
        "operational",
        "unknown",
    )
    registry.add(record)
    registry.add(record)
    assert registry.get(record.resident_id).certainty == "unknown"
    assert registry.snapshot() == (record,)


def test_conflicting_identity_and_operational_role_tools_fail_closed() -> None:
    registry = ResidentRegistry()
    record = ResidentRecord(
        "fixture:resident-2",
        "estate://resident/fixture-2",
        "Character Designer",
        "fixture://authoritative-test-record",
        "operational",
        "verified",
    )
    registry.add(record)
    with pytest.raises(ValueError, match="conflicting"):
        registry.add(replace(record, provenance="other://source"))
    context = build_role_context(
        record,
        allowed_tools=("advisory_reasoning", "shell", "sql", "provider_control", "creative_context"),
    )
    assert context.allowed_tools == ("advisory_reasoning", "creative_context")
