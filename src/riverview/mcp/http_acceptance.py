"""Protocol acceptance for the Riverview Comms Streamable HTTP boundary.

Version: 0.10.0
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from riverview.mcp.http_server import APPLICATION_NAME, APPLICATION_VERSION

REQUIRED = {
    "roadmap_revision",
    "waypoints",
    "current_position",
    "work_order_status",
    "completed_work_reports",
    "recent_diagnostic_events",
    "troubleshooting_cookbook",
    "resource_roadmap",
    "resource_work",
    "resource_reports",
    "resource_diagnostics",
    "resource_cookbook",
    "resource_capacity",
}
PROHIBITED_FRAGMENTS = {
    "sql",
    "filesystem",
    "shell",
    "process",
    "secret",
    "credential",
    "undercurrent",
    "write",
    "enqueue",
}


async def _accept(endpoint: str) -> dict[str, Any]:
    async with (
        streamable_http_client(endpoint) as (read_stream, write_stream, _),
        ClientSession(read_stream, write_stream) as session,
    ):
            await session.initialize()
            result = await session.list_tools()
            names = {tool.name for tool in result.tools}
            missing = sorted(REQUIRED - names)
            prohibited = sorted(
                name for name in names if any(fragment in name.lower() for fragment in PROHIBITED_FRAGMENTS)
            )
            if missing:
                raise RuntimeError(f"RIV-COMMS-0005: missing bounded tools: {missing}")
            if prohibited:
                raise RuntimeError(f"RIV-COMMS-0006: prohibited tools exposed: {prohibited}")
            for tool_name, arguments in (
                ("current_position", {}),
                ("roadmap_revision", {}),
                ("work_order_status", {"limit": 5}),
                ("recent_diagnostic_events", {"limit": 5}),
                ("troubleshooting_cookbook", {"limit": 5}),
            ):
                response = await session.call_tool(tool_name, arguments)
                if getattr(response, "isError", False) or getattr(response, "is_error", False):
                    raise RuntimeError(f"RIV-COMMS-0007: tool call failed: {tool_name}")
            return {
                "status": "healthy",
                "application": APPLICATION_NAME,
                "version": APPLICATION_VERSION,
                "transport": "streamable-http",
                "authority": "read_only",
                "tool_count": len(names),
                "required_tools_present": True,
                "prohibited_tools_present": False,
                "endpoint": endpoint,
            }


def main() -> None:
    endpoint = os.environ.get("RIVERVIEW_COMMS_ENDPOINT", "http://127.0.0.1:11825/mcp")
    print(json.dumps(asyncio.run(_accept(endpoint)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
