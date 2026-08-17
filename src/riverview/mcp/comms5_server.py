"""Separate Comms5 MCP entrypoint.

This is intentionally a distinct server from the Comms4 read surface.  It is
stdio by default; deployment/connector registration remains an explicit step.
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from riverview.mcp.comms5 import CONTRACT_VERSION, Comms5Service

SERVER_NAME = "Riverview Comms5"
mcp = FastMCP(SERVER_NAME)
service = Comms5Service()


def _safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _request(**values: Any) -> dict[str, Any]:
    """Build the backend request without exposing an opaque MCP object schema."""
    return {key: value for key, value in values.items() if value not in (None, "")}


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
def comms5_submit_steward_seed(
    seed_text: str,
    idempotency_key: str,
    client_id: str,
    client_type: str,
    client_name: str,
    authenticated_principal: str,
    correlation_id: str = "",
    client_version: str = "",
    protocol_version: str = CONTRACT_VERSION,
    classification: str = "river",
    causation_id: str = "",
    specification_id: str = "",
) -> Any:
    """Submit a bounded draft; this never promotes or creates work."""
    return _safe(service.submit_steward_seed(_request(
        seed_text=seed_text, idempotency_key=idempotency_key, client_id=client_id,
        client_type=client_type, client_name=client_name,
        authenticated_principal=authenticated_principal, correlation_id=correlation_id,
        client_version=client_version, protocol_version=protocol_version,
        classification=classification, causation_id=causation_id,
        specification_id=specification_id,
    )))


@mcp.tool()
def comms5_store_specification(
    content: str,
    summary: str,
    idempotency_key: str,
    client_id: str,
    client_type: str,
    client_name: str,
    authenticated_principal: str,
    correlation_id: str = "",
    client_version: str = "",
    protocol_version: str = CONTRACT_VERSION,
    classification: str = "river",
) -> Any:
    """Store a bounded large specification as an authoritative reference."""
    return _safe(service.store_specification(_request(
        content=content, summary=summary, idempotency_key=idempotency_key,
        client_id=client_id, client_type=client_type, client_name=client_name,
        authenticated_principal=authenticated_principal, correlation_id=correlation_id,
        client_version=client_version, protocol_version=protocol_version,
        classification=classification,
    )))


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
def comms5_confirm_and_promote_seed(
    seed_id: str,
    idempotency_key: str,
    explicit_steward_confirmation: bool,
    authenticated_principal: str,
) -> Any:
    """Promote only with explicit Steward authorization through the canonical store."""
    return _safe(service.confirm_and_promote_seed({
        "seed_id": seed_id,
        "idempotency_key": idempotency_key,
        "explicit_steward_confirmation": explicit_steward_confirmation,
        "authenticated_principal": authenticated_principal,
    }))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
