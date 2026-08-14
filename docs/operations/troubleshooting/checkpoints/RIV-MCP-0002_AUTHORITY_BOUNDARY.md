<!-- Version: 0.9.3 -->
# RIV-MCP-0002 - Prohibited authority exposed

Component: RV-004.4 read-only MCP Relay.

Observed or induced signature: Tool enumeration exposes write, arbitrary SQL, filesystem, shell, secret, credential, or Undercurrent authority.

Smallest safe repair: Remove the prohibited authority and rerun live MCP tool enumeration.

Recovery verification: run `python -m riverview.mcp_health` and `python -m riverview.mcp.live_acceptance`.

Escalation boundary: stop if repair would add write authority, remote exposure, arbitrary SQL/filesystem/process access, secrets, or Undercurrent access.

Applicable version: 0.9.3.
