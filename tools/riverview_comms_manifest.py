"""Create or validate the non-secret Riverview Comms registration manifest.

Version: 0.10.0

The generated manifest belongs under the external Riverview runtime tree. It
contains no credentials and does not register or publish the application.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

APPLICATION = "Riverview Comms"
VERSION = "0.11.0"
TOOLS = (
    "roadmap_revision",
    "waypoints",
    "current_position",
    "relay_workers",
    "work_order_status",
    "completed_work_reports",
    "open_steward_escalations",
    "recent_diagnostic_events",
    "troubleshooting_cookbook",
    "mailbox_requests",
    "resource_roadmap",
    "resource_work",
    "resource_reports",
    "resource_diagnostics",
    "resource_cookbook",
    "resource_capacity",
)
PROHIBITED = (
    "arbitrary_sql",
    "filesystem",
    "shell",
    "process",
    "credentials",
    "secrets",
    "undercurrent",
    "write",
)


def runtime_root() -> Path:
    return Path(os.environ.get("RIVERVIEW_RUNTIME_ROOT", r"A:\Riverview\runtime"))


def manifest(endpoint: str) -> dict[str, Any]:
    if not endpoint.startswith("https://") and not endpoint.startswith("http://127.0.0.1:"):
        raise ValueError("RIV-COMMS-0003: endpoint must be HTTPS or loopback HTTP.")
    return {
        "application": APPLICATION,
        "version": VERSION,
        "transport": "streamable-http",
        "endpoint": endpoint.rstrip("/") + "/mcp",
        "health_endpoint": endpoint.rstrip("/") + "/healthz",
        "authentication": "bearer",
        "authority": "read_only",
        "source_of_truth": "postgresql",
        "tools": list(TOOLS),
        "prohibited_capabilities": list(PROHIBITED),
        "registration_required": True,
        "secrets_in_manifest": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the Riverview Comms manifest.")
    parser.add_argument("--endpoint", default=os.environ.get("RIVERVIEW_COMMS_ENDPOINT", "http://127.0.0.1:11825"))
    parser.add_argument("--output", type=Path, default=runtime_root() / "comms" / "manifest.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = manifest(args.endpoint)
    if args.check:
        actual = json.loads(args.output.read_text(encoding="utf-8"))
        if actual != expected:
            raise SystemExit("RIV-COMMS-0004: registration manifest differs from the expected contract.")
        print(json.dumps({"status": "healthy", "application": APPLICATION, "version": VERSION}))
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "written", "application": APPLICATION, "path": str(args.output)}))


if __name__ == "__main__":
    main()
