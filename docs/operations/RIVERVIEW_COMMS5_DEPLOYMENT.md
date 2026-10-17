# Riverview Comms5 external deployment

> **CURRENT CAMRUI/IONOGE CONNECTIONS (verified 2026-10-17):** Start with [Riverview machine connections and Comms5 recovery](RIVERVIEW_MACHINE_CONNECTIONS_AND_COMMS5_RECOVERY_2026-10-17.md). The Windows reverse-tunnel instructions below are historical and **not** the currently verified deployment. The active tunnel is the Camrui Ubuntu `riverview-comms5-tunnel.service` with a systemd host-key credential drop-in. Ionoge loopback `127.0.0.1:11826/healthz` returned HTTP 200 through the tunnel. Public Caddy/OAuth/MCP end-to-end status must be reverified separately.


Comms5 has two distinct transports:

- local STDIO: `python -m riverview.mcp.comms5_server`
- loopback Streamable HTTP: `http://127.0.0.1:11826/mcp`, started by
  `tools/powershell/mcp/Start-RiverviewComms5Http.ps1`

The approved external pattern is the existing Riverview Comms Caddy boundary.
The Comms5 route is configured separately. The authenticated bearer is the
Steward-controlled connector credential; after Caddy accepts it, Caddy
overwrites the upstream `X-Riverview-Comms5` and
`X-Riverview-Comms5-Principal: steward` attestation headers. Comms5 ignores
client-supplied principal strings and accepts promotion authority only from
that server-injected attestation.

`https://riverview-comms.ionoge.com/comms5/mcp`

It proxies to `127.0.0.1:11826`, uses separate service-held bearer variables,
and does not alter the existing Comms4 `/mcp` route.

The corrected reverse tunnel is:

`VPS 127.0.0.1:11826 -> Windows 127.0.0.1:11826`

It is launched by `tools/powershell/mcp/Start-RiverviewComms5ReverseTunnel.ps1`
with the documented `root@64.227.21.54` SSH boundary and keepalive options.
The Caddy route rewrites `/comms5/mcp` to the loopback backend `/mcp` before
proxying; without that rewrite the authenticated public route returns backend
404.

The route has now been installed and validated on the authorized Caddy host.
Authenticated external MCP initialization, notification handling, tool
enumeration, and `comms5_help` invocation pass. Comms4 remains on its original
`/mcp` route.
