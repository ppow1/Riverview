# RUN-004AV — Writer/Validator Lifecycle and Acceptance-Gate Validation

Package: RUN-004AV  
Role: C2 independent implementation validator  
Date: 2026-08-25  
Implementation commit: `6985f73af677eb331a7dab6188b0b7eab792e6db`

## Verdict

**FAIL — BLOCKING DEFECTS REMAIN**

The durable lifecycle, fencing integration, validator independence exclusion,
defect/repair history, and restart-oriented persistence are substantially
implemented. However, the acceptance gate does not require actual resulting
tree/commit evidence. An independent validator can submit PASS with an
arbitrary nonempty `result_version_hash`, empty `evidence_refs`, and no
`implementation_ref`; the stage and objective are then accepted. This is a
reachable false-acceptance path against an explicit RUN-002 invariant.

## Verification scope

The implementation commit changes the reported six files:

- `database/migrations/0040_campaign_validation_lifecycle.sql`
- `src/riverview/campaign/__init__.py`
- `src/riverview/campaign/lifecycle.py`
- `src/riverview/relay/store.py`
- `tests/test_campaign_validation_lifecycle.py`
- the C1 implementation report

The worktree was at the reported commit in detached HEAD state. No
implementation files were modified during validation.

## 1. Schema and migration — PASS

Migration 0040 is present and its objects are applied in the configured
PostgreSQL database. The database contains `campaign_validation_bases`,
`campaign_validation_results`, and `campaign_validation_defects`, along with
stage runner state/progress, basis and attempt links, work-order source links,
and execution validation fields.

The migration provides primary keys, foreign keys, unique validation attempt
and idempotency constraints, closed verdict/severity/state checks, immutable
basis rows by revision convention, and nonnegative progress constraints. No
`objectives.active_stage_id` authority was introduced.

Schema/migration: **PASS**

## 2. Writer lifecycle and independent validator — PASS

`CampaignLifecycleStore.handoff_writer_to_validation` requires a technically
completed writer attempt with result evidence and matching basis, then creates
a validator work order linked to the source work order and attempt before
moving the stage to `validation_pending`.

`RelayStore.claim_fenced` adds a durable `NOT EXISTS` exclusion for validator
and revalidator claims whose worker instance matches the source attempt.
`record_validation` independently rechecks the completed attempt and compares
the validator worker instance with the writer instance. The same worker
instance cannot claim the validator or revalidator role for its source work.

The focused self-validation and repair-writer self-revalidation probes passed.
Seat eligibility and role are persisted separately from worker instance, as
required by the accepted design.

Writer lifecycle: **PASS**  
Independent validator enforcement: **PASS**

## 3. Defect, repair, revalidation, and history — PASS for exercised paths

FAIL requires structured defects and creates a repair work order linked to the
validation result/source attempt. Repair completion links unresolved defects
to the repair attempt and creates revalidation work. Revalidation PASS resolves
the linked defects while retaining the original writer, validator, result, and
defect rows.

The focused repair-cycle test reconstructed the expected history and accepted
only after revalidation. Wrong basis, stale validation, missing defects, and
invalid lifecycle transitions were rejected in the focused suite.

Defect/repair/revalidation linkage: **PASS**  
History preservation: **PASS**  
Idempotency: **PASS** for covered work-order/result operations

## 4. Blocking acceptance-gate defect

The accepted RUN-002 gate requires a validator/revalidator PASS tied to the
immutable basis, actual resulting tree/commit, and durable evidence. The
implementation does not enforce the latter two requirements.

In `src/riverview/campaign/lifecycle.py:267-312`, `record_validation` only
requires that `result_version_hash` be nonempty. `evidence_refs` may be empty
and `implementation_ref` is optional. In `_accept_locked` at approximately
line 359, acceptance checks PASS, basis ID, writer attempt ID, and unresolved
blocking defects, but never requires nonempty evidence, an implementation/tree
reference, or correspondence between the claimed result version and the
writer/repair result.

Independent reproduction:

1. Create and technically complete a writer.
2. Create and technically complete an independent validator.
3. Call `record_validation` with:
   - `verdict='PASS'`;
   - the correct basis hash;
   - `result_version_hash='arbitrary-unverified-value'`;
   - `evidence_refs=()`; and
   - `implementation_ref=None`.
4. Observe the result.

Observed output:

`ARBITRARY_PASS_ACCEPTED ... ('accepted', 'completed')`

The stage and objective therefore became accepted without actual tree/commit
or evidence binding. This is not merely a missing future feature: it permits
false acceptance through the authoritative lifecycle API.

Severity: **BLOCKING**  
Requirement violated: RUN-002 D.3 and state-transition matrix acceptance
requires exact basis, tree/commit, and evidence; arbitrary writer/validator
prose or ungrounded PASS must not accept work.  
Minimum correction: make the acceptance-producing path require and validate a
nonempty implementation/tree reference and durable evidence references, and
bind the result-version/tree evidence to the exact completed writer or repair
result and immutable basis before `_accept_locked` can advance state. Add an
adversarial test proving arbitrary PASS evidence cannot accept.

Acceptance gate: **FAIL**

## 5. RUN-003 fencing integration — PASS

RUN-004A uses the accepted exact fenced attempt identity for lifecycle
mutations and delegates progress to fenced relay persistence. The implementation
does not alter the accepted transaction-scoped `FencedReconciliation` boundary.
The focused valid reconciliation, stale-result, successor-protection, expiry,
and recovery tests remained valid when run in an isolated database state.

RUN-003 fencing integration: **PASS**  
FencedReconciliation regression: **PASS**

## 6. Restart/resume and progress — PASS for exercised persistence

Stage runner state, basis, attempts, validation results, defects, source links,
and River lifecycle events are PostgreSQL-backed. The focused lifecycle tests
recreated store objects and verified durable stage/basis/history projections.
Progress uses the exact RUN-003 fence and idempotency key; heartbeat remains
distinct from progress and acceptance.

Restart/resume: **PASS**  
Progress/heartbeat persistence: **PASS**

## 7. PostgreSQL concurrency — PASS for claim winner; contamination noted

The real PostgreSQL concurrent writer-claim test produced one authoritative
winner. Validator claims are also exclusive through the existing row-lock and
active-attempt predicates. The acceptance defect above is a gate-content
failure, not a competing-transaction race.

PostgreSQL concurrency: **PASS** for exercised claim races

## 8. Shared-database stale-lease failure — BENIGN TEST CONTAMINATION

The broader run reproduced two environment limitations:

1. The full suite cannot collect three MCP tests because the optional `mcp`
   Python package is unavailable in this environment.
2. With accumulated expired active rows in the shared PostgreSQL database,
   `test_reconciliation_authority_blocks_expiry_during_real_postgres_side_effect`
   fails because it asserts the global sweeper result is empty rather than
   filtering to its own work order. Repeated lifecycle tests also intermittently
   fail to claim newly created fixtures while residue remains.

Running `RelayStore.expire_leases()` to clear expired residue and then running
the reconciliation test or an individual lifecycle test passes. The stale
rows are historical test residue; no test showed them changing the
authoritative state of a particular production work order, successor fence, or
acceptance decision. This is a test-isolation defect and should be cleaned up
before relying on shared-database full-regression results, but it is not the
RUN-004A engineering verdict.

Shared-database stale-lease failure: **BENIGN TEST CONTAMINATION**

## 9. Independent test results

Compile/import validation: **PASS**.

Representative isolated lifecycle paths covering writer handoff, PASS,
structured FAIL/repair/revalidation, concurrency, and invalid transitions:
**PASS**.

The focused combined run reported **50 tests collected with 7 failures**:
the reconciliation assertion and lifecycle claim failures were the shared
expired-row contamination described above. After cleanup, the representative
acceptance/lifecycle tests passed. The full suite was blocked at collection by
three missing MCP dependencies; it did not provide a clean full-regression
signal.

The independent arbitrary-PASS probe is the decisive failure evidence and is
not covered by the submitted lifecycle tests.

## 10. Acceptance matrix summary

| Area | Result |
|---|---|
| schema/migration | PASS |
| writer lifecycle | PASS |
| writer self-validation rejection | PASS |
| validator PASS persistence | PASS |
| validator FAIL/defects | PASS |
| repair/revalidation linkage | PASS |
| acceptance before validation | PASS rejected |
| acceptance after arbitrary PASS without evidence | **FAIL — BLOCKING** |
| stale validator/fence rejection | PASS |
| restart/history persistence | PASS |
| claim concurrency | PASS |
| actual tree/evidence acceptance binding | **FAIL — BLOCKING** |

## 11. RUN-004B readiness

RUN-004B must not begin. The lifecycle persistence foundation has useful
passing behavior, but its authoritative acceptance gate can currently convert
an ungrounded validator PASS into accepted campaign state.

RUN-004B readiness: **REPAIR_REQUIRED**

