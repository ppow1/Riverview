import json
from pathlib import Path

import pytest

from riverview.runtime.supervisor import RuntimeSupervisor, ServiceRegistry

ROOT = Path(__file__).parents[1]


def test_runtime_registry_has_one_ordered_owner_and_required_services():
    registry = ServiceRegistry.from_file(ROOT / "config/runtime/riverview-runtime-services.json")
    ids = {spec.service_id for spec in registry.ordered()}
    assert ids == {"operator", "spatial", "cme-supervisor", "comms5-http", "comms5-transport", "relay-worker"}
    assert registry.specs["spatial"].process_match == "riverview.operator.lan_spatial_service"
    assert registry.specs["relay-worker"].dependencies == ("cme-supervisor",)
    assert registry.specs["comms5-transport"].dependencies == ("comms5-http",)
    assert registry.specs["comms5-http"].environment == {"RIVERVIEW_COMMS5_TRANSPORT_DIAGNOSTICS": "1"}
    assert registry.specs["cme-supervisor"].process_match == "riverview.autonomy.live_service"


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


def test_process_adoption_does_not_match_diagnostic_command_text() -> None:
    spec = ServiceRegistry.from_file(ROOT / "config/runtime/riverview-runtime-services.json").specs["cme-supervisor"]
    service = {"pid": 42, "ppid": 1, "cmdline": "powershell -Command Where-Object { $_.CommandLine -match 'riverview.autonomy.supervisor' }"}
    actual = {"pid": 43, "ppid": 1, "cmdline": ".venv/Scripts/python.exe -m riverview.autonomy.live_service"}
    assert RuntimeSupervisor._process_matches(spec, service) is False
    assert RuntimeSupervisor._process_matches(spec, actual) is True


def test_relay_service_recycle_is_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    supervisor = RuntimeSupervisor(ROOT, ROOT / "config/runtime/riverview-runtime-services.json")
    active = [{"pid": 123, "ppid": 1, "cmdline": "relay", "executable": "python"}]
    monkeypatch.setattr(supervisor, "_processes", lambda: list(active))
    monkeypatch.setattr(supervisor, "_process_matches", lambda _spec, _process: True)
    monkeypatch.setattr(supervisor, "_terminate_process_tree", lambda _pid: active.clear())
    result = supervisor._recycle_service("relay-worker")
    assert result["service_id"] == "relay-worker"


def test_comms5_http_service_recycle_is_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    supervisor = RuntimeSupervisor(ROOT, ROOT / "config/runtime/riverview-runtime-services.json")
    active = [{"pid": 123, "ppid": 1, "cmdline": "comms5", "executable": "python"}]
    monkeypatch.setattr(supervisor, "_processes", lambda: list(active))
    monkeypatch.setattr(supervisor, "_process_matches", lambda _spec, _process: True)
    monkeypatch.setattr(supervisor, "_terminate_process_tree", lambda _pid: active.clear())
    result = supervisor._recycle_service("comms5-http")
    assert result["service_id"] == "comms5-http"


def test_launcher_child_tree_is_one_managed_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    supervisor = RuntimeSupervisor(ROOT, ROOT / "config/runtime/riverview-runtime-services.json")
    state = supervisor.states["cme-supervisor"]
    processes = [
        {"pid": 100, "ppid": 1, "cmdline": ".venv/python -m riverview.autonomy.live_service"},
        {"pid": 101, "ppid": 100, "cmdline": ".venv/python -m riverview.autonomy.live_service"},
    ]
    monkeypatch.setattr(supervisor, "_processes", lambda: processes)
    assert supervisor._adopt(state) is True
    assert state.pid == 100


def test_supervisor_processes_only_canonical_cme_recycle_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    supervisor = RuntimeSupervisor(ROOT, ROOT / "config/runtime/riverview-runtime-services.json")
    supervisor.repository = tmp_path
    request_dir = tmp_path / "runtime" / "riverview-supervisor" / "requests"
    request_dir.mkdir(parents=True)
    (request_dir / "request.json").write_text('{"operation":"reload_service","service_id":"cme-supervisor"}')
    monkeypatch.setattr(supervisor, "_recycle_service", lambda service_id: {"service_id": service_id, "status": "stopped"})
    supervisor._process_control_requests()
    result = json.loads((request_dir / "results" / "request.json").read_text())
    assert result == {"ok": True, "service_id": "cme-supervisor", "status": "stopped"}


def test_supervisor_accepts_windows_powershell_utf8_bom_recycle_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    supervisor = RuntimeSupervisor(ROOT, ROOT / "config/runtime/riverview-runtime-services.json")
    supervisor.repository = tmp_path
    request_dir = tmp_path / "runtime" / "riverview-supervisor" / "requests"
    request_dir.mkdir(parents=True)
    (request_dir / "request.json").write_text(
        '{"operation":"reload_service","service_id":"cme-supervisor"}',
        encoding="utf-8-sig",
    )
    monkeypatch.setattr(supervisor, "_recycle_service", lambda service_id: {"service_id": service_id, "status": "stopped"})
    supervisor._process_control_requests()
    result = json.loads((request_dir / "results" / "request.json").read_text())
    assert result["ok"] is True
