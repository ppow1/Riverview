"""Local stdio MCP transport for the RV-004.4 read-only Relay.

Version: 0.9.3
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from riverview.mcp.read_model import ReadOnlyRelay

SERVER_NAME = "Riverview Read-Only Relay"
mcp = FastMCP(SERVER_NAME)
relay = ReadOnlyRelay()


def _safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


@mcp.tool()
def roadmap_revision() -> Any:
    """Return the latest applied master-roadmap revision."""
    return _safe(relay.roadmap_revision())


@mcp.tool()
def waypoints(limit: int = 200) -> Any:
    """Return a bounded roadmap waypoint projection."""
    return _safe(relay.waypoints(limit))


@mcp.tool()
def current_position() -> Any:
    """Return the bounded current roadmap position."""
    return _safe(relay.current_position())


@mcp.tool()
def relay_workers(limit: int = 50) -> Any:
    """Return bounded Relay worker state."""
    return _safe(relay.workers(limit))


@mcp.tool()
def work_order_status(limit: int = 50) -> Any:
    """Return bounded work-order status without parameters or payloads."""
    return _safe(relay.work_orders(limit))


@mcp.tool()
def completed_work_reports(limit: int = 50) -> Any:
    """Return bounded completed work reports."""
    return _safe(relay.completed_reports(limit))


@mcp.tool()
def open_steward_escalations(limit: int = 50) -> Any:
    """Return bounded open or acknowledged Steward escalations."""
    return _safe(relay.escalations(limit))


@mcp.tool()
def recent_diagnostic_events(limit: int = 100) -> Any:
    """Return bounded recent diagnostic events."""
    return _safe(relay.diagnostics(limit))


@mcp.tool()
def troubleshooting_cookbook(limit: int = 100) -> Any:
    """Return bounded Troubleshooting Cookbook projections."""
    return _safe(relay.cookbook(limit))


def main() -> None:
    """Run only over stdio; no TCP or remote listener is created."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()