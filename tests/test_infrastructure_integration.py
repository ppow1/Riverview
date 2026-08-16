from pathlib import Path

import pytest

from riverview.infrastructure.observability import project_observability
from riverview.infrastructure.topology import ServiceNode, validate_topology
from riverview.late_stage.recovery import run_isolated_recovery_drill


def test_service_topology_rejects_port_collision() -> None:
    nodes = (ServiceNode("river", "127.0.0.1", 18080, (), "process", "/health", "river", "config"), ServiceNode("other", "127.0.0.1", 18080, (), "process", "/health", "other", "config"))
    with pytest.raises(ValueError, match="collision"):
        validate_topology(nodes)


def test_recovery_drill_preserves_classified_reference(tmp_path: Path) -> None:
    result = run_isolated_recovery_drill(root=tmp_path, source_reference="ref://synthetic", classification="sensitive", content_hash="hash", credential_reference="credential://synthetic")
    assert result.isolated and result.classification == "sensitive"


def test_observability_excludes_private_payloads() -> None:
    view = project_observability(services=({"service": "river", "payload": "private"},), providers=(), diagnostics=())
    assert view["private_payloads_excluded"] is True
    assert "payload" not in view["services"][0]
