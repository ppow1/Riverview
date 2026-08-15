<!-- Version: 0.12.0 -->
# RIV-MCP-0009 - Full-loop mailbox and bounded reasoning response

Owner: Riverview mailbox store and bounded Riverview Comms reasoning capability.

## SYMPTOM

A River request is visible but cannot be acknowledged, claim ownership conflicts,
the lease expires, a response is duplicated or rejected, the request remains
incomplete, timeout paging is absent or duplicated, or the Comms schema is stale.

## LIKELY BOUNDARY

PostgreSQL mailbox lifecycle, request/correlation identity, fixed reasoning
consumer capability, migration `0012`, or deployed MCP schema.

## SAFE DIAGNOSTIC

Run the bounded local acceptance:

```powershell
Clear-Host
.venv\Scripts\python.exe -m riverview.mailbox.rv0045_acceptance
```

For the external service, use the authenticated Streamable HTTP acceptance and
inspect only tool names, counts, status, and bounded metadata. Trace one request
by `request_id` and `correlation_id`; do not query arbitrary SQL or protected
payloads.

## EXPECTED HEALTHY RESULT

The acceptance reports one completed request with event types:
`mailbox.request.accepted`, `mailbox.request.acknowledged`,
`mailbox.request.claimed`, and `mailbox.response.completed`. Duplicate retries
reuse the acknowledgement, claim, and response. An induced expiry reports one
timeout escalation; replay reports zero additional escalations.

## KNOWN FAILURE RESULT

- `RIV-MCP-0007`: bounded input, response, or classification validation failure.
- `RIV-MCP-0008`: missing request, invalid lifecycle, claim, correlation, or
  timeout/escalation state.
- A stale deployment exposes fewer than 19 tools or lacks one of
  `mailbox_acknowledge`, `mailbox_claim`, and `mailbox_submit_response`.
- A response accepted but the request remains incomplete indicates a transaction
  or schema mismatch; it is not a reason to replay the response blindly.

## REPAIR

Apply migration `0012_mailbox_timeout_escalation.sql` through the normal migration
runner, deploy the published Riverview Comms source, and restart only the
Riverview-owned loopback service. Refresh the ChatGPT application schema through
its supported registration path if discovery is stale.

## VERIFY

Rerun the local acceptance, external authenticated MCP acceptance, and schema
authority audit. Confirm the exact request/correlation lineage and one
`steward_escalations.mailbox_request_id` row for an induced timeout.

## DO NOT

Do not expose `mailbox_update`, arbitrary SQL, generic enqueue, roadmap mutation,
filesystem, shell, browser control, credentials, or Undercurrent. Do not bypass
correlation or lease ownership, fabricate a response, or mark a request complete
outside the typed response operation.

## EVIDENCE

PostgreSQL `mailbox_messages`, `mailbox_responses`, `river_events`, and
`steward_escalations` are authoritative. The migration ledger records the
`0012` checksum. Response payloads remain bounded and advisory.
