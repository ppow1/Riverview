# RUN-004ARV — Acceptance Evidence Binding Repair Revalidation

Package: RUN-004ARV  
Role: C2 independent repair revalidator  
Date: 2026-08-25  
Repair implementation commit: `a95aada42d30e89e70fbffa0899b4bcd1b409883`

## Verdict

**PASS**

The original arbitrary-PASS acceptance defect is resolved. The repaired
lifecycle now compares validator/revalidator claims against the exact durable
`work_orders.result_report` belonging to the authoritative writer or repair
attempt, including result version, implementation/tree reference, and durable
evidence references. The same binding is repeated inside `_accept_locked`, so
the lower-level acceptance path cannot bypass the repair.

## Verification

Repository: `ppow1/Riverview`  
Branch: `main`  
Original RUN-004A commit: `6985f73af677eb331a7dab6188b0b7eab792e6db`  
Repair commit: `a95aada42d30e89e70fbffa0899b4bcd1b409883`

The repair changes only the lifecycle binding gate, the runner’s canonical
result-report fields, and lifecycle tests. No RUN-004B orchestration or
RUN-003 fencing redesign was introduced.

## 1. Original arbitrary-PASS attack — RESOLVED

Independent reproduction:

1. Created a unique package and immutable basis.
2. Completed a fenced writer with a canonical result report.
3. Created and completed an independent validator.
4. Submitted PASS with the correct basis but:
   - `result_version_hash = arbitrary-unverified-value`;
   - `evidence_refs = ()`; and
   - `implementation_ref = None`.

Observed result:

`ARBITRARY_PASS_REJECTED RIV-CAM-0040: validation evidence does not correspond to the exact source result.`

Durable state after rejection:

`STATE_AFTER_ATTACK ('validation_running', 'ready')`

No accepted stage/objective state was produced.

Original arbitrary-PASS defect: **RESOLVED**

## 2. Authoritative binding inspection

`CampaignLifecycleStore._result_binding` requires the completed result report
to contain:

- a nonempty result version;
- a nonempty `commit:<40-hex>` or `tree:<40-64-hex>` implementation reference;
- a version equal to the referenced digest; and
- at least one bounded durable evidence reference.

`_assert_result_binding` locks and reads the source work order and exact source
attempt, requires succeeded status/terminal state and matching basis, then
compares the caller’s version/reference/evidence tuple byte-for-byte with the
stored result report.

`record_validation` additionally requires the validation work order’s source
attempt to equal the current writer or repair attempt. `_accept_locked` repeats
the source-result binding and current repair-attempt checks before changing
stage/objective state.

This is one authoritative source: the fenced completion report in
`work_orders.result_report`. Caller-supplied validation fields cannot replace
it.

Actual result correspondence: **PASS**  
Durable evidence requirement: **PASS**  
Implementation/tree/commit binding: **PASS**  
Lower-level bypass resistance: **PASS**

## 3. Adversarial correspondence cases

The repair tests and independent source inspection cover rejection of:

- arbitrary result version;
- empty evidence;
- missing implementation reference;
- wrong commit/tree reference;
- evidence/result from another package;
- validation against a superseded writer result; and
- revalidation against an older repair result.

Each rejection occurs before validation-result persistence and leaves the
lifecycle non-accepted. The independent arbitrary-PASS probe reproduced the
most important original attack directly.

Arbitrary result-version rejection: **PASS**  
Wrong-writer rejection: **PASS**  
Cross-package isolation: **PASS**  
Stale-result rejection: **PASS**  
Revalidation correspondence: **PASS**

## 4. Valid acceptance and repair paths

The isolated first-pass path succeeded when the validator supplied the exact
stored result version, matching implementation reference, and durable evidence
reference. The isolated writer → FAIL → structured defect → repair →
revalidation PASS path also succeeded and reached acceptance.

The repair gate validates the canonical repair result before creating
revalidation work. Revalidation binds to the current repair attempt and
`_accept_locked` requires that same repair attempt before accepting.

Valid acceptance path: **PASS**

## 5. History, restart, and idempotency

The repair preserves the existing normalized validation result, defect, repair,
revalidation, attempt, and evidence rows. It does not overwrite the failed
validation path. The binding data is stored in PostgreSQL result reports and
validation rows, so it remains available after process/store recreation.

Existing idempotent/conflict behavior remains in place; validation binding is
checked before append/state advancement and cannot silently replace the source
result.

History preservation: **PASS**  
Restart/resume: **PASS**  
Idempotency/conflict: **PASS**

## 6. RUN-003 regression

The repair uses the accepted fenced completion/result seam and does not alter
`FencedReconciliation`, stale-result rejection, successor protection,
expiry/reclaim, crash recovery, reconciliation-failure handling, or late-result
audit semantics.

RUN-003 fencing regression: **PASS**

## 7. Shared-database contamination

The broad lifecycle/fencing runs continue to show the previously documented
shared PostgreSQL residue: accumulated expired active rows appear in the broad
expiry sweep and can cause later fixture claims to fail. Clearing expired
residue with the normal `RelayStore.expire_leases()` recovery operation allows
the relevant isolated tests to pass. The reconciliation test’s global empty
sweep assertion is likewise affected by unrelated expired rows.

No new RUN-004AR-specific contamination or production state-semantics
regression was observed. This remains the pre-existing test-environment issue
classified by RUN-004AV.

Shared-database contamination: **BENIGN PRE-EXISTING**

## 8. Tests and validation evidence

Independent validation included:

- direct original arbitrary-PASS attack: rejected, state remained
  `validation_running`;
- isolated valid first-pass acceptance: passed;
- isolated repair/revalidation acceptance: passed;
- source inspection of `record_validation`, `_assert_result_binding`,
  `_result_binding`, `_accept_locked`, and runner result construction;
- focused repair/lifecycle/fencing tests, with contamination-related failures
  separated from the repair behavior; and
- compileall/import validation: PASS.

The broad suite excluding unavailable MCP test dependencies completed with
known shared-database residue failures only. The focused repair tests supplied
by C1 cover the arbitrary version, empty evidence, missing implementation,
wrong reference, cross-package, superseded writer, and stale repair cases.

## 9. RUN-004B gate

The acceptance-evidence binding repair is independently accepted. RUN-004A is
ready to proceed to the next bounded package.

RUN-004B readiness: **READY_FOR_RUN-004B**

