from __future__ import annotations

from riverview.knowledge.compatibility import adapt_bounded
from riverview.knowledge.extract import ExtractionCandidate
from riverview.knowledge.memory import fresh_context, publish_candidates
from riverview.residents.registry import ResidentRecord
from riverview.spatial.avatar import bind_avatar
from riverview.spatial.input_mapping import resolve_input
from riverview.spatial.status import project_status


def test_project_memory_preserves_decision_and_unresolved_states() -> None:
    entries = publish_candidates(
        (
            ExtractionCandidate("p:1", "P", "source_explicit_decision", "bounded", "src:1", "t", "operational", 1.0),
            ExtractionCandidate("p:2", "P", "ambiguous", "unclear", "src:2", "t", "operational", 0.6, "uncertain"),
        )
    )
    recovered = fresh_context(entries, project="P")
    assert [entry.kind for entry in recovered] == ["source_explicit_decision", "ambiguous"]


def test_compatibility_and_spatial_boundaries() -> None:
    result = adapt_bounded(adapter_id="estate-read-v1", identity="fixture", classification="operational", payload={"state": "ok"}, provenance="estate://fixture")
    assert result.output["state"] == "ok"
    record = ResidentRecord("RES-1", "estate://residents/1", "Manager", "estate://source", "operational", "verified")
    assert bind_avatar(record, asset_reference="fixture://avatar", classification="public").resident_id == "RES-1"
    assert project_status(services=("river",), diagnostics=(), objectives=(), capacity=()).services == ("river",)
    assert resolve_input("voice", "shutdown").requires_confirmation
