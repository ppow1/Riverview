<!-- Version: 0.9.3 -->
# RIV-MCP-0005 - Unbounded query request

Component: RV-004.4 read-only MCP Relay.

Observed or induced signature: A requested retrieval limit exceeds the declared maximum.

Smallest safe repair: Clamp to the declared maximum and rerun bounded-limit acceptance.

Recovery verification: run `python -m riverview.mcp_health` and `python -m riverview.mcp.live_acceptance`.

Escalation boundary: stop if repair would add write authority, remote exposure, arbitrary SQL/filesystem/process access, secrets, or Undercurrent access.

Applicable version: 0.9.3.
