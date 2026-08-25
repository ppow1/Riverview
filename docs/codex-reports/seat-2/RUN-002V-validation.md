# RUN-002V — Independent Validation of RUN-002 Campaign Runner Specification

Package: RUN-002V  
Role: C2 independent specification validator  
Primary input: `docs/codex-reports/seat-1/RUN-002-campaign-runner-specification.md`  
Architecture basis: `docs/codex-reports/seat-1/RUN-001R-revised-discovery.md`  
Prior validation: `docs/codex-reports/seat-2/RUN-001RV2-validation.md`

## Verdict

## FAIL — BLOCKING DEFECTS REMAIN

RUN-002 is substantially complete and implementable, but one contradictory
campaign-state requirement remains. It must be corrected before RUN-003, because
it leaves the authoritative current-phase/current-stage source of truth
ambiguous.

## Targeted validation findings

### A. Campaign/objective model — BLOCKING DEFECT

**Exact sections:** A.2, A.3, I.2, and P “Extend”.

Section A.2 states that the current phase is derived from ordered incomplete
stages and explicitly says: “No active-stage column is added.” Section A.3 and
I.2 continue to define the current phase as a derivation from ordered stages.

However, section P later requires extending `objectives` with:

`active_stage_id`

and describes this as a required physical database change.

This creates two incompatible sources of truth:

1. derived current phase/current stage from `objective_stages.sort_order`,
   `phase_key`, and incomplete state; and
2. stored `objectives.active_stage_id`.

**Requirement violated:** RUN-002 must avoid duplicate campaign state and must
not introduce contradictory objective/stage sources of truth.

**Why it matters:** RUN-003 cannot safely determine whether to calculate the
current phase from stage state or trust `active_stage_id`. A stale or incorrect
stored value could produce incorrect dashboard phase progress, dispatch the
wrong package, or cause phase/campaign completion logic to disagree with the
stage graph. Implementing both without a specified synchronization invariant
would create authoritative-state corruption risk.

**Minimum correction required:** choose exactly one model in RUN-002:

- remove `active_stage_id` from section P and state that current phase/current
  stage is always derived; or
- retain `active_stage_id` and define it as the sole authoritative projection,
  including the transaction that updates it and the invariant that it must
  match the ordered stage graph.

The preferred minimal correction is to remove `active_stage_id`, because the
specification already defines current phase as a deterministic projection.

### B. Attempt fencing — CONFIRMED

The exact tuple remains `work_order_id`, `attempt_id`, `lease_generation`,
`fencing_token`, and `worker_instance_id`. The specification covers claim,
heartbeat, progress, expiry, retry, terminal completion, and late-result
rejection. It explicitly prohibits stale results from reconciliation,
publication, acceptance, or downstream dispatch (sections B.1–B.8).

### C. Worker and seat identity — CONFIRMED

Seat identity is distinct from process-incarnation identity. A restart creates a
new `worker_instance_id`; roles are explicit; stale workers are timestamped;
and C1/C2/C3 concurrency is correctly treated as an accepted Steward fact.

### D. Writer/validator independence — CONFIRMED

The mandatory gate requires writer result → independent validator → PASS or
defects → repair → independent revalidation → acceptance. Writer completion
cannot transition directly to accepted. Validator assignment excludes the
writer worker instance and attempt. Repair writers cannot validate their own
repair.

The allowance for the original validator to revalidate only where policy
permits is not a blocking defect: the repair writer remains excluded and the
revalidation is a new fenced attempt.

### E. Immutable validation basis — CONFIRMED

The basis includes specification content/hash, acceptance criteria, evidence
requirements, base SHA, allowed paths, commands, expected outputs, revision,
and identity. It is created before the first writer claim, referenced by every
attempt, and superseded only through an explicit new revision.

### F. Defect and repair history — CONFIRMED

Structured defects include validation attempt, criterion, evidence, repair
requirement, state, and resolution attempt. Defects are append-only and cycle
linkage preserves writer, validator, repair, revalidation, and basis history.

### G. Arbitration — CONFIRMED

Arbitration is exceptional and triggered by disagreement, ambiguity, conflicting
evidence, or exhausted repair thresholds. Ordinary failures and repair cycles
do not invoke C3 arbitration.

### H. Heartbeat/progress/state — CONFIRMED

Heartbeat updates liveness and lease expiry only. Progress requires meaningful
idempotent detail and increments progress exactly once. State transitions are
separate authoritative events. The specification explicitly says heartbeat
does not increment progress and progress does not imply acceptance.

### I. Three-level progress — CONFIRMED

Overall roadmap and current phase progress are authoritative accepted-package
counts. Current step uses an approximate progress counter with `N / ~estimate`
and `+N and counting` display rules. It cannot authorize acceptance.

### J. Dashboard — CONFIRMED

The existing localhost `ThreadingHTTPServer` is reused. Required fields include
overall/phase/step progress, package, seat, role, heartbeat, meaningful
progress, state transition, activity, stale state, blocked reason, and lease
age. Status classification is timestamp/state based.

### K. Notifier — CONFIRMED

The existing Python speaking seam is reused. Heartbeats, routine progress, and
ordinary transitions are silent. Notification occurs after the database commit;
failure records diagnostics and leaves campaign state unchanged.

### L–N. Reports, recovery, and one-GO operation — CONFIRMED

The specification distinguishes local workflow reports from GitHub visibility
copies, preserves engineering success when GitHub publication fails, defines
restart/crash/validator/dashboard/notifier recovery, avoids Codex conversation
history, and explicitly excludes routine manual copy/paste from the one-GO
flow.

### O. Database discipline — PARTIALLY CONFIRMED

The physical changes are generally tied to runner requirements and avoid
duplicate campaign/package/dependency/defect/telemetry tables. The
`active_stage_id` contradiction identified above is the one blocking exception.

### P. State transition matrix — CONFIRMED SUBJECT TO A CORRECTION

The matrix explicitly covers validation, repair, revalidation, accepted,
blocked, failed, timed-out, and late-result states. Acceptance requires a
fenced validator/revalidator/arbitrator result and evidence. It becomes
implementable once the current-stage source-of-truth contradiction is removed.

### Q. Acceptance test matrix — CONFIRMED

The matrix covers normal PASS, repair/revalidation, self-validation rejection,
stale results, new fences on retry, heartbeat/progress distinction,
authoritative roadmap/phase progress, estimate overflow, crash recovery,
notifier behavior, Grace absence, local/GitHub report semantics, arbitration
absence during normal repair, one-GO progression, basis changes, actual-tree
validation, and dashboard restart.

## Required non-blocking clarification

Section B.7 says every retry receives a new `worker_instance_id`, while section
C.2 defines `worker_instance_id` as the process-incarnation identity that
changes on process startup. If the same process claims a retry, those statements
conflict. RUN-003 should clarify that a retry always receives a new attempt,
generation, and fencing token, while `worker_instance_id` changes only when a
new process incarnation performs the retry. This does not invalidate the
fencing design because the attempt, generation, and token are already new.

## Scope assessment

The specification remains appropriately bounded. It does not make Grace
cognition, GPU scheduling, provider routing, generalized artifact management,
full repository hardening, publication redesign, or a new security framework
prerequisites for this campaign.

## Implementation readiness

REPAIR_REQUIRED

RUN-003 should not begin until the `active_stage_id` contradiction is removed
or resolved with one explicit authoritative-source invariant. After that
correction, the remaining findings are suitable for implementation-level
clarification rather than architecture rejection.
