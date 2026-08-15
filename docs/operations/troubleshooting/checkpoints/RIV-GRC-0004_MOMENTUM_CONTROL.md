# RIV-GRC-0004 — Momentum evaluation and checkpoint routing

SYMPTOM: Grace cannot explain why an objective stage is ready, blocked, stale, or
Steward-gated.

LIKELY BOUNDARY: PostgreSQL objective/stage dependencies, lease timestamps, or the
explicit Grace authority rule.

SAFE DIAGNOSTIC: Run `GraceMomentum.evaluate(objective_key)` and inspect
`grace_transition_evaluations`; for stale work inspect `grace_checkpoints` and the
corresponding work-order lease.

EXPECTED HEALTHY RESULT: One idempotent evaluation records `ready`, `blocked`,
`completed`, or `checkpoint` with a bounded reason and no silent objective mutation.

KNOWN FAILURE: `RIV-GRC-0004` means the objective is absent; `RIV-GRC-0005` means a
work lease is stale; `RIV-GRC-0006` means checkpoint fields are incomplete;
`RIV-GRC-0007` means a retry request is outside the one-retry bound.

REPAIR: Restore the missing declared dependency or measured lease state, or route a
true Steward decision. Retry only a registered retry-safe transport/provider failure.

VERIFY: Re-evaluate and confirm the same idempotency key yields one durable decision
and, when needed, one open checkpoint.

DO NOT: Infer a transition from conversation prose, mark a stage complete without
required evidence, or enqueue recursive work from a diagnostic.

EVIDENCE: `grace_transition_evaluations`, `grace_checkpoints`, River correlation, and
the authoritative objective/stage rows.
