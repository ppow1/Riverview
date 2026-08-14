<!-- Version: 0.9.3 -->
# RIV-MCP-0001 - Missing read surface

Component: RV-004.4 read-only MCP Relay.

Observed or induced signature: Required fixed read tool or projection is missing.

Smallest safe repair: Restore only the missing fixed read adapter, then rerun read-model and live MCP acceptance.

Recovery verification: run `python -m riverview.mcp_health` and `python -m riverview.mcp.live_acceptance`.

Escalation boundary: stop if repair would add write authority, remote exposure, arbitrary SQL/filesystem/process access, secrets, or Undercurrent access.

Applicable version: 0.9.3.
