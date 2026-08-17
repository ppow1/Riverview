"""MCP action-scan compatibility checks for the public Comms5 projection."""

from __future__ import annotations

import re

from riverview.mcp.comms5_server import mcp


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
    assert len(tools) == 15
    assert {tool.name for tool in tools} >= {"comms5_help", "comms5_seed_lineage", "comms5_cancel_draft", "comms5_supersede_seed"}

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


def test_mutating_comms5_tools_do_not_expose_opaque_request_objects() -> None:
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}
    for name in (
        "comms5_submit_steward_seed",
        "comms5_store_specification",
        "comms5_confirm_and_promote_seed",
    ):
        properties = tools[name].parameters["properties"]
        assert "request" not in properties
        assert properties
