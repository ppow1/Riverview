# RUN-004BV — One-Go Campaign Runner Integration Validation

Package: RUN-004BV  
Role: C1 independent implementation validator  
Implementation commit: `41a55e70ecaf1ca66d8cd890e7f382fde53c6e5b`  
Implementation repository: `ppow1/Riverview`, branch `main`

## Verdict

**FAIL — BLOCKING DEFECTS REMAIN**

The first-pass writer → independent validator path works, but the required
writer → validator FAIL → repair → revalidation → acceptance path does not
complete against the actual PostgreSQL-backed implementation.

## Evidence inspected

I independently verified that `origin/main` points to the reported commit and
inspected the scoped implementation and tests:

- `src/riverview/campaign/one_go.py`
- `src/riverview/campaign/lifecycle.py`
- `src/riverview/relay/store.py`
- `tests/test_campaign_one_go.py`
- `tests/test_campaign_one_go_postgres.py`

The implementation uses the accepted RUN-004A lifecycle and the accepted
RUN-003 fenced relay APIs. The implementation report is
`docs/codex-reports/seat-3/RUN-004B-one-go-runner-integration.md`.

## Blocking finding

### Structured repair defects cannot cross the one-go persistence boundary

Exact reproduction on a newly created objective/stage:

1. Queue and claim a writer.
2. Return a valid writer result.
3. Return a validator `FAIL` containing the required structured
   `DefectInput` tuple.
4. Run the actual `CampaignOneGoRunner` with the actual PostgreSQL relay and
   lifecycle stores.

Observed outcomes:

```text
writer: succeeded, validator_queued
validator: failed, Object of type DefectInput is not JSON serializable
stage: failed / ready
```

No `repair_writer` or `revalidator` work is dispatched. The required repair
cycle therefore cannot reach acceptance.

The relevant implementation path is:

- `one_go.py:128` calls `RelayStore.complete_fenced`;
- `one_go.py:129` calls `_advance_completed`;
- `one_go.py:167-180` forwards `execution["defects"]` directly to
  `CampaignLifecycleStore.record_validation`;
- the actual PostgreSQL result persistence serializes the execution payload,
  and a `DefectInput` object is not JSON serializable.

The production-facing PostgreSQL test uses the same structured input at
`tests/test_campaign_one_go_postgres.py:49-63`. It fails independently on a
fresh objective, not because another objective's stale rows were selected.

Minimum repair required: make the one-go result/evidence boundary accept and
durably encode the structured defect representation required by RUN-004A,
without weakening the accepted lifecycle or evidence gate, then prove the
complete repair/revalidation path with PostgreSQL.

## Capability results

| Capability | Result | Evidence |
|---|---|---|
| One-go writer/validator orchestration | **PASS for first-pass only; overall FAIL** | PostgreSQL first-pass test passed; repair path is blocked above. |
| Independent validator enforcement | PASS | RUN-004A gate is used through `record_validation`; no direct acceptance call was added in `one_go.py`. Accepted RUN-004A enforcement remains in `lifecycle.py`. |
| Evidence-bound acceptance | PASS for the delegated gate | `_advance_completed` delegates validation to `record_validation`; accepted RUN-004ARV gate checks basis/result/tree/evidence correspondence. No higher-level acceptance bypass was found. |
| Repair/revalidation orchestration | **FAIL** | Actual PostgreSQL repair test fails before `repair_writer` dispatch because structured defects cannot be serialized. |
| Revalidator independence | PASS by delegated lifecycle design; end-to-end path not reachable | RUN-004A owns the identity gate; no RUN-004B bypass was found. |
| RUN-003 fencing integration | PASS in the one-go boundary | `one_go.py:113-129` claims with fenced identity and calls `complete_fenced`; stale outcomes are handled before lifecycle handoff. |
| Stale-result handling | PASS in focused unit coverage | `tests/test_campaign_one_go.py` stale completion test passes; stale result returns without lifecycle handoff. |
| Successor authority preservation | PASS by accepted RUN-003 seam; no new bypass found | RUN-004B calls accepted relay completion rather than replacing it. |
| Objective-scoped isolation | PASS by source inspection and objective-scoped claim/query predicates | `objective_id` is passed to claim and used in `_scoped_work_order_id` and admission. Dedicated live proof was limited by shared database residue. |
| Idempotency | PASS in focused unit coverage | bounded runner and repeated processing tests pass. |
| Bounded execution | PASS | `CampaignOneGoRunner.run()` has explicit `max_steps`; each tick dispatches at most one role. |
| Restart/resume | PASS in focused unit coverage; durable repair resume is blocked by the defect | Existing restart test passes and runner derives work from durable rows. |
| PostgreSQL first-pass proof | PASS | `test_live_one_go_writer_validator_pass_requires_no_manual_handoff` passed in isolation. |
| PostgreSQL repair-loop proof | FAIL | Fresh-objective reproduction fails with `DefectInput is not JSON serializable`. |
| History preservation | PASS for the paths reached; repair history cannot be completed | RUN-004A lifecycle retains source/result history; no repair history is created because the defect boundary fails first. |
| Failure safety | PASS for the observed serialization failure in the narrow sense | The validator work is failed and the stage is not accepted; however, the required recoverable repair transition is absent. |
| Downstream dispatch gating | PASS by inspection | No downstream accepted dispatch occurs before the delegated lifecycle gate. |

## Adversarial and regression tests

Executed independently in an isolated worktree at the implementation commit:

- `pytest -q tests/test_campaign_one_go.py`: **6 passed**.
- First-pass PostgreSQL test: **1 passed**.
- Repair-loop PostgreSQL test: **1 failed**, with the deterministic
  structured-defect serialization error described above.
- Focused RUN-004A acceptance-binding tests: the acceptance-binding cases that
  ran to completion passed; setup failures were caused by global expired-row
  residue preventing unrelated claims.
- `python -m compileall -q src`: **PASS**.

The broader selected run had three additional failures. They are classified
as **PRE-EXISTING SHARED-DATABASE CONTAMINATION**, not RUN-004B defects:

1. The RUN-003 reconciliation test's `expire_leases()` observed five expired
   rows belonging to other accumulated test state.
2. Two RUN-004A setup paths could not claim newly queued work because the
   shared relay database contained unrelated expired/claimed residue.

These failures do not explain the repair-loop failure: the repair-loop
reproduction used a fresh objective and reached the actual serialization
exception before any repair claim could be attempted.

## Scope and later capabilities

RUN-004B did not improperly implement dashboard, notifier, exceptional
arbitration, model/provider selection, GPU scheduling, Grace integration, or a
new schema. Those remain separately scoped. The implementation correctly uses
the accepted RUN-003 and RUN-004A seams.

The accepted RUN-004P decomposition identifies RUN-004A and RUN-004B as the
Campaign Runner core packages. No additional required core package was found
in the authoritative RUN-002/RUN-004P material. However, RUN-004B itself is
not accepted because its required repair-loop behavior is incomplete.

## Required disposition

`RUN-004B` requires targeted repair of the structured defect serialization /
result persistence boundary, followed by independent PostgreSQL revalidation
of:

```text
writer → validator FAIL → structured defects → repair writer
→ independent revalidator PASS → evidence-bound acceptance
```

Campaign Runner core implementation: **INCOMPLETE**  
Campaign Runner readiness: **REPAIR_REQUIRED**
