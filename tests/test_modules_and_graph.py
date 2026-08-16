from pathlib import Path

import pytest

from riverview.modules import ModuleRegistry
from riverview.modules.contracts import ModuleManifest
from riverview.topology.graph import (
    build_graph,
    render_mermaid,
    validate_graph,
    validate_mermaid,
    validate_projection_drift,
    write_graph,
)

ROOT = Path(__file__).parents[1]


def test_declared_modules_validate_without_secrets():
    registry = ModuleRegistry.from_directory(ROOT / "config" / "modules")
    assert {manifest.module_id for manifest in registry.manifests()} == {"riverview.operator", "riverview.reasoning.ollama"}
    for path in (ROOT / "config" / "modules").glob("*.json"):
        assert "token" not in path.read_text(encoding="utf-8").casefold()


def test_incompatible_module_fails_closed():
    data = {"module_id": "bad", "display_name": "bad", "module_version": "1", "required_core_contract": "riverview-core-contract-9.0", "module_type": "test"}
    with pytest.raises(ValueError, match="incompatible"):
        ModuleRegistry((ModuleManifest.from_dict(data),))


def test_system_graph_has_valid_endpoints_and_checkpoint_links():
    graph = build_graph(ROOT / "config" / "modules")
    assert not validate_graph(graph)
    assert len(graph["nodes"]) > 40
    assert len(graph["edges"]) > 80
    assert {"context", "events", "failures", "modules", "resident", "room", "character", "comms", "services"} <= set(graph["views"])
    assert any(edge.get("checkpoint") == "RIV-RES-0002" for edge in graph["edges"])
    assert not validate_mermaid(render_mermaid(graph), graph)
    assert "{node[" not in render_mermaid(graph)


def test_graph_questions_are_explicit_and_views_are_generated(tmp_path):
    graph = build_graph(ROOT / "config" / "modules")
    assert len(graph["questions"]) == 21
    assert {answer["status"] for answer in graph["questions"].values()} <= {"PASS", "ARCHITECTURE_GAP"}
    write_graph(graph, tmp_path)
    views = tmp_path / "graph_views"
    assert len(list(views.glob("*.mmd"))) == 11
    assert 'river["River event runtime / PostgreSQL"]' in (tmp_path / "riverview_system_graph.mmd").read_text(encoding="utf-8")
    assert "{node[" not in (tmp_path / "riverview_system_graph.mmd").read_text(encoding="utf-8")


def test_checked_in_graph_projections_are_not_stale():
    graph = build_graph(ROOT / "config" / "modules")
    assert validate_projection_drift(graph, ROOT / "docs" / "architecture") == []
