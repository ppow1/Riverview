from __future__ import annotations

from riverview.residents.continuity import evaluate_continuity
from riverview.residents.registry import ResidentRecord


def test_continuity_preserves_identity_across_provider_and_interface() -> None:
    record = ResidentRecord(
        "RES-000001", "estate://residents/res-000001", "Manager", "estate://source", "operational", "verified"
    )
    result = evaluate_continuity(record, provider_id="local:fixture", interface_id="riverview-openwebui")
    assert result.identity_preserved
    assert result.classification_preserved
    assert result.source_reference == "estate://source"
