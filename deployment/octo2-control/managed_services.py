"""Version 1.0.0: bounded systemd controls for OCTOMINER2 model workloads.

Only services listed in MANAGED_WORKLOADS can be inspected or controlled.
Starting and stopping a unit never changes its enabled-at-boot state.
"""
from __future__ import annotations

import json
import subprocess
import urllib.request
from typing import Callable


MANAGED_WORKLOADS = {
    "qwen30b-vision": {
        "name": "Qwen 30B Vision",
        "unit": "qwen30b-vision.service",
        "port": 8080,
    },
}


def _run(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout)


def _health(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
            return json.loads(response.read()).get("status") == "ok"
    except Exception:
        return False


def _unit_properties(output: str) -> dict[str, str]:
    return dict(
        line.split("=", 1)
        for line in output.splitlines()
        if "=" in line
    )


def workload_status(
    workload_id: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    health_check: Callable[[int], bool] | None = None,
) -> dict[str, object]:
    workload = MANAGED_WORKLOADS.get(workload_id)
    if workload is None:
        raise ValueError("unknown managed workload")
    runner = runner or _run
    health_check = health_check or _health
    result = runner(
        [
            "systemctl",
            "show",
            workload["unit"],
            "--property=LoadState,ActiveState,SubState,MainPID,UnitFileState",
            "--no-pager",
        ],
        timeout=10,
    )
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "systemd status query failed").strip())
    properties = _unit_properties(result.stdout)
    active = properties.get("ActiveState") == "active"
    return {
        "id": workload_id,
        "name": workload["name"],
        "unit": workload["unit"],
        "port": workload["port"],
        "load_state": properties.get("LoadState", "unknown"),
        "active_state": properties.get("ActiveState", "unknown"),
        "sub_state": properties.get("SubState", "unknown"),
        "main_pid": int(properties.get("MainPID", "0") or 0),
        "enabled_at_boot": properties.get("UnitFileState") == "enabled",
        "running": active,
        "api_ready": active and bool(health_check(int(workload["port"]))),
    }


def list_workloads(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    health_check: Callable[[int], bool] | None = None,
) -> list[dict[str, object]]:
    return [
        workload_status(workload_id, runner=runner, health_check=health_check)
        for workload_id in MANAGED_WORKLOADS
    ]


def transition_workload(
    workload_id: str,
    action: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    health_check: Callable[[int], bool] | None = None,
) -> dict[str, object]:
    workload = MANAGED_WORKLOADS.get(workload_id)
    if workload is None:
        raise ValueError("unknown managed workload")
    if action not in {"start", "stop"}:
        raise ValueError("action must be start or stop")
    runner = runner or _run
    result = runner(["systemctl", action, workload["unit"]], timeout=30)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or f"systemctl {action} failed").strip())
    return workload_status(workload_id, runner=runner, health_check=health_check)
