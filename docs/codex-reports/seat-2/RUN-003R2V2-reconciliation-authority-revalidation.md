# RUN-003R2V2 — Final Campaign Runner Reconciliation-Authority Race Revalidation

Package: RUN-003R2V2  
Role: C2 independent repair revalidator  
Date: 2026-08-25

## Verdict

**PASS**

RUN-003R2 closes the remaining reachable stale-reconciliation race. The
authoritative reconciliation interval is protected by a transaction-scoped
exact-fence row lock, and the lock remains held through reconciliation,
accepted-decision recording, and protected terminal completion. A successor
cannot become authoritative during that interval.

## Verification basis

Implementation commit:
`19448911550b3bd5c42299c3aa44ee44b2f3b6fc`

Repair report:
`docs/codex-reports/seat-1/RUN-003R2-reconciliation-authority-repair.md`

The local Riverview worktree is at the reported repair commit. Unrelated
spatial/operator worktree changes were not staged or modified.

## 1. Actual protection mechanism

RUN-003R2 adds `RelayStore.reconciliation_authority` in
`src/riverview/relay/store.py:423`, returning a transaction-scoped
`FencedReconciliation` guard.

On entry it selects the active `work_orders` row using `FOR UPDATE` and exact
matching of:

* `work_order_id`;
* `active_attempt_id` / `attempt_id`;
* `lease_generation`;
* `fencing_token`; and
* `worker_instance_id`.

It also requires `claimed` or `running` state and
`lease_expires_at > now()`.

The PostgreSQL connection/transaction remains open while the context is
active. `FencedReconciliation.complete` at line 72 performs an exact fenced
terminal update on the same cursor/transaction and clears the active fence.

`RestrictedRunner._execute_codex` now uses this protected authority around:

1. repository reconciliation;
2. accepted reconciliation decision recording; and
3. protected terminal completion.

This is a protected lease/fence state mechanism, not merely a released
pre-check and not a work-order-ID-only reservation.

## 2. Primary invariant

The implementation establishes the required invariant:

> No worker can perform authoritative reconciliation after another attempt
> has become authoritative.

`expire_leases` also locks the work-order row with `FOR UPDATE SKIP LOCKED`.
While A holds the reconciliation authority lock, expiry/reclaim cannot lock
or supersede that row. A either completes the protected section or its
transaction closes/rolls back, after which normal expiry/retry may proceed.

There is no reachable state in the protected path where B is authoritative
while A performs the protected authoritative reconciliation side effects.

## 3. Real PostgreSQL concurrency evidence

The added test
`test_reconciliation_authority_blocks_expiry_during_real_postgres_side_effect`
uses actual configured PostgreSQL connections and actual `RelayStore`
transactions. It:

1. claims a real fenced attempt A;
2. enters `reconciliation_authority` and holds the real row lock;
3. lets A’s lease become logically expired;
4. runs `expire_leases` concurrently;
5. observes no expired/reclaimed attempt while A holds the lock;
6. performs the protected side-effect marker and protected completion; and
7. verifies the work order is `succeeded` with no active attempt.

An independent live probe reproduced the same behavior:

```text
locked_expiry_result= [] final= ('succeeded', None)
```

The probe also independently exercised failure/recovery:

```text
failure_recovery= True successor= True new_attempt= True
```

This proves expiry/requeue/new-attempt behavior resumes after the protected
transaction is released.

Real PostgreSQL concurrency: **PASS**  
Post-check TOCTOU race: **CLOSED**

## 4. Expiry, reclaim, and crash recovery

During protected reconciliation, expiry cannot create a successor because the
work-order row is locked. The protection is bounded by the PostgreSQL
transaction and the reconciliation call; it does not permanently reserve a
separate row or create a migration-backed stuck reservation.

The failure test
`test_reconciliation_authority_failure_releases_lock_for_expiry_recovery`
raises inside the protected context, then expires the attempt, requeues it,
and obtains a new fenced attempt. The independent live probe confirmed the
same sequence.

If the worker process fails, PostgreSQL closes/rolls back the transaction and
releases the row lock. The still-active/expired work order remains recoverable
by the existing sweeper. Recovery cannot occur early while A’s transaction
still holds the row lock.

Expiry/reclaim safety: **PASS**  
Crash/recovery: **PASS**

The protected section uses an existing row lock and no additional lock-order
cycle was found. `SKIP LOCKED` avoids waiting behind the active reconciliation
row; after context release, normal expiry/retry proceeds. No indefinite
reservation path is introduced.

## 5. Valid and failure paths

### Valid current path

The runner-policy test verifies:

`persist → protected authority → reconcile → accepted decision → protected complete`

The exact current attempt succeeds and terminal completion clears active
authority.

Valid path: **PASS**

### Reconciliation failure

The runner catches reconciliation failure, records a checkpoint, does not call
protected terminal completion, and exits the authority context. The failure
test then proves expiry/recovery remains possible.

Reconciliation-failure safety: **PASS**

### Stale before protected entry

The existing stale ordering test was updated to the new context seam. If A is
already superseded, `reconciliation_authority` raises
`FenceNotCurrentError`; the runner performs late-result audit through the
existing fenced path and returns stale without reconciliation or accepted
decision recording.

Stale-before-entry behavior: **PASS**

## 6. Exact identity and successor protection

The authority-entry SQL requires all five accepted identity components, plus
active status and unexpired lease. Protected completion repeats the exact
attempt/generation/token/worker predicates.

A stale worker cannot clear, replace, extend, or complete a successor’s
authority through this path. `expire_leases` only acts after it obtains the
same work-order row lock, which it cannot obtain while A’s protected context
is active.

Exact fence identity: **PASS**  
Successor authority protection: **PASS**

## 7. Late-result audit

If authority acquisition fails, the runner retains the stale result as late
evidence through the existing `complete_fenced`/`_record_late_result` path.
The originating attempt ID remains attached, `late_or_stale` is set, and the
`runner.result.late_rejected` River event remains produced. The repair does
not silently discard stale results.

Late-result audit: **PASS**

## 8. Independent regression validation

Focused command:

```text
PYTHONPATH=src python -m pytest -q \
  tests/test_runner_policy.py \
  tests/test_campaign_fencing.py \
  tests/test_autonomy_control.py \
  tests/test_objective_stage_model.py \
  tests/test_status_view.py \
  tests/test_river_event.py \
  tests/test_relay_contract.py \
  tests/test_relay_worker.py
```

Result: **50 passed**.

This independently preserves passing coverage for claim and competing claim
exclusion, heartbeat/progress distinction, progress idempotency, expiry and
retry/new attempt, wrong token/generation/worker identity, stale completion,
worker identity, stale-before-entry, valid reconciliation, reconciliation
failure, late audit, River events, and absence of
`objectives.active_stage_id` authority.

## 9. RUN-004A gate

The previously identified collision with `RestrictedRunner._execute_codex`,
fencing/completion boundaries, and fencing tests is now resolved sufficiently
for the next package: the active reconciliation boundary has a stable
transaction-scoped authority seam and independent real-PostgreSQL evidence.

RUN-004A readiness: **READY_FOR_RUN-004A**

