# RUN-003 — Persistence and Attempt Fencing Implementation

Package: RUN-003
Role: C1 primary implementation writer
Status: IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION
Version: 0.1.0

## Scope delivered

This package implements the bounded PostgreSQL persistence foundation for
campaign attempt identity, claims, fenced liveness/progress, lease expiry,
retry re-claim, and terminal-result fencing. It does not implement campaign
orchestration, validation assignment, repair loops, arbitration, Codex
scheduling, dashboard, notifier, or Grace integration.

## Files changed

- `database/migrations/0039_campaign_attempt_fencing.sql`
- `src/riverview/relay/store.py`
- `src/riverview/relay/__init__.py`
- `src/riverview/relay/worker.py`
- `src/riverview/runner.py`
- `tests/test_campaign_fencing.py`
- this report

Unrelated dirty-worktree paths were preserved and are not part of this package.

## Migration and schema evidence

Migration `0039` was applied through the existing migration runner against the
configured PostgreSQL database `riverview` as role `riverview_app`.

It extends existing structures rather than adding parallel workflow tables:

- `work_orders`: active attempt UUID, lease generation, fencing token, worker
  instance, seat/role, progress projection, and blocked reason.
- `work_order_attempts`: promoted UUID `attempt_id` plus preserved
  `legacy_attempt_id`, generation/token/worker identity, heartbeat/progress,
  terminal and late-result fields.
- `relay_workers`: process-incarnation identity, seat, supported roles, current
  work order, and stale projection.
- `execution_envelopes` and `execution_results`: attempt fencing references and
  late/authoritative result markers.
- indexes and checks support active-lease lookup, unique attempt identity,
  non-negative progress, and the all-or-none active fence tuple.

No `objectives.active_stage_id` was added. Current phase remains derived from
authoritative objective-stage state as required by RUN-002.

## Runtime symbols and semantics

`riverview.relay.store` now provides:

- `AttemptIdentity`: immutable `(work_order_id, attempt_id,
  lease_generation, fencing_token, worker_instance_id)`.
- `RelayStore.claim_fenced`: one PostgreSQL transaction locks an eligible queued
  order with `FOR UPDATE SKIP LOCKED`, creates a new UUID attempt/token and
  generation, inserts the attempt, copies the exact tuple to `work_orders`,
  appends `runner.attempt.claimed`, and commits before execution.
- `heartbeat_fenced`: updates only heartbeat and lease expiry, requiring every
  component of the exact tuple. It never increments progress or changes state.
- `progress_fenced`: requires an idempotency key and meaningful message,
  appends one `runner.progress` event, and increments attempt/work-order
  progress exactly once. Duplicate keys do not increment counters.
- `expire_leases`: locks and rechecks expired active attempts, marks the
  attempt timed out, clears authoritative active ownership, and appends a
  timeout event.
- `requeue_timed_out`: makes a timed-out order eligible for a new attempt;
  claim creates a new attempt UUID, generation, token, and worker instance.
- `complete_fenced`: locks the work order and permits terminal state advance
  only when the exact tuple and active lifecycle match. It clears the active
  tuple only after the fenced update succeeds.

Legacy `claim`, `heartbeat`, `progress`, and `complete` calls remain bounded
compatibility wrappers; they resolve the current exact identity and execute the
same fenced mutations. `RelayWorker` and `RestrictedRunner` now generate and
carry a process-incarnation `worker_instance_id`.

## Stale and late results

When any tuple component is stale or wrong, terminal completion does not update
`work_orders`, does not clear or replace the active successor fence, and does
not invoke repository reconciliation/publication. The submitted result is
recorded on the historical attempt with `late_or_stale=true` and a
`runner.result.late_rejected` River event. The audit transaction commits before
the API returns the fenced rejection.

The same exact tuple rule applies to heartbeat and meaningful progress; stale
workers cannot extend a lease or advance the authoritative progress counters.

## Tests and evidence

Focused RUN-003 acceptance tests in `tests/test_campaign_fencing.py` cover:

- complete claim identity;
- competing/targeted claim behavior;
- heartbeat without progress;
- idempotent meaningful progress;
- wrong fencing token, generation, and worker instance;
- expired lease and new attempt authority;
- late-result preservation without state advance;
- no objective-level `active_stage_id` authority.

Executed evidence:

- Ruff on all changed runtime/test Python files: PASS.
- Focused fencing and related Relay/runner/objective/River/status tests: 23
  passed.
- Live PostgreSQL probe: PASS for claim, heartbeat, progress, expiry, retry,
  stale completion rejection, audit preservation, successor completion, and
  exact active-attempt continuity.

The full repository suite was exercised after isolating the fixture from active
relay-worker consumption by exact work-order targeting and seat/role
eligibility: PASS. The suite emitted one pre-existing pydantic settings
forward-reference warning; no test failed.

## Diagnostics and recovery

Stable runtime checkpoints include `RIV-WRK-0002` for fenced heartbeat/progress
ownership, `RIV-WRK-0003` for fenced terminal completion, `RIV-WRK-0004` for
lease expiry, and new bounded identity/claim/retry checkpoints `RIV-WRK-0010`
through `RIV-WRK-0015`. PostgreSQL plus immutable attempt rows and River events
are sufficient to reconstruct active authority after process restart; a new
worker instance never inherits the prior instance's fence.

## Known limitations and deferred work

- Existing historical attempts retain `legacy_attempt_id`; new executable
  attempts use UUID `attempt_id` and complete fencing identity.
- This package does not yet normalize validator/repair lifecycle states or
  implement validation-basis, defect, arbitration, dashboard, notifier, or
  campaign orchestration behavior.
- Lease expiry records a timed-out order and exposes explicit requeue; policy
  decisions about retry safety and retry thresholds remain later runner work.
- Execution-envelope/result fencing columns are persistence seams; full result
  reconciliation integration is deferred to the later orchestration package.

## Readiness

IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION

C1 does not independently accept RUN-003. Independent validation must verify
the migration on the target database, exact transaction behavior under
concurrency, stale-result non-propagation, and the remaining RUN-002 acceptance
boundaries.
