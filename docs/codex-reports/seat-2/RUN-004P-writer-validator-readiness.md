# RUN-004P — Writer / Validator / Repair Lifecycle Implementation Readiness

Package: RUN-004P  
Role: C2 read-only implementation-readiness investigator  
Date: 2026-08-25

## Status

READINESS_COMPLETE

This report is a read-only implementation plan. No runtime code or migration
was changed. RUN-003 remains unaccepted, and this plan assumes RUN-003R first
restores the accepted stale-result/fencing invariant.

## Executive conclusion

The repository has enough durable primitives for the lifecycle, but it does
not currently implement it. The smallest safe path is to retain PostgreSQL,
objective stages, work orders, attempts, execution envelopes/results,
reconciliation records, River events, and `RelayStore` fencing, then add a
bounded campaign-lifecycle layer. Writer completion must become a handoff to
validation, not campaign acceptance.

I recommend TWO practical implementation packages:

1. RUN-004A: lifecycle persistence and transactional gates — immutable basis,
   validator/repair/revalidation work orders, durable defects, state
   transitions, and the acceptance gate.
2. RUN-004B: runner/worker one-go integration — automatic role dispatch and
   lifecycle advancement through writer, validator, repair writer, and
   revalidator, with end-to-end crash/idempotency coverage.

This is a real split: the first package has an independently testable durable
state boundary, while the second changes the active Codex execution path. It
also reduces the collision with RUN-003R. RUN-004B must not begin until
RUN-003R is accepted.

## 1. Existing implementation facts

### Objective and stage model

`database/migrations/0010_objective_stage_model.sql` and
`src/riverview/grace/objectives.py:28` (`ObjectiveStore`) provide the
authoritative objective, ordered `objective_stages`, and
`objective_stage_dependencies` model. `ObjectiveStore.add_evidence`,
`complete_stage`, `ready_stages`, and `finalize` are durable stage operations,
but the class explicitly says it “never enqueues work.” It is therefore useful
as the objective/stage authority, but it cannot by itself provide the runner
loop.

The accepted RUN-002/RV rule remains in force: current phase is derived from
ordered authoritative objective-stage lifecycle state. Do not add
`objectives.active_stage_id`, a second dependency graph, or a campaign table
that duplicates objective/stage identity.

### Current writer completion boundary

`src/riverview/runner.py:41` (`RestrictedRunner`), especially
`run_once` at line 51 and `_execute_codex` at line 76, is the current Codex
writer path. It claims a writer work order, builds and persists an execution
envelope, invokes the Codex adapter, persists the execution result, performs
repository reconciliation/decision recording, and calls
`RelayStore.complete_fenced`.

The exact campaign handoff seam is after the writer result has passed the
RUN-003R-corrected fenced technical completion boundary and its bounded
evidence is durable. At that seam, the campaign lifecycle transaction must:

* retain the writer attempt and result as history;
* set the package/stage runner state to `validation_pending`;
* create the validator work order with the same immutable basis reference;
* emit an idempotent lifecycle event; and
* commit before validator execution begins.

The current `record_decision("accepted")` in
`src/riverview/autonomy/control.py:988` is a technical reconciliation
decision, not sufficient campaign acceptance. It must not be treated as the
campaign PASS gate. The current implementation has no validator work order,
defect handoff, repair work order, revalidation, or campaign acceptance gate.

The current ordering defect is explicitly outside this package: RUN-003R must
repair `_execute_codex` so stale completion is rejected before reconciliation
or publication. RUN-004 must consume that corrected seam.

### Existing persistence and dispatch

`database/migrations/0003_relay_foundation.sql` provides work orders and
historical attempts. `0014_autonomous_control_plane.sql` provides
`execution_envelopes` with objective/stage, base SHA, bounded instruction,
allowed paths, acceptance criteria, and evidence requirements, plus
`execution_results`. `0017_lanes_reconciliation.sql` provides technical
reconciliation records and execution lanes.

`src/riverview/relay/store.py` provides the accepted RUN-003 primitive APIs:
`claim_fenced` (line 125), `heartbeat_fenced` (227), `progress_fenced` (257),
`complete_fenced` (315), `expire_leases` (384), and
`requeue_timed_out` (422). These should remain the normal claim/heartbeat/
progress/completion machinery. `src/riverview/relay/worker.py:34` currently
supports only the writer role, and `RestrictedRunner.run_once` currently
claims with writer role, so validator and repair roles require explicit
dispatch integration.

`src/riverview/autonomy/control.py:434` (`ExecutionStore`) and
`ResultReconciler.persist` at line 887 persist the current envelope/result
shape, but do not yet persist the full campaign validation basis or lifecycle
result. `reconcile_repository` at line 928 remains the actual implementation
and evidence verification boundary.

## 2. Smallest lifecycle implementation path

### Writer success → validation pending

The writer’s technical result must be fenced and durably recorded first. The
new lifecycle service should then execute one PostgreSQL transaction that
locks the package/stage and current writer result, verifies the exact writer
attempt and basis, and atomically creates the validator work order. The
validator work order must not be executable before this transaction commits.

The resulting campaign state is `validation_pending`; claim changes it to
`validation_running`. Writer prose alone cannot change the campaign state to
accepted.

### Validator work order

Use the existing `work_orders`/`work_order_attempts` path and
`claim_fenced`, with a campaign action type and role `validator`. The work
order must carry or relationally reference:

* objective/stage/package identity;
* originating writer attempt ID;
* writer seat and writer `worker_instance_id`;
* immutable validation-basis ID/hash;
* role `validator` and eligibility policy;
* causal/correlation references to the writer work order/result; and
* the expected repository/tree/evidence target.

The validator is an ordinary claimable work order, not an in-process callback
or Steward handoff.

### Independence enforcement

At validator work-order creation and again at claim, enforce that the
validator attempt’s `seat_id`, `worker_instance_id`, and role are recorded and
that the worker instance is not the originating writer instance. The role
must be validator, and the source writer attempt must be immutable history.

For repair, enforce the same exclusion between repair writer and revalidator.
The same prior validator may revalidate only when it is a new attempt and is
not the repair writer, consistent with RUN-002. A validator cannot validate a
writer attempt whose origin matches its own current process instance. This is
the minimum enforcement needed; no new authentication system is required.

### Validation input and basis

`execution_envelopes` already contains most fields: base SHA, allowed paths,
acceptance criteria, evidence requirements, bounded instruction, and
objective/stage. It also has `validation_basis_hash` from migration 0039.
However, the current envelope is per execution attempt and the existing
`ExecutionStore.persist` does not populate a complete immutable package-level
basis or validation command set.

Recommended disposition: ONE NEW BOUNDED STRUCTURE, referenced by envelopes.
Add an immutable `campaign_validation_bases` record keyed to the objective
stage/package, containing the canonical specification/reference, hash,
acceptance criteria, evidence requirements, base SHA, allowed paths, expected
outputs, validation commands, and revision/supersedes metadata. Envelopes and
all validator/revalidator attempts reference the same basis ID/hash. A
revision creates a new basis record; it never mutates the original.

This avoids duplicating objective/stage data and avoids copying a mutable JSON
basis into every attempt. Existing envelope fields remain the execution
projection and can be retained for bounded invocation input.

### PASS and structured defects

Use existing `execution_results` for the durable validator result/evidence,
but add a bounded `validation_defects` table for queryable, append-only defect
history. Reusing only `validation_evidence` JSON would preserve raw material
but would make defect resolution, repair linkage, and unresolved-defect gates
ambiguous.

Minimum defect shape:

* `defect_id`;
* `validation_attempt_id` FK to the historical work-order attempt;
* criterion reference and severity;
* expected behavior and observed behavior;
* evidence references/details;
* required repair;
* resolution state and timestamps; and
* nullable repair/revalidation attempt references.

On validator PASS, the lifecycle transaction verifies the validator fence,
basis hash, implementation/tree evidence, and absence of unresolved blocking
defects before moving to the acceptance gate. On FAIL, it records all defects
append-only, sets `defects_found`/`repair_pending`, and creates the repair
writer work order in the same transaction. Duplicate result delivery must be
idempotent.

### Repair and revalidation

The repair work order uses normal fencing and links to the original package,
writer attempt, validator attempt, immutable basis, and defect set. It must
not overwrite the original writer attempt or validation result.

Repair completion creates `revalidation_pending`, then a new revalidator
attempt changes it to `revalidation_running`. The revalidator receives the
original basis, actual repaired tree/evidence, and the complete defect history.
It may be the prior validator only when it is a new independent attempt and is
not the repair writer. A repair writer can never claim its own revalidation.

Revalidation PASS uses the same acceptance gate. Further defects append to
history and create another repair cycle, subject to the existing RUN-002
exception seam for repeated unresolved disagreement.

## 3. Acceptance gate and state ownership

The acceptance gate should live in the new campaign lifecycle service, in one
transaction with row locks and exact attempt/fence checks. It must require:

* a successful fenced writer or repair result;
* actual implementation/tree and evidence verification;
* validator or revalidator PASS;
* the same immutable validation-basis ID/hash;
* no unresolved blocking defects;
* exact currently authoritative validator/revalidator attempt tuple;
* technical reconciliation accepted where required; and
* idempotent transition of the package/stage to accepted, followed by normal
  objective-stage advancement.

`reconciliation_records.decision='accepted'` remains technical execution
reconciliation. It is not by itself campaign acceptance. This distinction is
necessary because the current writer path can record a technical accepted
decision before any independent validator exists.

The existing `objective_stages.status` model should remain the roadmap/stage
authority and should not receive a second current-phase field. Add the minimum
runner lifecycle/acceptance projection needed for the explicit states (for
example a runner state/acceptance-state column on `objective_stages`, or an
equivalent bounded stage-run record), rather than overloading the objective
dependency graph. Work-order/attempt rows remain the authority for individual
role attempts.

The lifecycle must expose these transitions explicitly:

`validation_pending → validation_running → accepted`

or:

`validation_running → defects_found → repair_pending → repair_running →
revalidation_pending → revalidation_running → accepted`

with `blocked`, `failed`, and `timed_out` terminal/recovery outcomes as
appropriate. Every acceptance-producing transition must use the gate above.

## 4. Arbitration seam

RUN-004 need not implement C3 arbitration. The lifecycle service should,
however, preserve repair-cycle count and append-only validation history and
expose a single transition seam such as `arbitration_required` when the
configured repair limit is exceeded, evidence genuinely conflicts, or
writer/validator disagreement remains unresolved. Ordinary defect/repair/
revalidation cycles must never invoke C3.

## 5. Telemetry and later dashboard projection

The existing River event path and work-order timestamps are sufficient as the
initial telemetry foundation. Emit separate idempotent events for:

* claim/state movement;
* heartbeat (liveness only);
* meaningful progress (message/detail and incremented counter);
* validation PASS or defect recording;
* repair/revalidation transitions; and
* acceptance, block, timeout, or failure.

Heartbeat must not increment progress. Progress must not imply completion.
State transition is authoritative lifecycle movement. The dashboard can later
project role, seat, current package, last heartbeat, last meaningful
progress, recent activity, state, and blocked reason from these records. No
dashboard implementation is part of RUN-004.

## 6. One-GO gaps to remove

Today `ObjectiveStore` does not enqueue work, `RelayWorker` supports only
writer, and `RestrictedRunner` has no validator/repair/revalidator dispatch.
The current result path therefore stops at technical execution/reconciliation;
there is no automatic validator assignment or structured defect return.

RUN-004 must remove these manual seams:

* no Steward copy/paste of writer output into a validator request;
* no manual validator work-order creation;
* no manual transcription of defects;
* no manual repair work-order creation;
* no manual revalidation trigger; and
* no manual acceptance after a validator PASS.

The automatic chain must be PostgreSQL/event driven and restartable from
durable rows. Steward involvement remains only for a genuine blocker,
arbitration, or explicit attention condition.

## 7. Expected ownership and collision map

### Files likely to change

* a new next-number migration for the bounded lifecycle persistence;
* a new neutral module such as `src/riverview/campaign/lifecycle.py` for
  transactional transitions, basis, defects, and acceptance gates;
* `src/riverview/relay/store.py` for role-aware lifecycle work-order creation
  and independence checks, if those cannot remain in the new service;
* `src/riverview/runner.py` for automatic writer/validator/repair/revalidator
  dispatch and the post-fenced-completion handoff;
* `src/riverview/relay/worker.py` for supported roles and worker role
  configuration;
* `src/riverview/autonomy/control.py` only where envelopes/results must carry
  the immutable basis and validator evidence.

### Files to read/reuse, not redesign

* `database/migrations/0010_objective_stage_model.sql` and
  `src/riverview/grace/objectives.py` for objective/stage/dependency authority;
* existing River event storage and event types;
* existing execution lanes/reconciliation structures;
* status snapshot/server and notifier seams for later packages;
* the Codex adapter and repository evidence checks.

Do not make Grace a boot or execution dependency. The lifecycle service may
reuse the PostgreSQL model and transaction conventions without importing
Grace cognition as an authority.

### Migration likely required

One bounded migration is likely required for:

* immutable campaign validation basis;
* durable structured defects;
* stage/package runner lifecycle or acceptance projection; and
* relational source-attempt/basis/objective-stage links needed for safe
  validator and repair work-order queries.

Extend existing tables only where the field is a clear runner requirement.
Do not add campaign, package, dependency, artifact, or telemetry duplicates.

### Tests likely required

Add a focused lifecycle suite, for example
`tests/test_campaign_validation_lifecycle.py`, plus one-go integration tests
for role dispatch/restart. Extend existing runner/relay regression tests only
after RUN-003R is accepted. Tests should cover the matrix below and use real
PostgreSQL transactions where the gate/locking behavior matters.

### RUN-003R collision risk

HIGH and exact. RUN-003R necessarily overlaps:

* `src/riverview/runner.py`, especially `_execute_codex` and the completion/
  reconciliation ordering;
* `src/riverview/relay/store.py`, around `complete_fenced` and late-result
  rejection boundaries; and
* likely `tests/test_campaign_fencing.py`.

RUN-004 implementation must wait until RUN-003R is independently accepted.
RUN-004A should avoid changing the stale-result ordering; RUN-004B must call
only the corrected completion seam.

## 8. Acceptance test plan for implementation

The implementation should later pass at minimum:

1. Writer success creates `validation_pending`.
2. Writer cannot claim or validate its own attempt.
3. An eligible independent validator claims the validation work order.
4. Validator PASS satisfies the acceptance gate.
5. Writer completion prose alone cannot accept a package.
6. Validator failure creates durable structured defects.
7. Defects create `repair_pending` automatically.
8. Repair writer can claim the repair work order.
9. Original writer and validator attempts remain unchanged history.
10. Repair completion creates `revalidation_pending`.
11. Repair writer cannot claim its own revalidation.
12. Independent revalidator PASS allows acceptance.
13. Unresolved blocking defects prevent acceptance.
14. Duplicate validator/revalidator result delivery is idempotent.
15. Crash/restart preserves state, basis, attempts, defects, and next work.
16. Ordinary writer/validator/repair/revalidation requires no Steward
    copy/paste or manual work-order creation.
17. Arbitration is not invoked during a normal repair cycle.

Also retain the accepted RUN-003 fencing tests: exact tuple enforcement,
heartbeat without progress, durable progress idempotency, expiry/retry with a
new fence, and fail-closed stale results after RUN-003R.

## 9. Final recommendation

Recommended RUN-004 shape: TWO PACKAGES — RUN-004A durable lifecycle/gates,
then RUN-004B one-go runner integration. This provides a meaningful
independent persistence acceptance boundary and avoids merging a large new
orchestration path into the still-repairing RUN-003 execution boundary.

RUN-003R collision risk: HIGH — `RestrictedRunner._execute_codex`,
`RelayStore.complete_fenced`/late-result boundary, and related fencing tests.

Implementation readiness: READY_AFTER_RUN-003R_ACCEPTANCE

