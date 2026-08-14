<!-- Version: 0.9.3 -->
# RIV-MCP-0006 - MCP transport acceptance failure

Component: RV-004.4 read-only MCP Relay.

Observed or induced signature: The local stdio MCP server fails initialization, tool listing, or an allowed tool call.

Smallest safe repair: Repair only the local MCP protocol seam and replay the full acceptance chain.

Recovery verification: run `python -m riverview.mcp_health` and `python -m riverview.mcp.live_acceptance`.

Escalation boundary: stop if repair would add write authority, remote exposure, arbitrary SQL/filesystem/process access, secrets, or Undercurrent access.

Applicable version: 0.9.3.
