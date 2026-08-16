from pathlib import Path

import pytest

from riverview.modules import ModuleRegistry
from riverview.modules.contracts import ModuleManifest
from riverview.topology.graph import build_graph, validate_graph

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
    assert {"context", "events", "failures", "modules", "resident", "room"} <= set(graph["views"])
    assert any(edge.get("checkpoint") == "RIV-RES-0002" for edge in graph["edges"])
