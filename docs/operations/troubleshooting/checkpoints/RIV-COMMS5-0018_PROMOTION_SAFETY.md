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

## Do not

Do not rename or disguise promotion, remove confirmation, make promotion
automatic, bypass Comms5, or infer success from a local schema test alone.
