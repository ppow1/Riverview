from __future__ import annotations

import inspect
import json
import threading
import time
import urllib.request
from pathlib import Path
import riverview.status.server as steward_server
from riverview.snail.adapters import LocalPlanningAdapter
from riverview.snail.coordinator import SnailCoordinator
from riverview.snail.runtime import SnailRuntime
from riverview.snail.service import run_service


class UnusedWorker:
    def reason(self, _packet):
        raise AssertionError("paused coordinator must not reason")


class ReadyObserver:
    def observe(self):
        return {
            "observed_at": "qualification",
            "worker": {"state": "80B_READY", "boot_id": "boot-a", "pid": "100"},
            "target": {"identity": "OCTO1", "state": "UNCHANGED"},
            "frame": {"available": False, "path": "latest.jpg"},
            "infrastructure": {"dev": {"status": "READY"}},
        }


def river_projection():
    return {
        "generated_at": "2026-10-05T00:00:00+00:00",
        "status": "healthy",
        "authority": "read_only",
        "roadmap": [],
        "workers": [],
        "work_counts": [],
        "recent_work": [],
        "escalations": [],
        "diagnostics": [],
        "migrations": [],
    }


def request(url: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=2) as response:
        return response.status, response.headers, response.read()


def test_existing_steward_owns_single_surface_and_controls_live_coordinator(tmp_path, monkeypatch):
    root = tmp_path / "snail"
    runtime = SnailRuntime(root)
    runtime.command("PAUSE")
    frame = tmp_path / "latest.jpg"
    frame.write_bytes(b"jpeg-evidence")
    state = runtime.state
    state["last_observation"] = {"frame": {"path": str(frame)}}
    runtime.store.save_state(state)

    coordinator = SnailCoordinator(
        runtime,
        UnusedWorker(),
        ReadyObserver(),
        LocalPlanningAdapter(runtime.store),
        poll_seconds=0.02,
    )
    coordinator_thread = threading.Thread(target=coordinator.run)
    coordinator_thread.start()

    monkeypatch.setattr(steward_server, "status_snapshot", river_projection)
    server = steward_server.build_server("127.0.0.1", 0, snail_runtime=root)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        status, _, html = request(base + "/")
        assert status == 200
        assert b"The Estate at Riverview" in html
        assert b"SNAIL" in html

        status, _, river = request(base + "/api/status")
        assert status == 200
        assert json.loads(river)["authority"] == "read_only"

        status, _, snail = request(base + "/api/snail/status")
        assert status == 200
        assert json.loads(snail)["snail_state"] == "PAUSED"

        status, headers, image = request(base + "/api/snail/frame")
        assert status == 200
        assert headers["Content-Type"] == "image/jpeg"
        assert image == b"jpeg-evidence"

        status, _, control = request(base + "/api/snail/control", {"command": "STOP"})
        assert status == 202
        assert json.loads(control)["command"] == "STOP"
        coordinator_thread.join(timeout=2)
        assert not coordinator_thread.is_alive()
        assert runtime.state["snail_state"] == "STOPPED"
        assert runtime.state["checkpoint_time"]
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
        if coordinator_thread.is_alive():
            runtime.store.enqueue_control("STOP")
            coordinator.wake()
            coordinator_thread.join(timeout=2)


def test_snail_service_does_not_accept_or_bind_a_steward_port():
    parameters = inspect.signature(run_service).parameters
    assert "host" not in parameters
    assert "port" not in parameters


def test_existing_steward_launcher_mounts_snail_without_second_server():
    launcher = Path("tools/powershell/status/Start-RiverviewStewardStatus.ps1").read_text(
        encoding="utf-8"
    )
    assert "riverview.status.server" in launcher
    assert "--snail-runtime" in launcher
    assert "riverview.snail.server" not in launcher
    installer = Path("tools/powershell/status/Install-RiverviewStewardStatus.ps1").read_text(
        encoding="utf-8"
    )
    assert 'elif self.path == "/api/snail/status"' in installer
    assert "--snail-runtime" in installer


def test_steward_remains_running_when_coordinator_stops(tmp_path, monkeypatch):
    root = tmp_path / "snail"
    SnailRuntime(root)
    monkeypatch.setattr(steward_server, "status_snapshot", river_projection)
    server = steward_server.build_server("127.0.0.1", 0, snail_runtime=root)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        SnailRuntime(root).command("STOP")
        time.sleep(0.05)
        status, _, body = request(f"http://127.0.0.1:{server.server_port}/api/status")
        assert status == 200
        assert json.loads(body)["status"] == "healthy"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
