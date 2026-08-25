# RUN-003R2 — Close Post-Check TOCTOU Race Across Authoritative Reconciliation

Package: RUN-003R2
Role: C1 repair writer
Status: REPAIR_COMPLETE_READY_FOR_REVALIDATION
## C2 defect and root cause

RUN-003RV confirmed that RUN-003R's `assert_fence_current` checked the exact
five-field identity correctly, but its transaction ended when the helper
returned. The `FOR UPDATE` lock was released before
`reconcile_repository(...)`, so lease expiry/reclaim could supersede A after
the check and before authoritative reconciliation or accepted-decision work.

The defect was a real check/use gap, not an insufficient identity predicate.

## Chosen authority-protection mechanism

RUN-003R2 adds `RelayStore.reconciliation_authority`, a transaction-scoped
`FencedReconciliation` guard. It locks the exact active `work_orders` row with
the complete identity:

- `work_order_id`
- `attempt_id`
- `lease_generation`
- `fencing_token`
- `worker_instance_id`

The guard also requires `claimed`/`running` state and a non-expired lease at
entry. The row lock remains held across:

1. repository/Git reconciliation;
2. accepted reconciliation decision recording; and
3. terminal success update through `FencedReconciliation.complete`.

This is the smallest existing-architecture protocol because
`expire_leases` already uses `FOR UPDATE SKIP LOCKED`. No reservation table,
distributed transaction framework, or migration is required.

## Why the TOCTOU interval is closed

`assert_fence_current` returned a fact whose lock had already been released.
`reconciliation_authority` instead returns a live transaction-scoped guard.
While that context is active, expiry/reclaim cannot lock and supersede the
work-order row. It skips the locked row rather than becoming authoritative.
The protected worker either completes reconciliation and fenced terminal
completion under the same held row authority, or the context exits without
terminal success.

The runner now executes the successful Codex path as:

`persist result → acquire protected authority → reconcile repository → record accepted decision → protected fenced completion → release transaction`

If protected authority cannot be acquired, the runner preserves late audit
evidence through the existing fenced late-result path and does not reconcile.

## Expiry/reclaim behavior

While the guard is active, `RelayStore.expire_leases` cannot obtain the locked
row and therefore cannot mark the attempt timed out or enable a successor.
After the guard completes, normal expiry/retry behavior remains available.
If the lease timestamp passes while A is protected, A may complete the already
authorized protected section; the lock prevented a competing authoritative
transition during that section.

## Crash and failure recovery

The guard uses the existing transaction-scoped PostgreSQL connection. If the
runner or reconciliation process fails, PostgreSQL rolls back/closes the
transaction and releases the row lock. No permanent reservation remains. The
normal expiry sweeper can then mark the still-active expired attempt timed out,
and the existing requeue/new-fenced-attempt path can recover it.

If repository reconciliation raises while authority is held, the runner
records the existing checkpoint decision, does not call protected terminal
completion, and exits the context. The work therefore remains observable and
recoverable rather than falsely accepted.

## Files and symbols changed

- `src/riverview/relay/store.py`
  - Added `FenceNotCurrentError`.
  - Added `FencedReconciliation` with same-transaction terminal completion.
  - Added `RelayStore.reconciliation_authority`.
- `src/riverview/relay/__init__.py`
  - Exported `FenceNotCurrentError` for the runner seam.
- `src/riverview/runner.py`
  - Replaced the released-lock pre-check path with the transaction-scoped
    reconciliation authority context.
  - Kept late-result audit, accepted-decision ordering, and failure behavior.
- `tests/test_runner_policy.py`
  - Updated runner seam tests for protected authority.
  - Preserved stale, valid, and reconciliation-failure ordering coverage.
- `tests/test_campaign_fencing.py`
  - Added real PostgreSQL protected-reconciliation/expiry race coverage.
  - Added crash/failure lock-release and expiry-recovery coverage.

No database migration or schema change was necessary.

## Real PostgreSQL race evidence

`test_reconciliation_authority_blocks_expiry_during_real_postgres_side_effect`
uses the configured PostgreSQL database and actual `RelayStore` transactions:

1. A claims a real fenced work order.
2. A acquires `reconciliation_authority` and holds the real `FOR UPDATE` lock.
3. The test lets A's lease become logically expired.
4. A concurrent real `expire_leases` transaction attempts reclaim.
5. The sweeper returns no expired attempt while A owns the lock.
6. A performs the protected-side-effect marker and completes successfully.
7. The final work order is `succeeded` with no active attempt.

This proves the unsafe state “B becomes authoritative while A performs
protected reconciliation” cannot occur through the expiry/reclaim path.

`test_reconciliation_authority_failure_releases_lock_for_expiry_recovery`
raises inside the protected context, then expires and reclaims the same real
attempt. This proves failure does not leave the work permanently locked.

## Path results

### Valid current path — PASS

The runner-policy test proves protected authority acquisition precedes
reconciliation, accepted decision recording follows reconciliation, and
protected completion follows acceptance.

### Stale/late path — PASS

An attempt that cannot acquire the exact protected authority is audited through
the existing late-result path and returns stale without reconciliation or
accepted decision. Existing PostgreSQL terminal fencing and late-result event
coverage remains passing.

### Reconciliation failure — PASS

The current fence may be acquired, but a reconciliation exception records a
checkpoint and exits without terminal success. The guard releases normally for
recovery.

### Successor protection and recovery — PASS

Expiry/reclaim is excluded during the protected interval and remains possible
after context failure/release.

## Tests executed

Focused RUN-003R2 and fencing/regression set:

```text
50 passed in 7.82s
```

Full repository suite in the dependency-complete repository virtual
environment:

```text
275 passed, 1 warning in 169.76s
```

The warning is the pre-existing Pydantic settings unresolved-forward-reference
warning. Changed runtime and test files also passed `compileall`. Ruff was not
available in the active environment.

## RUN-004A collision/readiness

The `_execute_codex` fencing/completion boundary is now protected by a stable
transaction-scoped authority seam. No validator orchestration, dashboard,
notifier, Grace integration, or other RUN-004 functionality was added.

RUN-004A should remain gated until independent C2 revalidation accepts this
repair.
