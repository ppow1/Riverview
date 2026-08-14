<!-- Version: 0.9.3 -->
# RIV-MCP-0003 - PostgreSQL read failure

Component: RV-004.4 read-only MCP Relay.

Observed or induced signature: A fixed MCP read cannot retrieve authoritative PostgreSQL state.

Smallest safe repair: Repair the smallest database connectivity/schema seam; do not add file-state fallback authority.

Recovery verification: run `python -m riverview.mcp_health` and `python -m riverview.mcp.live_acceptance`.

Escalation boundary: stop if repair would add write authority, remote exposure, arbitrary SQL/filesystem/process access, secrets, or Undercurrent access.

Applicable version: 0.9.3.
