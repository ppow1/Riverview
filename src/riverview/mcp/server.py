"""Local stdio MCP transport for the RV-004.4/RV-008.1 read-only Relay.

Version: 0.10.0
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


@mcp.tool()
def resource_roadmap(limit: int = 50, cursor: int = 0, classification: str = "river") -> Any:
    """Return one bounded, classification-filtered roadmap resource page."""
    return _safe(relay.resource_roadmap(limit, cursor, classification))


@mcp.tool()
def resource_work(limit: int = 50, cursor: int = 0, classification: str = "river") -> Any:
    """Return one bounded, classification-filtered work resource page."""
    return _safe(relay.resource_work(limit, cursor, classification))


@mcp.tool()
def resource_reports(limit: int = 50, cursor: int = 0, classification: str = "river") -> Any:
    """Return one bounded, classification-filtered report resource page."""
    return _safe(relay.resource_reports(limit, cursor, classification))


@mcp.tool()
def resource_diagnostics(limit: int = 50, cursor: int = 0, classification: str = "river") -> Any:
    """Return one bounded, classification-filtered diagnostic resource page."""
    return _safe(relay.resource_diagnostics(limit, cursor, classification))


@mcp.tool()
def resource_cookbook(limit: int = 50, cursor: int = 0, classification: str = "river") -> Any:
    """Return one bounded, classification-filtered Cookbook resource page."""
    return _safe(relay.resource_cookbook(limit, cursor, classification))


@mcp.tool()
def resource_capacity(limit: int = 50, cursor: int = 0, classification: str = "river") -> Any:
    """Return one bounded, classification-filtered capacity resource page."""
    return _safe(relay.resource_capacity(limit, cursor, classification))


@mcp.resource("riverview://roadmap/{cursor}")
def roadmap_resource(cursor: str) -> Any:
    """Expose a bounded River roadmap resource page through the MCP resource API."""
    return _safe(relay.resource_roadmap(cursor=int(cursor), classification="river"))


@mcp.resource("riverview://work/{cursor}")
def work_resource(cursor: str) -> Any:
    """Expose a bounded River work resource page through the MCP resource API."""
    return _safe(relay.resource_work(cursor=int(cursor), classification="river"))


@mcp.resource("riverview://reports/{cursor}")
def reports_resource(cursor: str) -> Any:
    """Expose a bounded River report resource page through the MCP resource API."""
    return _safe(relay.resource_reports(cursor=int(cursor), classification="river"))


@mcp.resource("riverview://diagnostics/{cursor}")
def diagnostics_resource(cursor: str) -> Any:
    """Expose a bounded River diagnostics resource page through the MCP resource API."""
    return _safe(relay.resource_diagnostics(cursor=int(cursor), classification="river"))


@mcp.resource("riverview://cookbook/{cursor}")
def cookbook_resource(cursor: str) -> Any:
    """Expose a bounded River Cookbook resource page through the MCP resource API."""
    return _safe(relay.resource_cookbook(cursor=int(cursor), classification="river"))


@mcp.resource("riverview://capacity/{cursor}")
def capacity_resource(cursor: str) -> Any:
    """Expose a bounded River capacity resource page through the MCP resource API."""
    return _safe(relay.resource_capacity(cursor=int(cursor), classification="river"))


def main() -> None:
    """Run only over stdio; no TCP or remote listener is created."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
