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

A promoted Steward seed can also reach a `ready` validation stage and remain
without work when the objective stage has no `declared_action`. This is a
formation-boundary diagnostic, not evidence that Grace may infer an action from
seed text. The current seed contract records bounded intent and promotion;
typed engineering intake/decomposition must supply the approved action before
Relay can form a work order.

During migration 0016 integration, ObjectiveStage creation initially failed with a
PostgreSQL placeholder/parameter-count mismatch after adding `declared_action`. The
failure was a schema-binding/configuration defect, not a dependency or authority
decision.

REPAIR: Restore the missing declared dependency or measured lease state, or route a
true Steward decision. For a ready stage with no declared action, inspect the
authoritative intake/specification and action-binding boundary. Connect an
existing typed formation mechanism only if its authority, classification,
correlation, causation, and idempotency contract is already defined. Otherwise
stop and obtain the missing Steward-approved typed engineering-intent contract;
do not parse free-form seed prose, add a generic state setter, or insert an
action/work order directly. Retry only a registered retry-safe transport/provider
failure.
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
required evidence, enqueue recursive work from a diagnostic, or retrofit a
declared action onto an already-promoted objective without an authoritative
formation transition.

EVIDENCE: `grace_transition_evaluations`, `grace_checkpoints`, River correlation,
the authoritative objective/stage rows, the typed intake/specification record,
and the approved-action registry. The reproduced live specimen was objective
`7863bab6-72ce-425b-ba67-b21316c529d8`, stage
`92e933d5-6c2d-4855-a06f-88eb970f9c49`: it had accepted `seed:confirmed`, was
`ready`, and had `declared_action = null`, so no work order was formed.

TYPED FORMATION CLOSED LOOP: A Steward-authorized engineering seed may bind only
through `EngineeringIntentStore.bind`, which validates the durable seed/objective/
stage relationship, bounded repository identity and read-only policy, the
registered `codex.engineering.v1` action, capability health, classification,
correlation/causation, and idempotency. The resulting stage action is only
`{action_type, parameters.engineering_intent_id}`; it never contains shell text.
`CME` replays persisted declared actions after startup/cursor recovery, and Relay
owns idempotent work-order formation. A River cursor is not proof that evaluation
or dispatch completed, so a failed consumer slice must remain replayable.

DISTINGUISHING FORMATION FAILURES: A missing or malformed typed contract is a
formation validation failure; an unknown or disabled registered action is
`RIV-WRK-0001`; a missing declared action remains the waiting boundary above; an
idempotency replay returns the existing intent/action/work order and cannot
duplicate it. Unsupported classification, ineligible completed/cancelled state,
and absent explicit Steward confirmation fail closed. Inspect
`engineering_intents`, `objective_stages.declared_action`, `approved_actions`,
the River `engineering.intent.bound` event, then Relay and
execution/reconciliation records in that order.

VERIFY: Restart CME through its approved supervisor, confirm a healthy heartbeat,
observe the durable formation event/cursor, then confirm exactly one work order,
execution envelope, accepted reconciliation, and objective progression. Do not
invoke a manual cycle as acceptance proof and do not edit PostgreSQL directly.
