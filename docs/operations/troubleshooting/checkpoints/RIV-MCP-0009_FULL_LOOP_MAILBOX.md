<!-- Version: 0.13.0 -->
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
  `mailbox_acknowledge`, `mailbox_claim`, and
  `mailbox_submit_advisory_response`.
- `ACKNOWLEDGE AND CLAIM SUCCEED, RESPONSE WRITE BLOCKED BY CHATGPT SAFETY
  LAYER`: the designated conversation completed the first two typed writes,
  but the prior generic response-write schema was blocked twice before Riverview
  accepted the call. This is a ChatGPT tool-contract boundary, not evidence of
  PostgreSQL or mailbox failure.
- A response accepted but the request remains incomplete indicates a transaction
  or schema mismatch; it is not a reason to replay the response blindly.
- A real doorbell may succeed while the designated ChatGPT conversation leaves
  the request `unacknowledged/unclaimed/pending`. This indicates that the
  connected application has not executed the new typed write path, often
  because its application schema is stale or requires a UI refresh. This state
  was observed for one authorized RV-004.5 attempt.
- `SCHEMA REFRESH COMPLETED AFTER MAILBOX REQUEST EXPIRY`: the prior request's
  expiry deadline passed before the designated conversation had the refreshed
  write-capable schema. Treat that lineage as expired even if its pending row
  has not yet been swept by the expiry worker.
- `SCHEMA VISIBLE BUT NO REASONING TURN`: a fresh request is visible and
  unexpired, the fixed wake succeeds, and the application exposes the write
  tools, but no acknowledgement or tool call occurs. This distinguishes
  conversation-turn/tool-selection behavior from mailbox projection,
  correlation, and PostgreSQL failures.

## REPAIR

Apply migration `0012_mailbox_timeout_escalation.sql` through the normal migration
runner, deploy the published Riverview Comms source, and restart only the
Riverview-owned loopback service. Refresh the ChatGPT application schema through
its supported registration path if discovery is stale.

After deployment, refresh or reconnect the Riverview Comms application in the
designated conversation once if the platform has not refreshed its tool schema.
Then verify tool discovery before considering a new live acceptance request.
Only after that verification create a fresh bounded request with a sufficient
but finite TTL.
If a fresh request remains untouched after one known successful wake, require one
new reasoning turn in the designated conversation; do not issue another wake.

## VERIFY

Rerun the local acceptance, external authenticated MCP acceptance, and schema
authority audit. Confirm the exact request/correlation lineage and one
`steward_escalations.mailbox_request_id` row for an induced timeout.

## DO NOT

The exposed advisory response operation is
`mailbox_submit_advisory_response(request_id, correlation_id, summary,
evidence_refs)`. Its server-side semantics fix the response category to
`advice` and escalation to `false`; future escalation behavior remains a
separate explicitly authorized contract.

Do not expose `mailbox_update`, arbitrary SQL, generic enqueue, roadmap mutation,
filesystem, shell, browser control, credentials, or Undercurrent. Do not bypass
correlation or lease ownership, fabricate a response, or mark a request complete
outside the typed response operation.

Do not issue a second wake for a request whose first wake outcome is known, and
do not mark a pending request completed to compensate for a stale ChatGPT schema.
Do not revive or mutate a request whose expiry deadline has passed.
Do not treat a successful browser wake as proof that ChatGPT performed a tool
call, and do not scrape the conversation to manufacture that evidence.

Repeated retries of a platform-blocked response tool are not a repair. Narrow
the contract, deploy it, refresh the application schema, and resume only the
same request if it remains valid; never revive an expired request.

## EVIDENCE

PostgreSQL `mailbox_messages`, `mailbox_responses`, `river_events`, and
`steward_escalations` are authoritative. The migration ledger records the
`0012` checksum. Response payloads remain bounded and advisory.
