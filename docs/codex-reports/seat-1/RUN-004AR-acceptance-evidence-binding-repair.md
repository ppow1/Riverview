# RUN-004AR Acceptance Evidence Binding Repair

Package: RUN-004AR  
Role: C1 original RUN-004A implementation writer / repair writer

## Status

`REPAIR_COMPLETE_READY_FOR_REVALIDATION`

This is a targeted repair of the single blocking defect reported by RUN-004AV.
No RUN-004B functionality, new migration, validator orchestration, or RUN-003
fencing redesign was added.

## Defect repaired

RUN-004AV reproduced acceptance with a validator `PASS` while the caller
supplied an arbitrary result version, empty `evidence_refs`, and
`implementation_ref=None`. The stage and objective became accepted even though
the PASS was not bound to an actual completed implementation result.

Before this repair, `record_validation()` persisted the caller-provided fields
and `_accept_locked()` checked only the verdict, basis, attempt linkage, and
blocking defects. The lower-level acceptance API therefore did not enforce
actual result/tree/commit or durable-evidence correspondence.

## Binding authority and corrected ordering

The existing authoritative result store remains `work_orders.result_report`,
written by the accepted fenced completion path. No competing result-version
table or migration was introduced.

`RestrictedRunner._execute_codex` now records the reconciled repository HEAD as
the canonical result identity:

- `result_version_hash`: observed commit SHA;
- `implementation_ref`: `commit:<same SHA>`;
- `evidence_refs`: durable execution/reconciliation references.

The lifecycle gate now requires, before a validation result can be recorded:

1. immutable basis identity and hash match;
2. the exact authoritative source writer or repair attempt;
3. a succeeded source work order and succeeded source attempt;
4. source work-order basis equality;
5. result version equality with the source report;
6. a syntactically valid commit/tree reference whose digest equals the result
   version;
7. at least one durable evidence reference.

The same check is repeated in `_accept_locked()`, so direct invocation of the
lower-level acceptance gate cannot bypass the binding. Repair completion also
requires a canonical repaired result before queuing revalidation.

Corrected effective order:

```text
completed writer/repair result persisted
  -> exact source result/basis/tree/evidence binding checked
  -> independent validation result persisted
  -> acceptance gate repeats exact binding check
  -> accepted state transition
```

If any check fails, the transaction rolls back and the lifecycle remains in
validation or revalidation running state. A PASS verdict alone is not
acceptance.

## Files and symbols changed

- `src/riverview/campaign/lifecycle.py`
  - `CampaignLifecycleStore._result_binding`
  - `CampaignLifecycleStore._assert_result_binding`
  - `handoff_writer_to_validation`
  - `record_validation`
  - `_accept_locked`
  - `record_repair_completion`
- `src/riverview/runner.py`
  - `_execute_codex` result report construction
- `tests/test_campaign_validation_lifecycle.py`
  - canonical result fixtures and acceptance-binding adversarial coverage

No database migration was needed. Existing RUN-004A columns
`work_orders.result_report` and `campaign_validation_results` fields
(`result_version_hash`, `implementation_ref`, and `evidence_refs`) are
sufficient once the authoritative cross-check is enforced.

## Required attack and lifecycle behavior

The added tests cover rejection of:

- arbitrary result version hashes;
- empty evidence references;
- missing implementation references;
- wrong commit/tree references;
- results from another package;
- a validation against a superseded writer result;
- a revalidation against an older repair result.

They assert that the stage remains non-accepted after rejection. Existing happy
path tests prove exact current-result PASS acceptance, and the repair/fail/
revalidation path preserves failed validation and defect history before a valid
revalidation PASS accepts the package.

## Test evidence

Executed successfully in isolated PostgreSQL test processes:

- canonical validator PASS acceptance;
- arbitrary-PASS rejection cases;
- cross-package result rejection;
- superseded writer-result rejection;
- older repair-result revalidation rejection;
- repair and revalidation PASS acceptance;
- stale validator rejection;
- Python compile/import validation via `python -m compileall -q src
  tests/test_campaign_validation_lifecycle.py`.

The complete lifecycle file and RUN-003-related suite were also executed. Some
combined runs reproduce pre-existing shared-database lease residue: stale rows
are returned by the broad expiry sweep and occasionally prevent a later test
claim. This is the benign test contamination already classified by RUN-004AV;
RUN-004AR does not broaden scope into cleanup of that residue. The isolated
repair and acceptance cases pass, and no production cleanup behavior was
changed.

## Preserved behavior and limitations

The accepted RUN-003 exact fencing, stale-result handling,
`FencedReconciliation`, successor protection, expiry/reclaim, crash recovery,
and reconciliation-failure semantics were not redesigned. The new gate uses
the existing completed-result and fencing seams.

GitHub publication remains a later visibility concern; local durable result and
evidence fields are the acceptance authority. This package does not implement
RUN-004B dispatch/orchestration, dashboard, notifier, or broader artifact
management.

Independent C2 revalidation remains required.
