"""Separate Comms5 MCP entrypoint.

This is intentionally a distinct server from the Comms4 read surface.  It is
stdio by default; deployment/connector registration remains an explicit step.
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from riverview.mcp.comms5 import CONTRACT_VERSION, Comms5Error, Comms5Service

SERVER_NAME = "Riverview Comms5"
mcp = FastMCP(SERVER_NAME)
service = Comms5Service()
_GOVERNED_MUTATION_HINTS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


class FormationContractInput(BaseModel):
    """Bounded schema carrier; authority validation remains server-side."""

    model_config = ConfigDict(extra="forbid")
    repository_identity: str = ""
    repository_root: str = ""
    expected_base_sha: str = ""
    bounded_instruction: str = ""
    allowed_paths: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    evidence_requirements: list[str] = Field(default_factory=list)
    capability_name: str = ""
    action_type: str = ""
    timeout_seconds: int = 0
    write_policy: str = ""


_EMPTY_FORMATION_CONTRACT = FormationContractInput()


def _safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _request(**values: Any) -> dict[str, Any]:
    """Build the backend request without exposing an opaque MCP object schema."""
    return {key: value for key, value in values.items() if value not in (None, "")}


def _invoke(function: Any, *args: Any, **kwargs: Any) -> Any:
    """Project governed protocol errors as bounded JSON instead of stack text."""
    try:
        return _safe(function(*args, **kwargs))
    except Comms5Error as error:
        return error.as_dict()


def _transport_principal(context: Context) -> str | None:
    """Read only the server-injected Comms5 attestation, never body identity."""
    request_context = getattr(context, "request_context", None)
    request = getattr(request_context, "request", None)
    headers = getattr(request, "headers", {}) or {}
    marker = headers.get("x-riverview-comms5")
    principal = headers.get("x-riverview-comms5-principal")
    return "steward" if marker == "1" and principal == "steward" else None


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


@mcp.tool(title="Submit bounded draft", annotations=_GOVERNED_MUTATION_HINTS)
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
    return _invoke(service.submit_steward_seed, _request(
        seed_text=seed_text, idempotency_key=idempotency_key, client_id=client_id,
        client_type=client_type, client_name=client_name,
        authenticated_principal=authenticated_principal, correlation_id=correlation_id,
        client_version=client_version, protocol_version=protocol_version,
        classification=classification, causation_id=causation_id,
        specification_id=specification_id,
    ))


@mcp.tool(title="Store bounded specification reference", annotations=_GOVERNED_MUTATION_HINTS)
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
    formation_contract: FormationContractInput = _EMPTY_FORMATION_CONTRACT,
) -> Any:
    """Store a bounded specification and optional typed non-shell formation contract."""
    values = _request(
        content=content, summary=summary, idempotency_key=idempotency_key,
        client_id=client_id, client_type=client_type, client_name=client_name,
        authenticated_principal=authenticated_principal, correlation_id=correlation_id,
        client_version=client_version, protocol_version=protocol_version,
        classification=classification,
    )
    contract = formation_contract.model_dump(exclude_unset=True)
    if contract:
        values["formation_contract"] = contract
    return _invoke(service.store_specification, values)


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


@mcp.tool(title="Confirm Steward-approved draft", annotations=_GOVERNED_MUTATION_HINTS)
def comms5_confirm_and_promote_seed(
    seed_id: str,
    idempotency_key: str,
    explicit_steward_confirmation: bool,
    authenticated_principal: str,
    client_id: str,
    client_type: str,
    client_name: str,
    ctx: Context,
    client_version: str = "",
    protocol_version: str = CONTRACT_VERSION,
    correlation_id: str = "",
    classification: str = "river",
) -> Any:
    """Record explicit Steward confirmation for one existing draft.

    This bounded transition creates only the canonical objective record. It
    does not execute work, cancel work, supersede an active objective, or grant
    client authority. The server requires authenticated Steward authority and
    explicit confirmation.
    """
    return _invoke(service.confirm_and_promote_seed, {
        "seed_id": seed_id,
        "idempotency_key": idempotency_key,
        "explicit_steward_confirmation": explicit_steward_confirmation,
        "authenticated_principal": authenticated_principal,
        "client_id": client_id,
        "client_type": client_type,
        "client_name": client_name,
        "client_version": client_version,
        "protocol_version": protocol_version,
        "correlation_id": correlation_id,
        "classification": classification,
    }, transport_principal=_transport_principal(ctx))


@mcp.tool(title="Cancel draft with Steward confirmation", annotations=_GOVERNED_MUTATION_HINTS)
def comms5_cancel_draft(
    seed_id: str,
    reason: str,
    idempotency_key: str,
    explicit_steward_confirmation: bool,
    client_id: str,
    client_type: str,
    client_name: str,
    authenticated_principal: str,
    client_version: str = "",
    protocol_version: str = CONTRACT_VERSION,
    correlation_id: str = "",
    classification: str = "river",
) -> Any:
    """Append-only cancel of a draft; never cancels an objective or work order."""
    return _invoke(service.cancel_draft, _request(
        seed_id=seed_id, reason=reason, idempotency_key=idempotency_key,
        explicit_steward_confirmation=explicit_steward_confirmation,
        client_id=client_id, client_type=client_type, client_name=client_name,
        authenticated_principal=authenticated_principal, client_version=client_version,
        protocol_version=protocol_version, correlation_id=correlation_id,
        classification=classification,
    ))


@mcp.tool(title="Supersede draft with Steward confirmation", annotations=_GOVERNED_MUTATION_HINTS)
def comms5_supersede_seed(
    seed_id: str,
    replacement_seed_id: str,
    reason: str,
    idempotency_key: str,
    explicit_steward_confirmation: bool,
    client_id: str,
    client_type: str,
    client_name: str,
    authenticated_principal: str,
    client_version: str = "",
    protocol_version: str = CONTRACT_VERSION,
    correlation_id: str = "",
    classification: str = "river",
) -> Any:
    """Append an old-draft-to-new-draft replacement relation."""
    return _invoke(service.supersede_seed, _request(
        seed_id=seed_id, replacement_seed_id=replacement_seed_id, reason=reason,
        idempotency_key=idempotency_key,
        explicit_steward_confirmation=explicit_steward_confirmation,
        client_id=client_id, client_type=client_type, client_name=client_name,
        authenticated_principal=authenticated_principal, client_version=client_version,
        protocol_version=protocol_version, correlation_id=correlation_id,
        classification=classification,
    ))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
