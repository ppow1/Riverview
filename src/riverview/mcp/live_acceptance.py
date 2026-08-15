"""Live stdio MCP protocol acceptance for RV-004.4/RV-008.1.

Version: 0.10.0
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REQUIRED = {
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
    "mailbox_acknowledge",
    "mailbox_claim",
    "mailbox_submit_advisory_response",
    "submit_steward_seed",
    "resource_roadmap",
    "resource_work",
    "resource_reports",
    "resource_diagnostics",
    "resource_cookbook",
    "resource_capacity",
}
PROHIBITED = {
    "enqueue",
    "execute_sql",
    "filesystem",
    "shell",
    "secret",
    "credential",
    "undercurrent",
    "write",
}
EXPECTED_RESOURCE_TEMPLATES = {
    "riverview://roadmap/{cursor}",
    "riverview://work/{cursor}",
    "riverview://reports/{cursor}",
    "riverview://diagnostics/{cursor}",
    "riverview://cookbook/{cursor}",
    "riverview://capacity/{cursor}",
}


async def _accept() -> dict[str, Any]:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "riverview.mcp.server"],
    )
    async with (
        stdio_client(params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()
        listed = await session.list_tools()
        names = {tool.name for tool in listed.tools}
        missing = sorted(REQUIRED - names)
        prohibited = sorted(name for name in names if name.lower() in PROHIBITED)
        if missing:
            raise RuntimeError(f"RIV-MCP-0001: Missing MCP tools: {missing}")
        if prohibited:
            raise RuntimeError(f"RIV-MCP-0002: Prohibited MCP tools exposed: {prohibited}")

        revision = await session.call_tool("roadmap_revision", {})
        if getattr(revision, "isError", False) or getattr(revision, "is_error", False):
            raise RuntimeError("RIV-MCP-0006: roadmap_revision tool call failed.")

        position = await session.call_tool("current_position", {})
        if getattr(position, "isError", False) or getattr(position, "is_error", False):
            raise RuntimeError("RIV-MCP-0006: current_position tool call failed.")

        mailbox = await session.call_tool(
            "mailbox_requests", {"limit": 5, "cursor": 0, "classification": "river"}
        )
        if getattr(mailbox, "isError", False) or getattr(mailbox, "is_error", False):
            raise RuntimeError("RIV-MCP-0006: mailbox_requests tool call failed.")

        cookbook = await session.call_tool("troubleshooting_cookbook", {"limit": 5})
        if getattr(cookbook, "isError", False) or getattr(cookbook, "is_error", False):
            raise RuntimeError("RIV-MCP-0004: troubleshooting_cookbook tool call failed.")

        resource_page = await session.call_tool(
            "resource_roadmap", {"limit": 1, "cursor": 0, "classification": "river"}
        )
        if getattr(resource_page, "isError", False) or getattr(resource_page, "is_error", False):
            raise RuntimeError("RIV-MCP-0006: resource_roadmap tool call failed.")
        resources = await session.list_resources()
        templates = await session.list_resource_templates()
        template_names = {item.uriTemplate for item in templates.resourceTemplates}
        resource_count = len(resources.resources) + len(template_names)
        if template_names != EXPECTED_RESOURCE_TEMPLATES:
            raise RuntimeError("RIV-MCP-0001: bounded MCP resource templates are incomplete.")

        return {
            "status": "healthy",
            "transport": "stdio",
            "authority": "read_only_plus_bounded_mailbox_writes",
            "tool_count": len(names),
            "required_tools_present": True,
            "prohibited_tools_present": False,
            "resource_templates_observed": resource_count,
            "remote_listener_created": False,
        }


def main() -> None:
    print(json.dumps(asyncio.run(_accept()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
