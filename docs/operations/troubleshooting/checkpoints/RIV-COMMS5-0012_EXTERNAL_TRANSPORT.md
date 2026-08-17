# RIV-COMMS5-0012 — External MCP transport boundary

## Symptom

Comms5 works over local STDIO, but no externally connectable MCP endpoint can
initialize or enumerate tools.

## Probe

Verify the only local owner of `127.0.0.1:11826`, initialize the loopback
Streamable HTTP service at `/mcp`, then validate the approved Caddy hostname,
HTTPS certificate, bearer rejection, authenticated MCP initialization, and
`tools/list`. Compare the route with the unchanged Comms4 `/mcp` route.

## Repair

Start `comms5_http_server`, add the exact `/comms5/mcp` Caddy route beside the
existing Comms4 route, validate/reload Caddy through the approved host owner,
and keep both credential pairs separate and out of source.

## Verification

The public URL must be the approved hostname plus `/comms5/mcp`; authenticated
MCP initialization and tool enumeration must pass externally. Local STDIO is
not external acceptance. If the approved proxy host cannot be reached, stop
at deployment-required and do not claim a public endpoint.
