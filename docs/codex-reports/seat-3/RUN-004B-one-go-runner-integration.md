# RUN-004B — One-Go Campaign Runner Integration

Package: RUN-004B
Role: C3 primary implementation writer
Status: IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION

## 1. Authoritative package definition

The accepted RUN-004P/RUN-002 basis defines RUN-004B as the bounded one-go
operator flow over the accepted RUN-003 fenced work path and RUN-004A writer,
validator, repair, revalidation, and acceptance lifecycle.  One start/go
operation may advance eligible work through those persisted transitions;
repair/revalidation cycles are automatic, while configured Steward/arbitration
gates remain explicit.  Current phase remains derived from ordered
`objective_stages` lifecycle state; no `objectives.active_stage_id` authority is
introduced.

Dependencies are accepted RUN-002 specification, RUN-003 persistence/fencing
and reconciliation authority, and RUN-004A/R acceptance/evidence binding.
RUN-004B owns only the integration seam that claims role-appropriate work,
executes through the worker boundary, persists the fenced result, and invokes
the next accepted lifecycle transition. It does not replace any foundation.

## 2. Implementation and seams

Changed scoped files:

- `src/riverview/campaign/one_go.py` — `CampaignOneGoRunner`, `WorkerSlot`,
  bounded role execution, lifecycle advancement, failure checkpointing, and
  campaign-scoped claiming.
- `src/riverview/campaign/__init__.py` — public exports.
- `src/riverview/relay/store.py` — additive `objective_id` filter on the
  existing transactional `claim_fenced` query. The fence, attempt identity,
  `FOR UPDATE SKIP LOCKED`, and late-result path remain authoritative.
- `tests/test_campaign_one_go.py` — bounded orchestration, stale-fence,
  restart/resume, configurable worker, and repeated repair-loop tests.
- `tests/test_campaign_one_go_postgres.py` — PostgreSQL writer/validator and
  validation-failure repair/revalidation probes.

No migration is required. Existing `objective_stages`, `work_orders`,
`work_order_attempts`, lifecycle tables, and River events are sufficient.

## 3. One-go flow

`CampaignOneGoRunner.run()` has an explicit `max_steps` bound. Each tick claims
at most one role attempt. Worker capabilities are injected as `WorkerSlot`
configuration and executor callbacks; no C1/C2/C3 architecture, model, GPU,
provider, or endpoint is hardcoded. With an objective scope, the objective
predicate is applied inside the same transactional `claim_fenced` selection,
preventing a two-query scope/claim race.

The transition flow is:

`writer completion → handoff_writer_to_validation → validator completion →`
`record_validation(PASS|FAIL|BLOCKED) → acceptance or persisted defects →`
`repair completion → record_repair_completion → revalidator completion →`
`acceptance_gate`.

The runner does not directly accept a stage, manufacture validation evidence,
or create a parallel completion path.

## 4. Required behavior evidence

The in-memory integration tests prove:

- writer and independent validator advance without manual handoff;
- FAIL produces the repair/revalidation path;
- a second bounded repair cycle preserves distinct role/result history;
- a stale `RIV-WRK-0003` result produces a stale outcome and no downstream
  handoff;
- a new runner instance can resume a pending validator without replaying the
  writer;
- execution is bounded and worker slots are configurable.

The PostgreSQL probe passes the isolated writer→validator path when no
concurrent shared-database claimant intervenes. The failure-loop probe was
repeatably affected by the known shared database residue/concurrent claimant:
the test work order was claimed before the test runner could process it. This
is the same benign pre-existing expired-row/stale-lease contamination recorded
by RUN-004AV/RUN-004ARV; it is not represented as a RUN-004B success claim.

## 5. Fencing and stale results

All persisted claims use `RelayStore.claim_fenced`; completion uses the exact
work-order, attempt, lease-generation, fencing-token, and worker-instance
identity. `RIV-WRK-0003` is surfaced as `stale`, and the runner does not invoke
lifecycle handoff or validation after stale completion. The existing late
result audit remains in RelayStore.

Worker execution failures are recorded as truthful fenced terminal failures
with an error checkpoint, failed attempt, stage failure where current, and a
River state-transition event. They do not dispatch validation or acceptance.

## 6. Restart, phase, isolation, and idempotency

Restart/resume relies on persisted queued/claimed/succeeded lifecycle state;
runner objects hold no authoritative campaign state. Admission checks existing
writer work and uses lifecycle idempotency. Role transitions are persisted by
RUN-004A, and repeated ticks stop at the explicit bound when no claim is
available.

Current phase is not cached or separately writable. Admission refreshes
readiness from ordered dependency state and queues only the eligible stage in
the selected objective scope. The objective-scoped atomic claim prevents a
runner for objective A from claiming objective B. Exact source attempt and
basis/result binding remains enforced by RUN-004A, providing cross-package
isolation.

## 7. Acceptance and failure visibility

The runner requires a successful structured executor result before calling
`complete_fenced`. Validator/revalidator result fields are passed to
`record_validation`, where the accepted basis, actual result version, evidence,
independence, defect, repair, and acceptance gates remain authoritative.
Dispatch, fencing, lifecycle, malformed-result, and persistence errors are
returned as failed outcomes with checkpoints; they are not silently converted
to success. Steward escalation/notifier behavior remains owned by the
accepted runner/governance layers and is not duplicated here.

## 8. PostgreSQL and regression evidence

Executed successfully:

- `tests/test_campaign_one_go.py`: 6 passed.
- isolated PostgreSQL writer→validator one-go proof: passed.
- `compileall` for `campaign` and `relay`: passed.
- package import validation for `CampaignOneGoRunner`, `WorkerSlot`, and
  `RelayStore`: passed.

The focused RUN-004A/RUN-003 suite was run. Failures were the previously known
shared-database claimed/expired-row contamination, including lease sweeper
observations and inability of fixtures to claim their newly queued rows. No
new assertion identified a fencing or lifecycle semantic regression. The
failure-loop PostgreSQL probe remains to be rerun in an uncontended database
for independent validation.

The implementation adds no provider/model policy and no hardware assignment.
It does not alter Grace cognition or Campaign Runner schema.

## 9. Remaining packages and non-goals

No later Campaign Runner package was identified as a prerequisite in the
accepted RUN-002/RUN-004P package definition. Dashboard, notifier,
arbitration/exception handling, and provider-specific worker execution remain
outside this bounded integration unless separately assigned by the roadmap.

Explicit non-goals: Campaign Runner redesign, new schema, active-stage
authority, model/provider selection, GPU scheduling, Grace cognition changes,
UI, and unrelated database cleanup.

## 10. Validation instructions

An independent validator must inspect the accepted RUN-002/RUN-004A criteria,
the scoped diff, the actual `claim_fenced` SQL and lifecycle calls, the six
runner tests, and a clean PostgreSQL run of the success, FAIL→repair loop,
stale writer/validator, restart, cross-objective, and idempotency scenarios.
The validator must distinguish the documented shared-database contamination
from genuine RUN-004B failures.

Validation readiness: READY_FOR_INDEPENDENT_VALIDATION
