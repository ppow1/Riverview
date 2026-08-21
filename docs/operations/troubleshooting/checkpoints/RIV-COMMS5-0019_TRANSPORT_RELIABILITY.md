# RIV-COMMS5-0019 — Comms5 transport reliability boundary

## Failure signature

An authenticated MCP call intermittently times out while an identical retry
succeeds. Grace/CME health does not establish that the public return path is
healthy.

## Layer-isolation procedure

Use `tools/diagnostics/measure_comms5_transport.py` with MCP `initialize`
only. Test Windows loopback, the VPS loopback through the reverse forward, and
the authenticated Caddy route separately. Preserve the request ID and
timestamps; never record bearer values or MCP bodies. Review Caddy upstream
cancellation/error records and Comms5 diagnostic JSONL events together.

## Evidence interpretation

The original client timeout is independent of server rejection. A request in
Caddy logs with upstream dispatch but `context canceled` reached Caddy and the
upstream boundary; it is not evidence of a Grace failure. A Comms5
`http.received` event without `http.sent` means the server response did not
complete. A completed server response with a client timeout is a
`CLIENT/RETURN-PATH TIMEOUT AFTER SERVER COMMIT` and may be retried only when
the operation is idempotent or has an approved idempotency key.

## Repair rule

Repair only the first demonstrated divergent layer. Do not redesign Grace,
bypass Caddy or the tunnel, or tune every timeout layer without evidence. If a
client reports a timeout and no matching request ID reaches Caddy, classify the
remaining issue as upstream/client-boundary uncertainty rather than mutating
Riverview.
