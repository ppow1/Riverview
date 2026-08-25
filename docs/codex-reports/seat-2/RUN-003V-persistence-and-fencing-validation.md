# RUN-003V — Persistence and Attempt Fencing Validation

Package: RUN-003V  
Role: C2 independent implementation validator  
Implementation commit: `e67b951ba032c6cc756368e63439a1d4d2a8a2d7`  
Specification: `docs/codex-reports/seat-1/RUN-002-campaign-runner-specification.md`  
Implementation report: `docs/codex-reports/seat-1/RUN-003-persistence-and-fencing-implementation.md`

## Verdict

## FAIL — BLOCKING DEFECTS REMAIN

The persistence and fencing primitives themselves are substantially correct,
but the implemented Codex execution path violates the required stale-result
boundary. A worker can lose its lease and then invoke repository reconciliation
and record an accepted reconciliation before `complete_fenced` rejects its
stale terminal result.

This can allow stale work to reach an authoritative reconciliation/acceptance
boundary and therefore blocks RUN-003 acceptance.

## Blocking defect

### Stale Codex result reaches reconciliation before fencing

**Severity:** BLOCKING DEFECT  
**Files/symbols:** `src/riverview/runner.py`, `RestrictedRunner._execute_codex`  
**Relevant lines:** approximately 106–142 and 158–161 in the implementation
commit.

The Codex path performs this sequence:

1. `ResultReconciler().persist(result)`;
2. `ResultReconciler().reconcile_repository(...)`;
3. `ResultReconciler().record_decision(..., "accepted", ...)`;
4. only afterwards, `self.store.complete_fenced(self._identity(work), report)`.

`complete_fenced` correctly rejects a stale or mismatched tuple, but that check
occurs after reconciliation and the accepted reconciliation decision. Thus the
following race remains:

1. worker A claims an attempt;
2. A's lease expires and is replaced by a successor;
3. A's Codex process returns success;
4. A reconciles the repository and records an accepted reconciliation;
5. A finally calls `complete_fenced` and is rejected as stale.

**Requirement violated:** RUN-002 requires that a stale result must not trigger
reconciliation, publication, acceptance, or downstream dispatch. RUN-003's
implementation report claims the stale result cannot invoke repository
reconciliation/publication, but the actual call order does not enforce that
claim.

**Why it matters:** The stale terminal result is correctly prevented from
updating `work_orders`, but authoritative repository/reconciliation state has
already been touched. This is precisely the false-acceptance and stale-result
propagation race the fencing design is required to prevent.

**Minimum correction required:** add an ownership/fence validation immediately
before any callable authoritative reconciliation/publication/acceptance seam,
and make the reconciliation/terminal publication transactionally conditional
on the exact current tuple. A stale result must be rejected and recorded as
late evidence before `reconcile_repository` or `record_decision("accepted")`
can run. The correction must also preserve the successor's active authority.

## Migration 0039 validation — PASS

`database/migrations/0039_campaign_attempt_fencing.sql` follows the existing
transactional migration convention and was applied to the configured
PostgreSQL database. Direct database inspection showed migration `0039` in
`schema_migrations`; the required work-order fence columns are present; and
`objectives.active_stage_id` is absent.

The migration provides the active attempt identity across work orders,
attempts, relay workers, execution envelopes, and execution results. It adds
the all-or-none active tuple check, unique attempt identity, non-negative
progress checks, and relevant indexes. No objective-level current-phase
authority was introduced.

## Claim fencing — PASS

`RelayStore.claim_fenced` uses `FOR UPDATE SKIP LOCKED`, creates a new UUID
attempt and token, increments generation, captures worker instance/seat/role,
inserts the attempt, updates the work order, appends a claim event, and commits
before returning executable work.

An independent two-thread PostgreSQL probe against one queued work order
returned exactly one successful claim and one `None` result. The winning claim
was completed afterward.

## Heartbeat — PASS

`heartbeat_fenced` requires all five identity components and updates only
heartbeat/lease timestamps. Wrong attempt, generation, token, or worker
instance is rejected. Focused tests confirmed heartbeat does not increment
progress.

## Meaningful progress — PASS

`progress_fenced` requires a non-empty idempotency key and message, locks the
active work order, appends one idempotent River progress event, and increments
attempt/work-order progress only on first insertion. Duplicate progress keys
do not increment counters. Wrong or stale identities are rejected.

## Lease expiry and retry — PASS

`expire_leases` locks expired active work, rechecks the exact tuple, marks the
attempt timed out, clears active work-order authority, and appends a timeout
event. `requeue_timed_out` makes the order eligible again; the next claim gets
a new attempt ID, generation, and token while preserving the old attempt row.

## Terminal completion — PASS at the persistence boundary

`complete_fenced` locks the work order and checks the exact active tuple and
active lifecycle state. Correct completion succeeds; wrong attempt, generation,
token, worker instance, expired, and superseded completions are rejected. The
stale attempt is marked as late evidence and the successor active tuple is not
cleared or replaced.

The blocking failure is the caller ordering described above: the Codex path
does not wait for this fencing boundary before reconciliation.

## Worker identity — PASS

`RelayWorker` and `RestrictedRunner` generate UUID process-incarnation
identities. The identity is carried into claims and persisted. A restarted
process receives a new identity even with the same logical worker and seat.

## Compatibility wrappers — PASS

Legacy `claim`, `heartbeat`, `progress`, and `complete` resolve the currently
active exact identity and delegate to fenced operations. They do not accept a
caller-supplied stale identity through the legacy API or bypass the exact tuple
checks.

## River/audit events — PASS

Claim, progress, timeout, state-transition, and late-result rejection events
are produced with idempotency handling appropriate to the implemented scope.

## Current-phase authority — PASS

No `objectives.active_stage_id` column or alternate current-phase authority was
introduced.

## Independent test execution

Executed locally:

- `tests/test_campaign_fencing.py`: 6 passed;
- directly relevant Relay, runner-policy, objective-stage, status, and River
  tests: 23 passed in total;
- independent two-thread PostgreSQL claim probe: one winner, one excluded
  claimant;
- Ruff on changed runtime/test files: passed;
- migration/schema inspection against configured PostgreSQL: passed.

The focused tests validate the persistence fencing primitives, but they do not
exercise lease expiry during `_execute_codex` between repository reconciliation
and `complete_fenced`. That missing integration race is why the implementation
cannot be accepted despite the passing primitive tests.

## Acceptance matrix

| # | Boundary | Result |
|---:|---|---|
| 1 | valid claim | PASS |
| 2 | complete fencing tuple created | PASS |
| 3 | competing claim excluded | PASS |
| 4 | valid heartbeat | PASS |
| 5 | heartbeat does not increment progress | PASS |
| 6 | stale heartbeat rejected | PASS |
| 7 | valid progress | PASS |
| 8 | duplicate progress idempotent | PASS |
| 9 | stale progress rejected | PASS |
| 10 | expired lease loses authority | PASS |
| 11 | retry obtains new authority | PASS |
| 12 | exact current completion succeeds | PASS |
| 13 | stale completion rejected | PASS at store boundary |
| 14 | wrong token rejected | PASS |
| 15 | wrong generation rejected | PASS |
| 16 | wrong worker instance rejected | PASS |
| 17 | stale result cannot advance work-order state | PASS |
| 18 | stale result cannot reach reconciliation/publication | **FAIL** |
| 19 | restarted worker does not inherit old authority | PASS |
| 20 | no duplicate current-phase authority | PASS |

## Scope validation

RUN-003 remains bounded. It does not attempt validator assignment, repair
orchestration, arbitration, dashboard, notifier, Grace integration, or
resource scheduling. Those omissions are not defects for this package.

## Live PostgreSQL validation

PASS. Migration 0039 is applied; schema inspection passed; focused live
PostgreSQL fencing tests passed; and an independent concurrent claim probe
excluded the competing claimant.

## Fencing verdict

Persistence-layer fencing is correct for claim, heartbeat, progress, expiry,
retry, and terminal authority. End-to-end implementation fencing is not yet
correct because `_execute_codex` crosses the reconciliation/acceptance boundary
before invoking `complete_fenced`.

## Stale-result verdict

FAIL. `complete_fenced` rejects stale results and preserves audit evidence, but
the Codex caller can reconcile and record acceptance before that rejection.

## Implementation readiness

REPAIR_REQUIRED
