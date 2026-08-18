# RIV-COMMS5-0018 — Promotion safety-classification boundary

## Symptom

ChatGPT intercepts `comms5_confirm_and_promote_seed` before transport execution
with an inability to determine the request's safety status, while bounded
draft, cancellation, and supersession tools reach Comms5.

## Distinguishing probe

Compare the emitted promotion metadata with the accepted mutation tools:

- title and precise bounded description;
- `ToolAnnotations` safety hints;
- required flat client/provenance fields;
- explicit confirmation and idempotency fields.

Confirm from Comms5 diagnostics that no promotion request arrived. This is a
client pre-execution classification boundary, not a Riverview authorization
denial.

If the connector reports that the app was disabled after invocation, inspect
the approved public-boundary logs as a second probe. A request forwarded to the
Comms5 upstream followed by `aborting with incomplete response` / `context
canceled`, while the seed remains `draft` with no lifecycle event or objective,
means the connector abandoned the MCP response before canonical promotion was
committed. The forwarded request proves transport reachability, but does not
prove that `StewardSeedStore.confirm_and_promote` completed.

Tool discovery is a separate signal. A cached or previously fetched
`tools/list` result may remain visible after the connector can no longer invoke
the app. After the reported disabled invocation, correlate the exact time
window with Caddy logs. If no new request carrying the connector's traffic
reaches Caddy while independent authenticated `initialize`, `tools/list`, and
read-only tool probes succeed, the disablement is pre-transport and is not a
Comms5 response. Do not treat visible tool definitions as proof of a live
invocation session.

## Smallest repair

Publish non-destructive, idempotent, closed-world MCP hints and explain that the
operation records explicit Steward confirmation for one existing draft only.
Retain backend validation for authenticated Steward authority, explicit
confirmation, classification, correlation, idempotency, and lifecycle guards.

## Verification

Inspect the local FastMCP registry and public `tools/list`, restart the approved
Comms5 service, and have Pat retry promotion of the existing draft. A successful
transport call must still pass the canonical promotion store; no Codex test may
promote a seed.

For a connector-disable incident, first query `seed_status` read-only. If the
seed is still `draft`, reconnect or refresh the existing app and retry the same
promotion request with the same idempotency key. Do not infer promotion from a
connector error, and do not create a replacement key.

Record whether the failed read-only call produced any public request at all.
No Caddy request is the strongest available Riverview evidence of a
ChatGPT-side connector/app-state failure; a Caddy request with an upstream
response or cancellation requires tracing the MCP session ID and response
status before assigning blame.

## Do not

Do not rename or disguise promotion, remove confirmation, make promotion
automatic, bypass Comms5, or infer success from a local schema test alone.
