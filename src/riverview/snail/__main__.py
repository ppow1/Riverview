from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runtime import SnailRuntime


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m riverview.snail")
    parser.add_argument("--runtime", type=Path, default=Path("var/snail"))
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "stop", "status", "pause", "resume", "abort", "snapshot", "reasoning-packet"):
        command = sub.add_parser(name)
        if name == "snapshot":
            command.add_argument("--reason", default="External second-set-of-eyes review")
    for name in ("update-task", "update-direction", "inquiry", "physical-work-complete"):
        command = sub.add_parser(name)
        command.add_argument("value")
    monitor = sub.add_parser("observe-worker")
    monitor.add_argument("monitor_state", type=Path)
    run = sub.add_parser("run", aliases=["start"])
    run.add_argument("--monitor-state", type=Path, required=True)
    run.add_argument("--latest-frame", type=Path, required=True)
    args = parser.parse_args()
    runtime = SnailRuntime(args.runtime)
    if args.command == "init":
        result = runtime.start()
    elif args.command in {"run", "start"}:
        from .service import run_service

        run_service(args.runtime, args.monitor_state, args.latest_frame)
        return
    elif args.command == "status":
        result = runtime.state
    elif args.command == "reasoning-packet":
        result = runtime.build_reasoning_packet()
    elif args.command == "snapshot":
        result = {"snapshot": str(runtime.snapshot(args.reason))}
    elif args.command == "observe-worker":
        runtime.ingest_octo2_monitor(args.monitor_state)
        result = runtime.state
    else:
        mapping = {"stop": "STOP", "pause": "PAUSE", "resume": "RESUME", "abort": "ABORT", "update-task": "UPDATE_TASK", "update-direction": "UPDATE_DIRECTION", "inquiry": "INQUIRY", "physical-work-complete": "PHYSICAL_WORK_COMPLETE"}
        result = runtime.store.enqueue_control(mapping[args.command], getattr(args, "value", None))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
