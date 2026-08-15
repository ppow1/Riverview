from __future__ import annotations

import json
from pathlib import Path

from riverview.residents.registry import ResidentRecord, ResidentRegistry
from riverview.residents.roles import build_role_context


def test_authoritative_estate_metadata_resolves_to_bounded_registry() -> None:
    evidence = json.loads(
        Path("docs/operations/roadmap/evidence/RV-014.1_RESIDENT_REGISTRY.json").read_text()
    )
    registry = ResidentRegistry()
    for item in evidence["records"]:
        registry.add(
            ResidentRecord(
                item["resident_id"],
                item["canonical_reference"],
                item["office"],
                item["source_reference"],
                item["classification"],
                item["certainty"],
            )
        )
    assert len(registry.snapshot()) == 6
    for record in registry.snapshot():
        context = build_role_context(record, allowed_tools=("advisory_reasoning", "sql"))
        assert context.resident_id == record.resident_id
        assert context.allowed_tools == ("advisory_reasoning",)
