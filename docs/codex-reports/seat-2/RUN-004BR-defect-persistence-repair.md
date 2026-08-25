# RUN-004BR Defect Persistence / Repair-Loop Serialization Repair

Package: RUN-004BR
Role: C2 targeted repair writer
Status: REPAIR_COMPLETE_READY_FOR_REVALIDATION

## 1. Blocking defect

RUN-004BV found that the first-pass PostgreSQL writer/validator path worked,
but a validator FAIL containing structured `DefectInput` values failed when
`RelayStore.complete_fenced` serialized the execution result to JSONB. The
repair writer and revalidator therefore could not be dispatched.

## 2. Root cause and repair

`DefectInput` is a frozen structured lifecycle value, not a JSON-native value.
The one-go executor result was passed directly to the fenced result persistence
boundary. The repair adds one canonical representation at that boundary:

```json
{
  "acceptance_criterion_ref": "...",
  "severity": "blocking|non_blocking",
  "expected_behavior": "...",
  "observed_behavior": "...",
  "evidence_ref": "...",
  "required_repair": "..."
}
```

`DefectInput.as_payload()` validates the complete field set, non-empty string
values, allowed severity, and the existing bounded-field requirement.
`DefectInput.from_payload()` requires the exact key set and reconstructs the
structured value with the same validation. No `str(defect)` conversion is
used.

In `CampaignOneGoRunner`, execution results are normalized before
`complete_fenced`, so PostgreSQL JSONB receives deterministic dictionaries.
After reload/normalization, `_advance_completed` reconstructs `DefectInput`
objects before calling `record_validation`. This preserves the existing
lifecycle API and avoids a second persistence architecture.

## 3. Evidence

The focused structured round-trip test serializes a `DefectInput` through
`json.dumps`/`json.loads`, reconstructs it with `from_payload`, and compares
all six semantic fields. Malformed key sets and over-bound fields fail closed.

An isolated-objective live PostgreSQL proof exercised:

`writer -> independent validator FAIL with DefectInput -> durable JSONB defect
-> repair_writer -> independent revalidator PASS -> accepted completion`.

The persisted validator result contained the six-field defect dictionary. A
new lifecycle/store read reconstructed the same defect. The database showed
the validation defect in `resolved` state with both repair and resolution
attempt links populated, and the objective stage reached `accepted` /
`completed`.

The PostgreSQL test additionally verifies the JSONB report can be loaded and
round-tripped after the run, rather than only proving an in-memory conversion.

## 4. History, restart, and multiple defects

The original writer result, validator FAIL result, structured defect row,
repair attempt, revalidation attempt, and final acceptance remain separate
durable records. Acceptance does not overwrite the failed validation history.

The durable representation is reconstructed by a fresh lifecycle/store
instance from persisted JSONB. Multiple defects are represented as an ordered
list of independently validated dictionaries; no flattening or silent loss is
introduced. Malformed persisted entries fail through the existing lifecycle
error path before becoming repair input.

## 5. Preserved behavior

- First-pass writer/validator PASS and evidence-bound acceptance: PASS in the
  existing focused PostgreSQL/unit coverage.
- Writer/validator and repair-writer/revalidator independence: unchanged;
  the repair only changes defect representation.
- RUN-003 exact fencing, transaction-scoped reconciliation, stale-result
  rejection, successor authority, and late-result audit: no fencing or relay
  code changed; relevant accepted regression coverage remains applicable.
- Objective/package isolation: no lifecycle identity or selection logic
  changed; defect reconstruction is local to the exact execution result.
- Idempotency and bounded execution: no dispatch or loop policy changed.
- Failure safety: serialization/validation raises before a successful fenced
  completion can be recorded; it cannot become PASS or acceptance.
- Downstream dispatch gating: repair dispatch occurs only after the durable
  validator result/defect lifecycle succeeds, and final success dispatch still
  requires revalidation and acceptance.

## 6. Shared database contamination

The known accumulated expired-row problem remains **PRE-EXISTING**. In the
shared test database, some lifecycle setup tests cannot claim newly queued
work and the broad one-go PostgreSQL tests can stop between roles. The same
failure mode was identified by RUN-004BV and is unrelated to defect JSON
serialization. It was not changed in this targeted repair. The successful
unique-objective PostgreSQL proof crossed the actual JSONB boundary and
completed the full repair loop.

## 7. Files and symbols changed

- `src/riverview/campaign/lifecycle.py`: `DefectInput.as_payload` and
  `DefectInput.from_payload`.
- `src/riverview/campaign/one_go.py`: execution normalization and structured
  defect reconstruction around the existing fenced persistence/lifecycle
  boundary.
- `tests/test_campaign_defect_serialization.py`: canonical round-trip and
  malformed/bound tests.
- `tests/test_campaign_one_go.py`: structured defect inputs in repair-loop
  unit scenarios.
- `tests/test_campaign_one_go_postgres.py`: JSONB reload, defect history, and
  completed repair-loop assertions.

No relay, fencing, Grace, dashboard, notifier, or unrelated work was changed.

## 8. Tests

- Focused defect serialization tests: PASS (2 tests).
- One-go unit tests: PASS (6 tests).
- Compileall and import/collection checks: PASS.
- `git diff --check`: PASS.
- Isolated PostgreSQL repair/revalidation proof: PASS.
- Relevant existing PostgreSQL/lifecycle suite: contains known shared-database
  claim/expired-row contamination; no new serialization failure was observed.

## 9. Readiness

The RUN-004BV blocking defect is repaired at the durable JSON/PostgreSQL
boundary and the full repair/revalidation path has been proven against an
isolated objective. This implementation is ready for independent
revalidation; C2 does not accept its own repair.
