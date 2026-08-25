# RUN-003R — Stale-Result Reconciliation Repair

Package: RUN-003R  
Role: C1 repair writer  
Status: REPAIR_COMPLETE_READY_FOR_REVALIDATION

## Defect repaired

C2 identified that `RestrictedRunner._execute_codex` crossed the
repository-reconciliation and accepted-decision boundaries before invoking
`RelayStore.complete_fenced`. A worker could lose its lease, be superseded,
return a successful Codex result, reconcile the repository, and record an
accepted decision before terminal fencing rejected the stale result.

The repair adds a bounded exact-attempt authority gate immediately before
repository reconciliation. The gate requires the complete active identity:

- `work_order_id`
- `attempt_id`
- `lease_generation`
- `fencing_token`
- `worker_instance_id`

It also requires an active `claimed`/`running` state and a non-expired lease.

## Runtime ordering

Before repair, the effective successful path was:

1. Codex child returns.
2. Persist execution result.
3. `ResultReconciler.reconcile_repository(...)`.
4. `record_decision(..., "accepted", ...)`.
5. `complete_fenced(...)`.

After repair, the path is:

1. Codex child returns.
2. Persist execution result as durable evidence.
3. `RelayStore.assert_fence_current(exact_identity)`.
4. If stale/invalid: attempt late-result audit through `complete_fenced`,
   return `stale`, and stop. No reconciliation or accepted decision runs.
5. If current: reconcile the repository.
6. Record the accepted reconciliation decision.
7. Run `complete_fenced(...)` for terminal work-order advancement.

The final completion remains after reconciliation, so reconciliation failure
does not become false successful completion.

## Files and symbols changed

- `src/riverview/relay/store.py`
  - Added `RelayStore.assert_fence_current`.
  - Uses a PostgreSQL row lock and exact five-component identity comparison,
    active lifecycle check, and lease-expiry check.
- `src/riverview/runner.py`
  - Added the pre-reconciliation fence gate in
    `RestrictedRunner._execute_codex`.
  - Stale results are preserved as late evidence through the existing fenced
    terminal path and return without authoritative reconciliation.
- `tests/test_runner_policy.py`
  - Added stale successor-race ordering test.
  - Added valid current-result ordering test.
  - Added reconciliation-failure safety test.

No migration or schema change was required. No RUN-004+ functionality was
added.

## Stale path behavior

The regression test models Worker A beginning Codex execution, a successor
claiming authority before A returns, and A then reaching the runner’s fence
gate. It proves:

- the successor remains the active authority;
- A is returned as `stale`;
- late evidence is retained through the fenced audit path;
- `reconcile_repository` is not called;
- accepted reconciliation is not recorded;
- downstream publication/dispatch cannot be reached by A.

The existing PostgreSQL `complete_fenced` behavior remains responsible for
persisting late-result evidence without changing the successor’s active tuple.

## Valid path behavior

The valid-result regression proves this order:

`persist -> fence gate -> reconcile -> accepted decision -> fenced complete`

An exact current attempt therefore reconciles successfully and only then
advances terminal work state.

## Reconciliation-failure behavior

The failure regression proves that when the current fence is valid but
`reconcile_repository` raises:

- a checkpoint decision is recorded;
- terminal completion is not called;
- the work is not falsely marked accepted/completed by this path.

## Tests executed

Focused RUN-003R and fencing suite:

```text
48 passed in 7.03s
```

This included the new runner-policy tests, `tests/test_campaign_fencing.py`,
and directly relevant autonomy, objective-stage, status, River-event, Relay
contract, and Relay worker tests.

The dependency-complete repository virtual environment also ran the complete
repository suite to 100% with only the pre-existing Pydantic settings forward
reference warning. A system-interpreter full-suite attempt was not used as
engineering evidence because its environment lacked the unrelated `mcp`
dependency during collection.

Compilation of the changed runtime and test files passed. Ruff was unavailable
in the active environment.

## Scope confirmation

This repair changes only the end-to-end stale-result authority boundary. It
does not implement validator assignment, repair/revalidation orchestration,
dashboard, notifier, one-GO orchestration, Grace integration, or GPU/resource
scheduling.

C1 does not accept RUN-003R. The implementation is ready for independent C2
revalidation of the stale-result race.

