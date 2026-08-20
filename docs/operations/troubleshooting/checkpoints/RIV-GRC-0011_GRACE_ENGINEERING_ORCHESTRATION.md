# RIV-GRC-0011 — Grace engineering orchestration

## Symptom

An approved objective remains ready, reaches Grace, or creates a work order but
does not progress to authoritative execution and reconciliation.

## Diagnostic sequence

1. Read the objective, stage, authority, engineering-intent, work-order,
   execution-envelope, result, and reconciliation rows from PostgreSQL.
2. Compare the latest River sequence with `cme_runtime_status.last_river_sequence_seen`.
3. Confirm CME is listening and that startup replay completed; a fresh heartbeat
   with `STARTING` state is not progress.
4. Confirm the durable authority still binds the exact specification, seed,
   objective, stage, repository, base SHA, allowed paths, capability, action,
   write policy, acceptance criteria, and evidence requirements.
5. Distinguish the boundary: Grace formation, Relay queue/lease, provider
   execution, authoritative copy-back, or reconciliation.
6. For a failed work order, preserve the failed attempt and inspect its stable
   checkpoint. Use only the registered retry/revalidation path; do not rewrite
   history or dispatch the provider directly.

## Recovery rules

Grace is an orchestrator, not an observer. Approved bounded engineering work
must either progress, fail with a specific recoverable or terminal reason, or
explicitly require Steward action. It must not silently stall.

Pat approval is not repeated for an unchanged, still-valid scope. A transient
provider or transport failure may use the registered bounded retry policy. A
stale base, material scope drift, missing authority, contradictory evidence, or
unsafe retry remains a governed checkpoint and follows stale-base or Steward
review rules.

Failed work-order and execution records remain immutable evidence. A failed
provider result is never reconciled as success, and a bounded write with no
authoritative changed path is not successful merely because the provider exited
zero or returned completion prose.

## Boundary identification

- `RIV-GRC-*`: Grace/CME evaluation, formation, cursor, or recovery.
- `RIV-WRK-*`: Relay queue, lease, worker, or successor-attempt handling.
- `RIV-EXE-*`: execution envelope, provider, sandbox, base, or bounded adapter.
- `RIV-REC-*`: authoritative evidence and reconciliation.
- `RIV-DB-*`: PostgreSQL connection, transaction, migration, or projection.

Verify recovery at the next durable boundary and after restart/replay. A unit
cycle or healthy HTTP endpoint alone does not prove the end-to-end path.
