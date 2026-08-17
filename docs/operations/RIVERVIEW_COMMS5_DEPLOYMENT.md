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

At the time of this revision, the repository and local loopback service are
ready, but the authorized Caddy host could not be reached from the deployment
environment. The public route therefore remains deployment-required until an
authorized operator installs and validates
`config/riverview-comms5-ingress.Caddyfile.example` on the existing Caddy host.
Do not tell a client that the public URL is live until authenticated external
MCP initialization and `tools/list` pass.
