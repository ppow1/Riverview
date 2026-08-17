"""Separate Comms5 MCP entrypoint.

This is intentionally a distinct server from the Comms4 read surface.  It is
stdio by default; deployment/connector registration remains an explicit step.
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from riverview.mcp.comms5 import Comms5Service

SERVER_NAME = "Riverview Comms5"
mcp = FastMCP(SERVER_NAME)
service = Comms5Service()


def _safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


@mcp.tool()
def comms5_contract_info() -> Any:
    """Return the versioned Comms5 contract identity."""
    return _safe(service.contract_info())


@mcp.tool()
def comms5_help() -> Any:
    """Return machine-readable Comms5 discovery and safe-use guidance."""
    return _safe(service.help())


@mcp.tool()
def comms5_capabilities() -> Any:
    """List Comms5 operations, limits, and authorization classes."""
    return _safe(service.capabilities())


@mcp.tool()
def comms5_describe_operation(operation: str) -> Any:
    """Describe one Comms5 operation."""
    return _safe(service.describe_operation(operation))


@mcp.tool()
def comms5_examples() -> Any:
    """Return bounded examples for public operations."""
    return _safe(service.examples())


@mcp.tool()
def comms5_submit_steward_seed(request: dict[str, Any]) -> Any:
    """Submit a bounded draft; this never promotes or creates work."""
    return _safe(service.submit_steward_seed(request))


@mcp.tool()
def comms5_store_specification(request: dict[str, Any]) -> Any:
    """Store a bounded large specification as an authoritative reference."""
    return _safe(service.store_specification(request))


@mcp.tool()
def comms5_seed_status(seed_id: str) -> Any:
    """Return bounded seed status metadata."""
    return _safe(service.seed_status(seed_id))


@mcp.tool()
def comms5_seed_lineage(seed_id: str) -> Any:
    """Return authoritative bounded seed lineage."""
    return _safe(service.seed_lineage(seed_id))


@mcp.tool()
def comms5_objective_status(objective_id: str) -> Any:
    """Return bounded objective/stage/CME/work state."""
    return _safe(service.objective_status(objective_id))


@mcp.tool()
def comms5_cme_status() -> Any:
    """Return the authoritative CME runtime projection."""
    return _safe(service.cme_status())


@mcp.tool()
def comms5_recent_steward_submissions(limit: int = 20) -> Any:
    """Return bounded recent submission metadata."""
    return _safe(service.recent_steward_submissions(limit))


@mcp.tool()
def comms5_confirm_and_promote_seed(request: dict[str, Any]) -> Any:
    """Promote only with explicit Steward authorization through the canonical store."""
    return _safe(service.confirm_and_promote_seed(request))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
