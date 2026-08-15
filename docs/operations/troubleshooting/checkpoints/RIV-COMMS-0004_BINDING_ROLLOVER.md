# RIV-COMMS-0004 — Comms binding and conversation rollover

SYMPTOM: The ChatGPT application definition and the conversation-bound target
disagree, or the doorbell target differs from the active designated binding.

LIKELY BOUNDARY: Durable Comms binding registry, verification evidence, or
conversation rollover activation.

SAFE DIAGNOSTIC: Resolve the active `designated_reasoning` row from
`comms_bindings`; compare its conversation ID, exact URL, application reference,
consumer, contract version, and verification evidence. Do not infer from chat memory.

EXPECTED HEALTHY RESULT: Exactly one verified active binding exists for the role.
Candidate verification precedes activation; activation retires the previous binding
transactionally and preserves `replaced_binding_id`.

KNOWN FAILURE: A candidate is present but unverified, a URL does not contain the
exact conversation ID, or a stale local target differs from the authoritative active
binding. These fail closed before a wake.

REPAIR: Complete bounded candidate initialization and verification, then activate
only through the explicit Steward binding-confirmation path. Update local runtime
configuration only after authoritative activation is verified.

VERIFY: Resolve the active binding again, require `verification_state=verified`, and
run the bounded browser preflight against that exact target. Retain old binding and
replacement evidence; do not delete history.

DO NOT: wake a hand-edited fallback conversation, store credentials/cookies, create
a new MCP schema solely for rollover, or treat a new candidate as active before
verification and confirmation.

EVIDENCE: PostgreSQL `comms_bindings`, active-binding projection, candidate evidence,
and `RIV-COMMS-0004` diagnostic records.
