"""Separate Comms5 MCP entrypoint.

This is intentionally a distinct server from the Comms4 read surface.  It is
stdio by default; deployment/connector registration remains an explicit step.
"""

from __future__ import annotations

import json
import time
from typing import Annotated, Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from riverview.mcp.comms5 import CONTRACT_VERSION, Comms5Error, Comms5Service
from riverview.mcp.transport_diagnostics import record

SERVER_NAME = "Riverview Comms5"
mcp = FastMCP(SERVER_NAME)
service = Comms5Service()
_GOVERNED_MUTATION_HINTS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
_READ_ONLY_HINTS = ToolAnnotations(
    readOnlyHint=True,
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


class ResourcePolicyParameters(BaseModel):
    """Closed schema for the existing resource-policy parameter contract."""

    model_config = ConfigDict(extra="forbid")
    target_seat: str = ""
    priority_order: list[str] = Field(default_factory=list)
    fallback: bool = True
    consume_reset: bool = False


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


def _server_request_id(context: Context) -> str:
    request_context = getattr(context, "request_context", None)
    request = getattr(request_context, "request", None)
    scope = getattr(request, "scope", {}) or {}
    return str(scope.get("riverview_request_id", ""))


@mcp.tool(annotations=_READ_ONLY_HINTS)
def comms5_contract_info(ctx: Context) -> Any:
    """Return the versioned Comms5 contract identity."""
    request_id = _server_request_id(ctx)
    started = time.perf_counter()
    record("mcp.dispatch", request_id, started=started, operation="contract_info", phase="dispatch")
    result = _safe(service.contract_info())
    record("mcp.complete", request_id, started=started, operation="contract_info", phase="tool")
    return result


@mcp.tool(annotations=_READ_ONLY_HINTS)
def comms5_help() -> Any:
    """Return machine-readable Comms5 discovery and safe-use guidance."""
    return _safe(service.help())


@mcp.tool(annotations=_READ_ONLY_HINTS)
def comms5_capabilities() -> Any:
    """List Comms5 operations, limits, and authorization classes."""
    return _safe(service.capabilities())


@mcp.tool(annotations=_READ_ONLY_HINTS)
def comms5_describe_operation(operation: str) -> Any:
    """Describe one Comms5 operation."""
    return _safe(service.describe_operation(operation))


@mcp.tool(annotations=_READ_ONLY_HINTS)
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


@mcp.tool(
    title="Read bounded seed status",
    annotations=_READ_ONLY_HINTS,
)
def comms5_seed_status(seed_id: str) -> Any:
    """Return bounded seed, specification, objective linkage, and promotion status metadata."""
    return _safe(service.seed_status(seed_id))


@mcp.tool(annotations=_READ_ONLY_HINTS)
def comms5_seed_lineage(seed_id: str) -> Any:
    """Return authoritative bounded seed lineage."""
    return _safe(service.seed_lineage(seed_id))


@mcp.tool(title="Read bounded objective status", annotations=_READ_ONLY_HINTS)
def comms5_objective_status(objective_id: str) -> Any:
    """Return bounded objective, stages, authority, intent, and work metadata."""
    return _safe(service.objective_status(objective_id))


@mcp.tool(annotations=_READ_ONLY_HINTS)
def comms5_cme_status(ctx: Context) -> Any:
    """Return the authoritative CME runtime projection."""
    request_id = _server_request_id(ctx)
    started = time.perf_counter()
    record("mcp.dispatch", request_id, started=started, operation="cme_status", phase="dispatch")
    result = _safe(service.cme_status(request_id))
    record("mcp.complete", request_id, started=started, operation="cme_status", phase="tool")
    return result


@mcp.tool(annotations=_READ_ONLY_HINTS)
def comms5_recent_steward_submissions(limit: int = 20) -> Any:
    """Return bounded recent submission metadata."""
    return _safe(service.recent_steward_submissions(limit))


@mcp.tool(annotations=_READ_ONLY_HINTS)
def comms5_transport_probe(probe_id: str, ctx: Context) -> Any:
    """Run one read-only end-to-end transport correlation probe."""
    return _safe(service.transport_probe(probe_id, _server_request_id(ctx)))


@mcp.tool(annotations=_READ_ONLY_HINTS)
def comms5_resource_policy_status() -> Any:
    """Return the durable Codex resource policy and its audit projection."""
    return _invoke(service.resource_policy_status)


@mcp.tool(title="Set resource policy", annotations=_GOVERNED_MUTATION_HINTS)
def comms5_set_resource_policy(
    mode: str,
    parameters: ResourcePolicyParameters,
    explicit_steward_confirmation: bool,
    ctx: Context,
    rationale: str = "",
    expected_revision: int = -1,
) -> Any:
    """Set policy only from authenticated Steward transport attestation."""
    parameters_value = parameters.model_dump(exclude_unset=True)
    if parameters_value.get("target_seat") == "":
        parameters_value.pop("target_seat")
    return _invoke(
        service.set_resource_policy,
        {"mode": mode, "parameters": parameters_value, "explicit_steward_confirmation": explicit_steward_confirmation, "rationale": rationale, "expected_revision": None if expected_revision == -1 else expected_revision, "source_request_id": _server_request_id(ctx)},
        transport_principal=_transport_principal(ctx),
    )


@mcp.tool(title="Lock resource policy", annotations=_GOVERNED_MUTATION_HINTS)
def comms5_set_resource_policy_lock(
    locked: bool,
    explicit_steward_confirmation: bool,
    ctx: Context,
    rationale: str = "",
) -> Any:
    """Lock or unlock policy only from authenticated Steward transport attestation."""
    return _invoke(
        service.set_resource_policy_lock,
        locked,
        transport_principal=_transport_principal(ctx),
        explicit_steward_confirmation=explicit_steward_confirmation,
        rationale=rationale,
    )


@mcp.tool(title="Confirm Steward-approved draft", annotations=_GOVERNED_MUTATION_HINTS)
def comms5_confirm_and_promote_seed(
    seed_id: Annotated[str, Field(description="Exact eligible specification-backed draft ID to approve.")],
    idempotency_key: Annotated[str, Field(description="Stable retry key for this one approval transition.")],
    explicit_steward_confirmation: Annotated[bool, Field(description="Pat's explicit approval of this exact draft; must be true.")],
    client_id: Annotated[str, Field(description="Calling client provenance; not an authority claim.")],
    client_type: Annotated[str, Field(description="Calling client provenance; not an authority claim.")],
    client_name: Annotated[str, Field(description="Calling client provenance; not an authority claim.")],
    ctx: Context,
    client_version: str = "",
    protocol_version: str = CONTRACT_VERSION,
    correlation_id: str = "",
    classification: str = "river",
) -> Any:
    """Record Pat's approval and atomically materialize one exact draft objective.

    This governed write verifies transport-attested Steward authority, explicit
    confirmation, the eligible specification ID/version/hash, and idempotency,
    then records bounded authority and creates the canonical objective record.
    It does not execute Codex or other work, run shell commands, cancel or
    supersede work, grant arbitrary authority, or bypass Grace, Relay,
    capability, or reconciliation gates. Client identity is provenance only.
    """
    return _invoke(service.confirm_and_promote_seed, {
        "seed_id": seed_id,
        "idempotency_key": idempotency_key,
        "explicit_steward_confirmation": explicit_steward_confirmation,
        # ClientContext retains a provenance field for protocol compatibility;
        # it is deliberately not exposed as a promotion authority input.
        "authenticated_principal": "untrusted-client-provenance",
        "client_id": client_id,
        "client_type": client_type,
        "client_name": client_name,
        "client_version": client_version,
        "protocol_version": protocol_version,
        "correlation_id": correlation_id,
        "classification": classification,
    }, transport_principal=_transport_principal(ctx))


@mcp.tool(title="Form and queue approved work", annotations=_GOVERNED_MUTATION_HINTS)
def comms5_form_and_queue_work(
    objective_id: Annotated[str, Field(description="Exact already-promoted objective ID; scope is derived server-side.")],
    stage_id: Annotated[str, Field(description="Exact ready stage ID bound to the objective.")],
    authority_id: Annotated[str, Field(description="Exact active Steward authority grant ID bound to the objective and stage.")],
    idempotency_key: Annotated[str, Field(description="Stable retry key for this one formation and enqueue operation.")],
    explicit_steward_confirmation: Annotated[bool, Field(description="Explicit Steward approval to form and enqueue this existing approved lineage; must be true.")],
    client_id: str,
    client_type: str,
    client_name: str,
    ctx: Context,
    client_version: str = "",
    protocol_version: str = CONTRACT_VERSION,
    correlation_id: str = "",
    classification: str = "river",
) -> Any:
    """Form the approved typed intent and enqueue exactly one work order."""
    return _invoke(service.form_and_queue_work, {
        "objective_id": objective_id,
        "stage_id": stage_id,
        "authority_id": authority_id,
        "idempotency_key": idempotency_key,
        "explicit_steward_confirmation": explicit_steward_confirmation,
        "client_id": client_id,
        "client_type": client_type,
        "client_name": client_name,
        "authenticated_principal": "untrusted-client-provenance",
        "client_version": client_version,
        "protocol_version": protocol_version,
        "correlation_id": correlation_id,
        "classification": classification,
    }, transport_principal=_transport_principal(ctx))


@mcp.tool(title="Revalidate approved work base", annotations=_GOVERNED_MUTATION_HINTS)
def comms5_revalidate_and_queue_work(
    work_order_id: Annotated[str, Field(description="Exact preserved failed work order with RIV-EXE-0008 stale-base evidence.")],
    idempotency_key: Annotated[str, Field(description="Stable retry key for this one base revalidation and successor attempt.")],
    explicit_steward_confirmation: Annotated[bool, Field(description="Pat's narrow confirmation of the verified new base binding; must be true.")],
    client_id: Annotated[str, Field(description="Calling client provenance; not an authority claim.")],
    client_type: Annotated[str, Field(description="Calling client provenance; not an authority claim.")],
    client_name: Annotated[str, Field(description="Calling client provenance; not an authority claim.")],
    ctx: Context,
    client_version: str = "",
    protocol_version: str = CONTRACT_VERSION,
    correlation_id: str = "",
    classification: str = "river",
    infrastructure_repair_evidence: list[str] = [],
) -> Any:
    """Revalidate one stale approved base and queue one bounded successor.

    This preserves the original failed attempt and exact authority scope. It
    never widens paths, changes the capability, or executes Codex; material
    repository drift fails closed for renewed specification approval.
    """
    return _invoke(service.revalidate_and_queue_work, {
        "work_order_id": work_order_id,
        "idempotency_key": idempotency_key,
        "explicit_steward_confirmation": explicit_steward_confirmation,
        "client_id": client_id,
        "client_type": client_type,
        "client_name": client_name,
        "authenticated_principal": "untrusted-client-provenance",
        "client_version": client_version,
        "protocol_version": protocol_version,
        "correlation_id": correlation_id,
        "classification": classification,
        "infrastructure_repair_evidence": infrastructure_repair_evidence,
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


@mcp._mcp_server.list_tools()
async def _list_tools_with_oauth_security_schemes() -> list[Any]:
    """Advertise the OAuth requirement on every authenticated Comms5 tool."""
    tools = await mcp.list_tools()
    for tool in tools:
        # OpenAI's ChatGPT extension currently consumes this top-level field;
        # MCP's Pydantic Tool model permits protocol extensions.
        tool.securitySchemes = [{"type": "oauth2", "scopes": ["comms5"]}]
    return tools


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
