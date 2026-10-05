from __future__ import annotations

import argparse
import threading
from pathlib import Path

from .adapters import LocalPlanningAdapter, StewardEnvironmentObserver
from .coordinator import SnailCoordinator
from .runtime import SnailRuntime
from .server import build_server
from .worker import ReasoningWorker


def run_service(
    runtime_root: Path,
    monitor_state: Path,
    latest_frame: Path,
    host: str = "127.0.0.1",
    port: int = 8785,
    config_path: Path | None = None,
) -> None:
    runtime = SnailRuntime(runtime_root, config_path)
    coordinator = SnailCoordinator(
        runtime,
        ReasoningWorker(runtime.config["worker"]["endpoint"]),
        StewardEnvironmentObserver(monitor_state, latest_frame, runtime.config.get("infrastructure")),
        LocalPlanningAdapter(runtime.store),
        poll_seconds=float(runtime.config.get("poll_seconds", 2)),
    )
    thread = threading.Thread(target=coordinator.run, name="snail-coordinator", daemon=True)
    server = build_server(runtime, host, port, latest_frame, coordinator)

    def stop_server_after_coordinator() -> None:
        thread.join()
        server.shutdown()

    thread.start()
    watcher = threading.Thread(target=stop_server_after_coordinator, name="snail-stop-watcher", daemon=True)
    watcher.start()
    try:
        server.serve_forever()
    finally:
        if thread.is_alive():
            runtime.store.enqueue_control("STOP")
            coordinator.wake()
            thread.join(timeout=10)
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="SNAIL coordinator integrated with Steward")
    parser.add_argument("--runtime", type=Path, default=Path("var/snail"))
    parser.add_argument("--monitor-state", type=Path, required=True)
    parser.add_argument("--latest-frame", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8785)
    args = parser.parse_args()
    run_service(
        args.runtime,
        args.monitor_state,
        args.latest_frame,
        args.host,
        args.port,
        args.config,
    )


if __name__ == "__main__":
    main()
