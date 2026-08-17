"""Loopback Streamable HTTP transport for Riverview Comms5.

The public boundary remains the approved Caddy HTTPS ingress. This process is
never allowed to bind broadly; Caddy supplies authentication and proxies only
the fixed MCP path.
"""

from __future__ import annotations

import os

from riverview.mcp.comms5_server import mcp

APPLICATION_NAME = "Riverview Comms5"
APPLICATION_VERSION = "5.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 11826


def _port() -> int:
    raw = os.environ.get("RIVERVIEW_COMMS5_PORT", str(DEFAULT_PORT))
    try:
        value = int(raw)
    except ValueError as exc:
        raise SystemExit("RIV-COMMS5-0013: RIVERVIEW_COMMS5_PORT must be an integer.") from exc
    if not 1 <= value <= 65535:
        raise SystemExit("RIV-COMMS5-0013: RIVERVIEW_COMMS5_PORT is outside the valid range.")
    return value


def main() -> None:
    host = os.environ.get("RIVERVIEW_COMMS5_HOST", DEFAULT_HOST)
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("RIV-COMMS5-0014: non-loopback binding requires approved Caddy ingress.")
    mcp.settings.host = host
    mcp.settings.port = _port()
    mcp.settings.streamable_http_path = "/mcp"
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
