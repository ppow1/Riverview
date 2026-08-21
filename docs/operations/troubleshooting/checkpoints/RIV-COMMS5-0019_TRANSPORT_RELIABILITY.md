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

## External / ChatGPT correlation procedure

Use the read-only `comms5_transport_probe` operation with a fresh opaque
`probe_id`, for example `chatgpt-20260820-230000-001`. The caller does not need
to set an HTTP header. Comms5 creates the server request ID at HTTP receipt,
associates it with the supplied probe ID, performs `SELECT 1`, and records
dispatch, database, tool-completion, response-serialization, and response-send
events. Query afterward with:

```powershell
.venv\Scripts\python.exe tools\diagnostics\query_comms5_transport_probe.py <probe_id>
```

Interpretation:

- no server record: the request probably failed before Comms5;
- receipt without completion: investigate Comms5/backend execution;
- server completion with Caddy cancellation: client/return-path disconnect;
- Caddy completion with a ChatGPT timeout: external/client session or
  interpretation issue remains likely.

When ChatGPT reports a timeout, preserve that exact probe ID and query the
local evidence before retrying. Do not immediately retry with another ID. If a
retry is necessary, use a new attempt ID and retain both records. Run only a
bounded sequence of approximately ten probes, then stop if no failure occurs.

## Ordinary-read fallback

If OpenAI intercepts `comms5_transport_probe` before connector execution, record
the separate class `OPENAI_PRE_CONNECTOR_INTERCEPTION`; that event has no
Riverview request. Do not bypass the safety gate. Use the already-allowed
`comms5_cme_status` or `comms5_contract_info` operation instead. Record Pat's
local attempt time and operation name, then query the bounded event window:

```powershell
.venv\Scripts\python.exe tools\diagnostics\query_comms5_transport_window.py `
  --start 2026-08-21T03:10:00+00:00 `
  --end 2026-08-21T03:11:00+00:00 `
  --operation cme_status
```

Classify only from evidence: `REQUEST_NEVER_REACHED_CADDY` when an allowed
attempt has no matching ingress record; `CADDY_RECEIVED_BACKEND_INCOMPLETE`
when HTTP receipt exists without MCP dispatch; `COMMS5_RECEIVED_DB_INCOMPLETE`
when database start lacks completion; `SERVER_COMPLETED_CLIENT_CANCELED`
when MCP completion exists without HTTP send; and
`SERVER_COMPLETED_CHATGPT_REPORTED_TIMEOUT` when server and HTTP completion
exist but ChatGPT reports a timeout. A missing record for a blocked tool is
`OPENAI_PRE_CONNECTOR_INTERCEPTION`, not a Riverview transport failure.

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
