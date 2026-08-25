# RUN-001RV2 — Targeted Revalidation of RUN-001R

Validator: C2 Independent Validator  
Input: `docs/codex-reports/seat-1/RUN-001R-revised-discovery.md`  
Scope: targeted correction of material RUN-001 defects only

## Verdict

## PASS

RUN-001R adequately corrects the material defects identified in the prior
RUN-001 validation. No blocking defect remains in the revised architecture
recommendation.

Concurrent C1/C2/C3 operation was treated as the accepted Steward fact and
was not re-opened as an acceptance issue.

## Targeted findings

### 1. Attempt fencing — CONFIRMED

RUN-001R requires terminal updates to match the exact tuple:

`work_order_id`, `attempt_id`, `lease_generation`, `fencing_token`, and
`worker_instance_id`.

It explicitly states that expired, superseded, or mismatched results may be
preserved as late-result evidence but may not advance authoritative work,
campaign, stage, or acceptance state. It also requires transactional checking
on heartbeat, terminal result, and reconciliation operations.

This is sufficient as an architecture requirement to prevent the previously
identified stale-worker success race. Implementation is correctly deferred to
RUN-002.

### 2. Writer/validator independence — CONFIRMED

The required lifecycle is explicitly:

`writer result → independent validator → PASS or structured defects → repair
attempt → independent revalidation → accepted`.

RUN-001R also states that the writer may not validate its own attempt and that
writer completion is never equivalent to acceptance. Explicit writer,
validator, repair-writer, and revalidator roles are required.

### 3. Immutable validation basis — CONFIRMED

Validation is required to bind to the original specification and hash,
acceptance criteria, original base SHA, resulting code/tree, changed paths,
validation commands, evidence, and validator identity/attempt.

The report expressly rejects writer completion prose as acceptance evidence.
This corrects the prior risk of accepting a self-authored completion summary.

### 4. Heartbeat, progress, and state — CONFIRMED

RUN-001R separates:

- `last_heartbeat_at` for worker liveness;
- `last_progress_at` and `progress_count` for meaningful activity;
- current authoritative state and blocked reason for lifecycle status.

It explicitly requires heartbeat, progress, and authoritative state transition
to remain distinct.

### 5. Three-level progress — CONFIRMED

The dashboard requirements preserve:

- overall roadmap progress;
- current phase progress;
- approximate current-step activity.

The report labels the current-step value as approximate and includes recent
activity, timestamps, seat/role, stale heartbeat visibility, and blocked state.
This preserves the required “and counting” semantics rather than treating the
step counter as authoritative completion percentage.

### 6. Grace independence — CONFIRMED

RUN-001R requires the Campaign Runner to start, dispatch, execute, validate,
repair, recover, and expose status without Grace. Grace is limited to a later
consumer/orchestrator role and is prohibited from being a runner-critical
dependency.

This corrects the prior architectural coupling concern.

### 7. Scope discipline — CONFIRMED

RUN-001R explicitly separates the RUN-002 implementation boundary from future
hardening. The RUN-002 list is limited to fencing, independent validation,
immutable validation basis, distinct telemetry/state, dashboard projection,
Grace-independent operation, and seat attribution.

Broader collision hardening, richer artifact cataloging, generalized routing,
additional Grace integration, and unrelated runtime changes are explicitly
classified as outside RUN-002 unless an actual failure requires them.

That is consistent with the targeted validation scope and does not make
optional improvements prerequisites.

## Required non-blocking changes

None required for acceptance of RUN-001R as the architecture basis.

RUN-002 must implement the stated fencing and lifecycle requirements, but their
absence from the current design-time report is not a defect because RUN-001R
correctly assigns implementation to RUN-002.

## Final recommendation

Proceed to RUN-002 using RUN-001R as the approved architecture basis. Preserve
the exact fencing tuple, independent validation lifecycle, immutable validation
basis, distinct telemetry semantics, three-level dashboard model, and
Grace-independent runner boundary as implementation acceptance criteria.
