# RUN-003RV — Stale-Result Reconciliation Repair Revalidation

Package: RUN-003RV  
Role: C2 independent repair revalidator  
Date: 2026-08-25

## Verdict

**FAIL — ORIGINAL BLOCKING DEFECT REMAINS**

The repair correctly adds an exact five-field pre-reconciliation check and
closes the stale-before-check path. It does not close the required authority
boundary: the `FOR UPDATE` lock held by `assert_fence_current` is released
before `reconcile_repository` runs. A worker can therefore pass the check,
lose or be superseded after the check, and still perform authoritative
reconciliation/accepted-decision work.

## Implementation verification

Implementation repository: `ppow1/Riverview`  
Repair commit:
`a2d28cbb67947218b561c7d4a845af5b4ee2a18d`

The local worktree is at that commit. The repair changes only:

* `src/riverview/relay/store.py` — `assert_fence_current`;
* `src/riverview/runner.py` — pre-reconciliation gate; and
* `tests/test_runner_policy.py` — stale, valid, and reconciliation-failure
  tests.

## 1. Actual call order

`RestrictedRunner._execute_codex` in `src/riverview/runner.py:76` now runs:

1. persist the result;
2. call `self.store.assert_fence_current(self._identity(work))`;
3. on rejection, call `complete_fenced` only for late audit and return stale;
4. on success, call `reconcile_repository`;
5. record accepted reconciliation; and
6. call `complete_fenced` for terminal work-order advancement.

This is the claimed order for the interval immediately surrounding the check.
The repair does prevent a worker already stale when the check executes from
reaching reconciliation.

## 2. Exact fence validation

`RelayStore.assert_fence_current` in `src/riverview/relay/store.py:356`
checks all required identity components in one query:

* `work_order_id`;
* `active_attempt_id` / `attempt_id`;
* `lease_generation`;
* `fencing_token`; and
* `worker_instance_id`.

It also requires work-order status `claimed` or `running` and
`lease_expires_at > now()`. The query uses `FOR UPDATE`.

The exact helper semantics are sound for the instant of its query. The defect
is the lifetime of the ownership protection after that query.

## 3. Primary stale race result

### Stale before the pre-check — PASS

The new `test_stale_codex_result_is_rejected_before_reconciliation` models a
successor replacing Worker A before A reaches the check. It observes:

`persist → fence rejection → late audit`

and asserts no reconciliation, no accepted decision, and unchanged successor
identity. This test exercises the runtime ordering boundary rather than only a
standalone helper.

The live PostgreSQL probe independently verified:

* current exact identity passes `assert_fence_current`;
* after lease expiry, the same identity is rejected;
* late `complete_fenced` is rejected; and
* the historical attempt is marked `(late_or_stale=true,
  terminal_state='late_result')`.

### Stale after the pre-check — FAIL

`assert_fence_current` is implemented as:

```python
with connect(self._config) as connection, connection.cursor() as cursor:
    ... SELECT ... FOR UPDATE
```

`src/riverview/database/connection.py:80` defines `connect` as a
transaction-scoped connection context. When `assert_fence_current` returns,
that context exits and the row lock is released. `reconcile_repository` is a
separate call after the helper returns, using a separate transaction and no
second exact-fence reservation/check.

Therefore this sequence remains possible:

1. Worker A calls `assert_fence_current` and passes.
2. The helper transaction closes and releases its lock.
3. A lease expires, or the order is otherwise fenced/reclaimed by Worker B.
4. Worker A enters `reconcile_repository`.
5. Worker A updates execution evidence/envelope state and can record accepted
   reconciliation before its later `complete_fenced` call rejects it.

`ResultReconciler.reconcile_repository` in
`src/riverview/autonomy/control.py:928` performs database updates and emits
`execution.reconciled`; `record_decision` at line 988 writes
`reconciliation_records` and emits a reconciliation event. These are the
authoritative side-effect boundaries named in the original RUN-003V defect.

This is not a nanosecond-only objection: PostgreSQL lease expiry/reclaim uses
its own transaction and `FOR UPDATE SKIP LOCKED` in `RelayStore.expire_leases`
(`src/riverview/relay/store.py:405`). The ownership lock is not held across
the side effect it is supposed to protect.

Stale-before-reconciliation overall: **FAIL**

The repair closes the stale-before-check subcase but not the full required
stale-result invariant, which includes loss of authority after the check and
before reconciliation.

## 4. Valid current path — PASS

`test_current_codex_result_reconciles_before_terminal_completion` observes:

`persist → fence → reconcile → accepted → complete`

The exact current path reaches reconciliation and accepted decision before
fenced terminal completion, as required by the repaired intended ordering.

Valid current path: **PASS**

## 5. Reconciliation failure — PASS

`test_reconciliation_failure_does_not_complete_current_work` verifies that a
valid pre-check followed by reconciliation failure records a checkpoint and
does not call successful `complete_fenced`. The source `try/except` around
`reconcile_repository` does not produce a false terminal success.

Reconciliation-failure safety: **PASS**

## 6. Successor authority and late audit

For the stale path detected by `complete_fenced`, the existing implementation
locks the work order, rejects the mismatched active tuple, and records late
evidence against the historical attempt. `_record_late_result` updates only
the old attempt and emits `runner.result.late_rejected`; it does not clear or
replace the successor active tuple.

The live probe confirmed late audit persistence. The successor-preservation
behavior for a stale result detected at terminal completion is therefore
passing.

However, in the post-check race, reconciliation side effects can occur before
the stale worker reaches `complete_fenced`. That is why the overall
successor/authoritative-state invariant remains failed even though the final
fenced update itself is safe.

Successor authority preservation: **FAIL for the complete required race**  
Late-result audit: **PASS for detected stale completion**

## 7. Independent regression tests

Command run:

```text
PYTHONPATH=src python -m pytest -q \
  tests/test_runner_policy.py \
  tests/test_campaign_fencing.py \
  tests/test_relay_contract.py \
  tests/test_relay_worker.py \
  tests/test_objective_stage_model.py \
  tests/test_river_event.py
```

Result: **all tests passed**.

The suite includes the new stale-ordering, valid-ordering, and reconciliation
failure tests, as well as claim, competing fence components, heartbeat,
progress idempotency, expiry/retry, late completion, worker identity, River,
relay, and current-phase authority tests.

The new stale test replaces the store with a test double whose active identity
changes before `assert_fence_current`; it does not hold a real PostgreSQL
transaction open across reconciliation and expire/reclaim. No test covers
the post-check lease-loss interval identified above.

## 8. Required correction

RUN-003R is not ready for acceptance. The implementation must protect the
whole authoritative reconciliation boundary, not only perform a check before
it. The minimum correction is to make the fence reservation/validation and
the authoritative reconciliation/acceptance decision share a valid ownership
guard, or to perform an equivalent exact-fence revalidation atomically at the
side-effect boundary. The correction must make a worker that loses authority
after the initial check fail closed before reconciliation/accepted decision.

The repair should add a real PostgreSQL race test that interleaves lease
expiry/reclaim between the pre-check and reconciliation and proves that the
stale worker cannot write reconciliation or accepted decision state.

No broader Campaign Runner redesign is required for this finding.

## RUN-004A readiness

RUN-004P identified direct collision with `_execute_codex`, fencing/completion
boundaries, and related fencing tests. Those collisions are not resolved for
implementation purposes because the authority guard still requires repair.

RUN-004A readiness: **REPAIR_REQUIRED**

