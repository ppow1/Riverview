"""Live stdio MCP protocol acceptance for RV-004.4.

Version: 0.9.11
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

            cookbook = await session.call_tool("troubleshooting_cookbook", {"limit": 5})
            if getattr(cookbook, "isError", False) or getattr(cookbook, "is_error", False):
                raise RuntimeError("RIV-MCP-0004: troubleshooting_cookbook tool call failed.")

            return {
                "status": "healthy",
                "transport": "stdio",
                "authority": "read_only",
                "tool_count": len(names),
                "required_tools_present": True,
                "prohibited_tools_present": False,
                "remote_listener_created": False,
            }


def main() -> None:
    print(json.dumps(asyncio.run(_accept()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()