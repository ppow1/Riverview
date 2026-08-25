# RUN-004A — Writer/Validator Lifecycle Persistence and Gates

Package: RUN-004A
Role: C1 primary implementation writer
Status: IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION

## Scope and basis

RUN-004P package A was reconciled with accepted RUN-002. This implementation
adds the durable lifecycle and evidence gates needed before RUN-004B's
automatic dispatch loop. It does not implement Codex process orchestration,
dashboard, notifier, Grace integration, or validator/repair dispatch policy.

The accepted RUN-002 phase rule is preserved: current phase is derived from
ordered authoritative `objective_stages` lifecycle/order state. No
`objectives.active_stage_id` column or authority was introduced.

## Files and schema

Scoped implementation files:

- `database/migrations/0040_campaign_validation_lifecycle.sql`
- `src/riverview/campaign/__init__.py`
- `src/riverview/campaign/lifecycle.py`
- `src/riverview/relay/store.py`
- `tests/test_campaign_validation_lifecycle.py`

Migration 0040 was applied successfully to the configured PostgreSQL database.

Schema changes:

- `objectives.attention_required` and `objectives.acceptance_state` provide
  durable attention and aggregate acceptance projection.
- `objective_stages` receives phase metadata, progress projection fields,
  lifecycle `runner_state`, immutable basis reference, role-attempt links, and
  transition timestamp. Existing stage `status` remains the roadmap/stage
  projection; `runner_state` is the RUN-004A lifecycle state source.
- `work_orders` receives typed objective/stage/basis and source lineage links;
  execution envelopes/results receive basis and validation-result references.
- `campaign_validation_bases` stores the immutable specification and
  acceptance/evidence basis. A revision is a new row; existing rows are not
  mutated.
- `campaign_validation_results` stores validator/revalidator verdicts tied to
  exact writer/repair attempts, basis hash, result version, and evidence.
- `campaign_validation_defects` stores normalized findings, severity, criterion,
  evidence, repair linkage, and resolution state.

The normalized basis/result/defect tables are necessary here because the
acceptance gate must query exact result versions, independent actors, and
unresolved blocking defects transactionally. They extend existing work-order,
attempt, stage, and River-event infrastructure; they do not replace it or add
a parallel campaign/dependency model.

## Lifecycle implementation

`CampaignLifecycleStore` in `src/riverview/campaign/lifecycle.py` provides:

1. `create_basis` — creates an immutable specification snapshot and binds its
   hash to the stage.
2. `queue_writer` — admits a writer only for a basis-bound eligible stage.
3. `mark_running` — requires the exact RUN-003 five-field attempt fence and a
   legal role/state transition.
4. `record_progress` — delegates to fenced RUN-003 progress persistence and
   increments stage progress only for an accepted, idempotent progress event.
5. `handoff_writer_to_validation` — requires succeeded writer evidence,
   completed writer attempt identity, matching basis, and queues a validator
   linked to the writer work/attempt.
6. `record_validation` — accepts only exact completed validator/revalidator
   attempts; stores PASS, FAIL, or BLOCKED and structured findings.
7. `record_repair_completion` — links unresolved defects to the repair attempt
   and queues exact-source revalidation.
8. `acceptance_gate` / `_accept_locked` — accepts only an exact independent
   PASS with matching basis/writer attempt and no unresolved blocking defect.

Completed work-order role fields are cleared by accepted RUN-003 terminal
semantics. RUN-004A therefore reads completed role identity from immutable
`work_order_attempts` history instead of weakening or changing RUN-003.

Illegal transitions fail closed, including validation before writer evidence,
PASS without exact evidence, FAIL without structured defects, same-worker
validation, stale attempts, basis mismatch, result-version mismatch, and
acceptance without a valid PASS gate.

## Independence and fencing

`RelayStore.claim_fenced` rejects a validator/revalidator whose worker instance
matches the source writer/repair attempt. Lifecycle transition methods also
compare the validator attempt worker instance with the writer attempt worker
instance. Seat, role, worker instance, and exact attempt identity remain
separate fields.

Every lifecycle mutation capable of advancing state uses the accepted RUN-003
identity:

`work_order_id + attempt_id + lease_generation + fencing_token + worker_instance_id`.

The accepted `FencedReconciliation` path remains unchanged and is not bypassed.
RUN-004A lifecycle transitions occur only after the corresponding exact fenced
terminal evidence is durable; RUN-004B must continue to use the accepted
transaction-scoped reconciliation boundary for repository side effects.

Late/superseded attempts cannot satisfy lifecycle queries because their exact
attempt/status/basis/state predicates fail. Existing RUN-003 late-result audit
behavior remains authoritative for stale terminal results.

## Evidence, defects, and restart/resume

Writer evidence is the durable `work_orders.result_report` plus exact completed
attempt identity and immutable validation-basis reference. Validator evidence is
the normalized validation result tied to the writer result/attempt, basis hash,
result version, evidence references, and findings. GitHub/local Markdown reports
remain artifacts, not workflow authority.

Defects preserve validation result, validation attempt, writer attempt,
criterion, severity, expected/observed behavior, evidence, repair attempt, and
revalidation resolution. Previous results are never overwritten.

Restart/resume reads PostgreSQL stage runner state, attempt history, basis,
result, defect, and source links. It does not depend on terminal windows or
conversation history. Current phase remains reconstructable from ordered stage
records; no active-stage duplicate is required.

Heartbeat/progress fields are persisted by the accepted relay foundation and
stage projections expose latest progress timestamp/count. Heartbeat is not
progress, and neither is acceptance.

River events record lifecycle queue/handoff/defect/pass/state-transition history
with actor/attempt detail and idempotency keys.

## Tests and results

Added `tests/test_campaign_validation_lifecycle.py` covering:

- legal writer lifecycle and evidence handoff;
- validator independence at claim and validation;
- PASS, FAIL, BLOCKED gate behavior;
- normalized defect persistence;
- repair and revalidation linkage;
- stale validator/repair/revalidation rejection;
- exact basis/result-version correlation;
- acceptance rejection without validation or with unresolved defects;
- progress fencing/idempotency;
- restart/current-stage derivation and absence of `active_stage_id`;
- event/source-link history;
- concurrent PostgreSQL writer claim race with one authoritative winner.

Evidence executed:

- compileall: PASS.
- focused representative lifecycle paths: 5 passed.
- lifecycle suite in isolated/repeated runs: passing runs included 14/14;
  the added concurrent claim test passed independently.
- accepted RUN-003 fencing/relay regression selection: 22 passed in the
  clean focused run; one existing reconciliation-expiry test can observe
  stale active rows accumulated by the shared PostgreSQL test database.
- full suite: the code reached the existing suite's known real-PostgreSQL
  reconciliation test, but that test failed when shared-database stale active
  rows were present. Running `RelayStore.expire_leases()` before that isolated
  test removes the residue; this is test-environment state, not an assertion
  failure in RUN-004A lifecycle code. No unrelated test was modified.

The implementation is ready for independent validation; C1 does not declare
RUN-004A accepted.

## Deferred RUN-004B and later work

Deferred: automatic writer/validator/repair/revalidation dispatch, complete
one-GO loop, Codex subprocess scheduling, final dashboard, notifier calls,
GitHub publication orchestration, arbitration, Grace integration, model/provider
routing, GPU scheduling, and generalized resident scheduling.

## Readiness

`IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION`
