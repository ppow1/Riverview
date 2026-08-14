"""RV-004.4 read-model acceptance and authority checks.

Version: 0.9.3
"""

from __future__ import annotations

import json

from riverview.mcp import ReadOnlyRelay

REQUIRED_METHODS = {
    "roadmap_revision",
    "waypoints",
    "current_position",
    "workers",
    "work_orders",
    "completed_reports",
    "escalations",
    "diagnostics",
    "cookbook",
}
PROHIBITED_METHODS = {
    "enqueue",
    "execute_sql",
    "filesystem",
    "shell",
    "secret",
    "credential",
    "undercurrent",
    "write",
}


def acceptance() -> dict[str, object]:
    relay = ReadOnlyRelay()
    methods = {
        name
        for name in dir(relay)
        if not name.startswith("_") and callable(getattr(relay, name))
    }
    missing = sorted(REQUIRED_METHODS - methods)
    prohibited = sorted(PROHIBITED_METHODS & methods)
    if missing:
        raise RuntimeError(f"RIV-MCP-0001: Required read surface missing: {missing}")
    if prohibited:
        raise RuntimeError(f"RIV-MCP-0002: Prohibited authority exposed: {prohibited}")

    revision = relay.roadmap_revision()
    position = relay.current_position()
    relay.workers(1)
    relay.work_orders(1)
    relay.completed_reports(1)
    relay.escalations(1)
    relay.diagnostics(1)
    relay.cookbook(1)
    relay.waypoints(1)

    return {
        "status": "healthy",
        "authority": "read_only",
        "roadmap_revision": None if revision is None else revision["revision_id"],
        "position_items": len(position["items"]),
        "prohibited_authority_exposed": False,
    }


if __name__ == "__main__":
    print(json.dumps(acceptance(), indent=2, sort_keys=True, default=str))