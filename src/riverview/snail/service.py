from __future__ import annotations

import argparse
from pathlib import Path

from .adapters import LocalPlanningAdapter, StewardEnvironmentObserver
from .coordinator import SnailCoordinator
from .runtime import SnailRuntime
from .worker import ReasoningWorker


def run_service(
    runtime_root: Path,
    monitor_state: Path,
    latest_frame: Path,
    config_path: Path | None = None,
) -> None:
    """Run the coordinator; the existing Riverview Steward service owns HTTP/8785."""
    runtime = SnailRuntime(runtime_root, config_path)
    coordinator = SnailCoordinator(
        runtime,
        ReasoningWorker(runtime.config["worker"]["endpoint"]),
        StewardEnvironmentObserver(monitor_state, latest_frame, runtime.config.get("infrastructure")),
        LocalPlanningAdapter(runtime.store),
        poll_seconds=float(runtime.config.get("poll_seconds", 2)),
    )
    coordinator.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="SNAIL coordinator integrated with Steward")
    parser.add_argument("--runtime", type=Path, default=Path("var/snail"))
    parser.add_argument("--monitor-state", type=Path, required=True)
    parser.add_argument("--latest-frame", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    run_service(
        args.runtime,
        args.monitor_state,
        args.latest_frame,
        args.config,
    )


if __name__ == "__main__":
    main()
