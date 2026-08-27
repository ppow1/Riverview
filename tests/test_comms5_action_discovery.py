"""MCP action-scan compatibility checks for the public Comms5 projection."""

from __future__ import annotations

import re

from riverview.mcp.comms5 import Comms5Service
from riverview.mcp.comms5_server import mcp
from tools.riverview_comms5_manifest import TOOL_SCHEMAS, TOOLS


def _walk_schema(value: object) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(_walk_schema(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_schema(child))
    return found


def test_comms5_tools_have_chatgpt_discoverable_schemas() -> None:
    tools = mcp._tool_manager.list_tools()
    expected = {
        "comms5_contract_info", "comms5_help", "comms5_capabilities",
        "comms5_describe_operation", "comms5_examples", "comms5_submit_steward_seed",
        "comms5_store_specification", "comms5_seed_status", "comms5_seed_lineage",
        "comms5_objective_status", "comms5_cme_status", "comms5_recent_steward_submissions",
        "comms5_transport_probe",
        "comms5_confirm_and_promote_seed", "comms5_form_and_queue_work", "comms5_revalidate_and_queue_work", "comms5_cancel_draft", "comms5_supersede_seed",
        "comms5_resource_policy_status", "comms5_set_resource_policy", "comms5_set_resource_policy_lock",
    }
    assert {tool.name for tool in tools} == expected
    assert TOOLS == expected
    assert set(TOOL_SCHEMAS) == expected

    for tool in tools:
        assert re.fullmatch(r"[A-Za-z0-9_.-]+", tool.name)
        assert tool.description and tool.description.strip()
        schema = tool.parameters
        assert schema.get("type") == "object"
        properties = schema.get("properties")
        assert isinstance(properties, dict)
        required = schema.get("required", [])
        assert isinstance(required, list)
        assert set(required) <= set(properties)
        for fragment in _walk_schema(schema):
            assert "anyOf" not in fragment
            assert "oneOf" not in fragment
            assert "allOf" not in fragment
            assert fragment.get("additionalProperties") is not True


def test_mutating_comms5_tools_publish_flat_authoritative_schemas() -> None:
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}
    expected = {
        "comms5_submit_steward_seed": {"seed_text", "idempotency_key", "client_id", "client_type", "client_name", "authenticated_principal", "correlation_id", "client_version", "protocol_version", "classification", "causation_id", "specification_id"},
            "comms5_store_specification": {"content", "summary", "idempotency_key", "client_id", "client_type", "client_name", "authenticated_principal", "correlation_id", "client_version", "protocol_version", "classification", "formation_contract"},
        "comms5_confirm_and_promote_seed": {"seed_id", "idempotency_key", "explicit_steward_confirmation", "client_id", "client_type", "client_name", "client_version", "protocol_version", "correlation_id", "classification"},
        "comms5_form_and_queue_work": {"objective_id", "stage_id", "authority_id", "idempotency_key", "explicit_steward_confirmation", "client_id", "client_type", "client_name", "client_version", "protocol_version", "correlation_id", "classification"},
        "comms5_revalidate_and_queue_work": {"work_order_id", "idempotency_key", "explicit_steward_confirmation", "client_id", "client_type", "client_name", "client_version", "protocol_version", "correlation_id", "classification", "infrastructure_repair_evidence"},
        "comms5_cancel_draft": {"seed_id", "reason", "idempotency_key", "explicit_steward_confirmation", "client_id", "client_type", "client_name", "authenticated_principal", "client_version", "protocol_version", "correlation_id", "classification"},
        "comms5_supersede_seed": {"seed_id", "replacement_seed_id", "reason", "idempotency_key", "explicit_steward_confirmation", "client_id", "client_type", "client_name", "authenticated_principal", "client_version", "protocol_version", "correlation_id", "classification"},
    }
    required = {
        "comms5_submit_steward_seed": {"seed_text", "idempotency_key", "client_id", "client_type", "client_name", "authenticated_principal"},
        "comms5_store_specification": {"content", "summary", "idempotency_key", "client_id", "client_type", "client_name", "authenticated_principal"},
        "comms5_confirm_and_promote_seed": {"seed_id", "idempotency_key", "explicit_steward_confirmation", "client_id", "client_type", "client_name"},
        "comms5_form_and_queue_work": {"objective_id", "stage_id", "authority_id", "idempotency_key", "explicit_steward_confirmation", "client_id", "client_type", "client_name"},
        "comms5_revalidate_and_queue_work": {"work_order_id", "idempotency_key", "explicit_steward_confirmation", "client_id", "client_type", "client_name"},
        "comms5_cancel_draft": {"seed_id", "reason", "idempotency_key", "explicit_steward_confirmation", "client_id", "client_type", "client_name", "authenticated_principal"},
        "comms5_supersede_seed": {"seed_id", "replacement_seed_id", "reason", "idempotency_key", "explicit_steward_confirmation", "client_id", "client_type", "client_name", "authenticated_principal"},
    }
    for name, expected_properties in expected.items():
        properties = tools[name].parameters["properties"]
        assert "request" not in properties
        assert set(properties) == expected_properties
        assert set(tools[name].parameters.get("required", [])) == required[name]
        assert set(TOOL_SCHEMAS[name]["properties"]) == expected_properties


def test_promotion_publishes_non_destructive_idempotent_safety_hints() -> None:
    tool = next(tool for tool in mcp._tool_manager.list_tools() if tool.name == "comms5_confirm_and_promote_seed")
    assert tool.title == "Confirm Steward-approved draft"
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is False
    assert tool.annotations.destructiveHint is False
    assert tool.annotations.idempotentHint is True
    assert tool.annotations.openWorldHint is False


def test_stale_base_revalidation_publishes_non_destructive_idempotent_safety_hints() -> None:
    tool = next(tool for tool in mcp._tool_manager.list_tools() if tool.name == "comms5_revalidate_and_queue_work")
    assert tool.title == "Revalidate approved work base"
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is False
    assert tool.annotations.destructiveHint is False
    assert tool.annotations.idempotentHint is True
    assert tool.annotations.openWorldHint is False


def test_status_reads_publish_explicit_read_only_safety_hints() -> None:
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}
    for name in (
        "comms5_seed_status",
        "comms5_seed_lineage",
        "comms5_objective_status",
        "comms5_cme_status",
        "comms5_recent_steward_submissions",
        "comms5_transport_probe",
        "comms5_resource_policy_status",
    ):
        annotations = tools[name].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False
        assert annotations.idempotentHint is True
        assert annotations.openWorldHint is False


def test_objective_and_seed_status_are_the_bounded_preflight_reads() -> None:
    objective = Comms5Service().describe_operation("objective_status")
    seed = Comms5Service().describe_operation("seed_status")
    assert objective["authorization"] == "READ_ONLY"
    assert seed["authorization"] == "READ_ONLY"
    assert objective["required"] == ["objective_id"]
    assert seed["required"] == ["seed_id"]
    assert "objective, stages, authority, intent, and work" in objective["description"]
    assert seed["description"] == "Return bounded seed, specification, objective linkage, and promotion status metadata."


def test_seed_status_has_explicit_bounded_read_title_and_description() -> None:
    tool = next(tool for tool in mcp._tool_manager.list_tools() if tool.name == "comms5_seed_status")
    assert tool.title == "Read bounded seed status"
    assert tool.description == "Return bounded seed, specification, objective linkage, and promotion status metadata."


def test_public_discovery_describes_typed_formation_and_durable_authority() -> None:
    from riverview.mcp.comms5 import Comms5Service

    service = Comms5Service()
    store = service.describe_operation("store_specification")
    promote = service.describe_operation("confirm_and_promote_seed")
    assert store["optional"] == ["formation_contract"]
    assert "typed formation_contract" in store["description"]
    assert "bounded_write" in store["description"]
    assert "durable bounded Steward authority" in promote["description"]
    assert "exact specification version/hash" in promote["description"]
    assert "canonical objective" in promote["description"]
    assert "does not execute work" in promote["description"]
    discovery = service.help()
    assert "formation_contract" in discovery["examples"]["store_specification"]


def test_promotion_schema_excludes_non_authoritative_body_principal() -> None:
    tool = next(tool for tool in mcp._tool_manager.list_tools() if tool.name == "comms5_confirm_and_promote_seed")
    properties = tool.parameters["properties"]
    assert "authenticated_principal" not in properties
    assert "authenticated_principal" not in tool.parameters["required"]
    assert "not an authority claim" in properties["client_id"]["description"]
    assert "must be true" in properties["explicit_steward_confirmation"]["description"]
