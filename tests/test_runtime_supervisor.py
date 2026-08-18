import json
from pathlib import Path

import pytest

from riverview.runtime.supervisor import RuntimeSupervisor, ServiceRegistry

ROOT = Path(__file__).parents[1]


def test_runtime_registry_has_one_ordered_owner_and_required_services():
    registry = ServiceRegistry.from_file(ROOT / "config/runtime/riverview-runtime-services.json")
    ids = {spec.service_id for spec in registry.ordered()}
    assert ids == {"operator", "cme-supervisor", "comms5-http", "comms5-transport", "relay-worker"}
    assert registry.specs["relay-worker"].dependencies == ("cme-supervisor",)
    assert registry.specs["comms5-transport"].dependencies == ("comms5-http",)


def test_runtime_registry_rejects_missing_dependency_and_cycles(tmp_path: Path):
    missing = tmp_path / "missing.json"
    missing.write_text(
        json.dumps({"services": [{"service_id": "a", "command": ["x"], "dependencies": ["b"]}]})
    )
    with pytest.raises(ValueError, match="missing dependencies"):
        ServiceRegistry.from_file(missing)
    cycle = tmp_path / "cycle.json"
    cycle.write_text(
        json.dumps(
            {
                "services": [
                    {"service_id": "a", "command": ["x"], "dependencies": ["b"]},
                    {"service_id": "b", "command": ["x"], "dependencies": ["a"]},
                ]
            }
        )
    )
    with pytest.raises(ValueError, match="dependency cycle"):
        ServiceRegistry.from_file(cycle)


def test_runtime_status_is_bounded_and_does_not_contain_secret_value(tmp_path: Path):
    registry = ROOT / "config/runtime/riverview-runtime-services.json"
    supervisor = RuntimeSupervisor(ROOT, registry, status_path=tmp_path / "status.json")
    supervisor.write_status()
    status = json.loads((tmp_path / "status.json").read_text())
    assert status["schema_version"] == "riverview-runtime-status-v1"
    assert status["supervisor"] == "riverview.runtime.supervisor"
    assert status["services"]["operator"]["credential_available"] is True
    assert "webui_secret_key" not in json.dumps(status).lower()


def test_runtime_supervisor_rejects_nonpositive_poll(tmp_path: Path):
    with pytest.raises(ValueError, match="poll_seconds"):
        RuntimeSupervisor(
            ROOT,
            ROOT / "config/runtime/riverview-runtime-services.json",
            status_path=tmp_path / "x",
            poll_seconds=0,
        )


def test_runtime_command_expands_windows_environment_syntax(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RIVERVIEW_TEST_HOME", "C:/Users/example")
    assert RuntimeSupervisor._expand_command_item(
        "${RIVERVIEW_TEST_HOME}/.ssh/id_ed25519"
    ) == "C:/Users/example/.ssh/id_ed25519"


def test_runtime_status_identifies_top_level_owner(tmp_path: Path):
    supervisor = RuntimeSupervisor(
        ROOT,
        ROOT / "config/runtime/riverview-runtime-services.json",
        status_path=tmp_path / "status.json",
    )
    supervisor.write_status()
    status = json.loads((tmp_path / "status.json").read_text())
    assert status["supervisor_pid"] > 0
    assert status["lock_path"].endswith("riverview-supervisor.lock.d")
