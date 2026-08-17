# Riverview Comms5 external deployment

Comms5 has two distinct transports:

- local STDIO: `python -m riverview.mcp.comms5_server`
- loopback Streamable HTTP: `http://127.0.0.1:11826/mcp`, started by
  `tools/powershell/mcp/Start-RiverviewComms5Http.ps1`

The approved external pattern is the existing Riverview Comms Caddy boundary.
The Comms5 route is configured separately as:

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
