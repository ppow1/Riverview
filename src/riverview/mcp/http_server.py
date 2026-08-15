"""Riverview Comms Streamable HTTP entrypoint.

Version: 0.10.0

This is a transport wrapper around the existing fixed bounded MCP server. It
does not add generic writes, SQL inputs, or browser authority. The default bind
is loopback; a separately controlled deployment may place this service behind
an authenticated HTTPS ingress without changing the read model.
"""

from __future__ import annotations

import os

from riverview.mcp.server import mcp

APPLICATION_NAME = "Riverview Comms"
APPLICATION_VERSION = "0.14.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 11825


def _port() -> int:
    raw = os.environ.get("RIVERVIEW_COMMS_PORT", str(DEFAULT_PORT))
    try:
        value = int(raw)
    except ValueError as exc:
        raise SystemExit("RIV-COMMS-0001: RIVERVIEW_COMMS_PORT must be an integer.") from exc
    if not 1 <= value <= 65535:
        raise SystemExit("RIV-COMMS-0001: RIVERVIEW_COMMS_PORT is outside the valid range.")
    return value


def main() -> None:
    """Run the bounded service using the MCP Streamable HTTP transport."""
    host = os.environ.get("RIVERVIEW_COMMS_HOST", DEFAULT_HOST)
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit(
            "RIV-COMMS-0002: non-loopback binding requires an approved authenticated ingress."
        )
    mcp.settings.host = host
    mcp.settings.port = _port()
    mcp.settings.streamable_http_path = "/mcp"
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
