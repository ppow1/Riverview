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

During migration 0016 integration, ObjectiveStage creation initially failed with a
PostgreSQL placeholder/parameter-count mismatch after adding `declared_action`. The
failure was a schema-binding/configuration defect, not a dependency or authority
decision.

REPAIR: Restore the missing declared dependency or measured lease state, or route a
true Steward decision. Retry only a registered retry-safe transport/provider failure.
For the migration defect, align the additive column list, placeholder count, and
parameter tuple, then rerun the existing objective-stage tests and migration ledger
check; never rewrite an applied migration.

VERIFY: Re-evaluate and confirm the same idempotency key yields one durable decision
and, when needed, one open checkpoint.

A real recovery acceptance completed objective
`grace-momentum.acceptance.0819f7b0-6c65-4d56-8cd0-5e1937487244`, enqueued work
`f5250284-584d-4448-8890-5035af378d59`, and finalized without recursive creation.

The retry acceptance used work `389c0428-0695-4a36-94ef-360df8b1878b`: the first
bounded timeout was requeued once, the second bounded timeout remained terminal, and
a third retry was rejected with `RIV-GRC-0007` for Steward checkpoint routing.

DO NOT: Infer a transition from conversation prose, mark a stage complete without
required evidence, or enqueue recursive work from a diagnostic.

EVIDENCE: `grace_transition_evaluations`, `grace_checkpoints`, River correlation, and
the authoritative objective/stage rows.
