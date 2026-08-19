# RIV-RES-0002 — Resident room/session boundary

Resident room turns require an authoritative in-process room, admitted resident
IDs, bounded classification, automatically initialized resident sessions, an
eligible provider, and one preserved correlation ID. Diagnostics contain only
bounded IDs/types and never resident payloads or credentials.

Recovery: validate the room and participant set, select the configured local
provider, initialize sessions through the resident gateway, run one ordered
round, and preserve the room snapshot. A failed provider turn must not transfer
authority or create recursive resident work.

Direct Grace execution-intent boundary: a Grace response or a Steward message
containing words such as “proceed”, “authorize”, or “implement” is only a
candidate and never creates authority. The governed direct-Grace path requires
an authenticated Operator session plus a typed `direct_grace_approval` envelope
containing one complete immutable specification, validated read-only formation
contract, stable idempotency key, approval-operation UUID, and explicit Steward
confirmation. The server supplies the Steward principal from the authenticated
Operator boundary; the client cannot select it. The envelope enters the same
specification → seed → promotion → `steward_authority_grants` path used by
Comms5, so one approval produces one replay-safe objective/authority lineage.

The normal Operator conversation presents that exact typed proposal as one
durable pending approval. Grace owns the approval ceremony; the Steward may
answer `Yes` or `No` in the conversation, without protocol text or JSON. The
server binds `Yes` only to the latest unconsumed proposal for that conversation
and materializes the typed envelope itself. A later proposal supersedes an
earlier pending proposal; a stale approval control fails closed. `No` records a
bounded rejection and creates no authority. An unrelated `Yes` is ordinary
conversation and is never executable.

If Activity records `execution_intent_detected=false` after Grace says it is
proceeding, inspect the correlated `grace.conversation.completed` event and
distinguish `execution_intent_candidate` from `governed_execution_intent`.
Missing typed approval is a real Steward checkpoint; malformed contract,
missing specification fields, hash/version conflict, or idempotency conflict
fails closed. Never reconstruct an exact specification from conversation prose
or insert an objective/work order directly.

Response/redaction boundary: if a Grace turn is persisted with literal repeated
`<REDACTED>` text, compare the bounded response metadata, provider identity,
classification, correlation, and the stored/API text hash. The Ollama adapter
passes its provider `response` field into `ReasoningResponse.summary` without a
Riverview redaction transform; the Operator projection and client render that
summary without replacing it. Therefore an operationally classified response
that is already marker-only at persistence is provider-boundary evidence, not
proof of Riverview protected-payload redaction. Check the provider result or
provider logs through a bounded, non-payload diagnostic path. Do not recover
hidden content, disable redaction, or treat a malformed/missing
`RIVERVIEW_SPECIFICATION_V1` proposal as authority. A marker-only provider
result yields no pending approval and must remain a diagnosable failed proposal.
If persistence/API hashes differ, investigate the projection boundary; if they
match but the browser differs, investigate Operator rendering. A separate
external ChatGPT display error is not evidence that Riverview redacted the
Grace response.
