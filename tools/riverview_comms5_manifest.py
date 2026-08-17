"""Callable Comms5 connector manifest derived from the authoritative MCP registry.

This module contains no credentials and performs no external registration. Names
and schemas come from the same FastMCP registry used by STDIO and HTTP.
"""

from __future__ import annotations

from typing import Any

from riverview.mcp.comms5_server import mcp

APPLICATION = "Riverview Comms5"
VERSION = "riverview-comms-contract:5.0"
ENTRYPOINT = "python -m riverview.mcp.comms5_server"
TRANSPORT = "stdio"
_REGISTERED_TOOLS = tuple(mcp._tool_manager.list_tools())
TOOLS = frozenset(tool.name for tool in _REGISTERED_TOOLS)
TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    tool.name: tool.parameters for tool in _REGISTERED_TOOLS
}
PROHIBITED = {"direct_sql", "arbitrary_filesystem", "shell", "secret_export", "self_promotion"}
