# RUN-002 — Codex Campaign Runner Canonical Specification

Status: Design specification only
Role: C1 primary specification author
Basis: RUN-001R revised discovery and RUN-001RV2 validation
Validation basis: RUN-001RV2 verdict PASS

## 1. Purpose and non-goals

This specification defines the minimum PostgreSQL-backed Codex Campaign Runner
that can be implemented in RUN-003 and subsequently validated.

PostgreSQL is authoritative campaign and runtime state. The runner operates
without Grace. Existing Riverview Relay, execution-envelope, reconciliation,
River-event, diagnostics, notification, and localhost status infrastructure is
extended rather than replaced.

C1, C2, and C3 are accepted as independently concurrent authenticated Codex
seats. Seat concurrency is not a blocker.

This specification does not include Grace cognition, GPU scheduling, provider
routing redesign, a new security framework, broad repository hardening,
advanced merge/publication management, an artifact platform, or notification
redesign.

## 2. Existing foundation and terminology

The implementation shall reuse:

- objectives, objective_stages, and objective_stage_dependencies;
- approved_actions, work_orders, work_order_attempts, and relay_workers;
- execution_envelopes, execution_results, reconciliation_records;
- execution_lanes and lane_path_owners;
- river_events, diagnostic_events, steward_escalations, and steward_notifications;
- RestrictedRunner and the existing Codex CLI adapter;
- the existing localhost-only ThreadingHTTPServer status surface;
- existing CODEX_HOME mappings for C1, C2, and C3.

Authoritative source evidence:

- database/migrations/0010_objective_stage_model.sql
- database/migrations/0014_autonomous_control_plane.sql
- database/migrations/0017_lanes_reconciliation.sql
- src/riverview/relay/store.py
- src/riverview/relay/worker.py
- src/riverview/runner.py
- src/riverview/status/server.py
- src/riverview/status/snapshot.py
- ../theestate/src/estate/core/codex_bridge.py
- docs/codex-reports/seat-1/RUN-001R-revised-discovery.md
- docs/codex-reports/seat-2/RUN-001RV2-validation.md

A campaign means one PostgreSQL objective. A phase means a grouped ordered
set of objective stages. A work package means one objective stage and its
associated execution chain. An attempt means one fenced execution of one work
package role.

## A. Campaign model

### A.1 Decision: no new campaign aggregate table

The existing objectives table is sufficient as the campaign aggregate. A new
campaign_runs table would duplicate objective identity, status, timestamps,
correlation, and final output.

Use:

- objectives.objective_id as campaign ID;
- objectives.objective_key as campaign key;
- objectives.title as campaign name;
- objectives.description as campaign objective;
- objectives.status as campaign lifecycle;
- objectives.created_at, updated_at, completed_at as campaign timestamps;
- objectives.correlation_id as campaign correlation;
- objectives.final_output as accepted campaign output.

The existing objective stage model is the campaign package/dependency model.
No second dependency graph or package-state table is permitted.

### A.2 Minimal objective extensions

Extend objectives only where a campaign-level requirement cannot be derived:

- attention_required boolean not null default false;
- acceptance_state text not null default pending, constrained to pending,
  awaiting_validation, accepted, rejected.

The current active phase is derived from the ordered incomplete stages. No
active-stage column is added: the authoritative phase/package ordering remains
objective_stages.sort_order and the current phase is a projection of that
state.

### A.3 Minimal stage extensions

Extend objective_stages with:

- phase_key text not null;
- phase_title text not null;
- eligible_seats jsonb not null default ["C1","C2","C3"];
- estimated_progress_units integer not null default 15, greater than zero;
- blocked_reason text nullable;
- last_progress_at timestamptz nullable;
- progress_count integer not null default 0, non-negative.

A stage remains one work package. phase_key groups ordered packages into the
current phase without creating another phase-state model. Current phase is
derived from the first phase_key containing an active or incomplete package.
Execution role is assigned to each work order/attempt, not to the stage, so
the same package can have writer, validator, repair_writer, revalidator, and
arbitrator work orders without duplicating the package model.

The existing objective_stage_dependencies table remains the only dependency
relation. Dependencies must not be duplicated in JSON or in a new campaign
table.

### A.4 Campaign state and progress

Campaign status is authoritative in objectives.status.

Campaign acceptance requires:

- every required package accepted;
- no unresolved defect set;
- required validation and revalidation evidence present;
- accepted execution/reconciliation records present;
- objectives.acceptance_state = accepted;
- objectives.status = completed.

A writer result, completion receipt, commit, or report alone cannot satisfy
campaign acceptance.

## B. Work and attempt fencing

### B.1 Exact active-attempt identity

Every active attempt is identified by this complete tuple:

- work_order_id;
- attempt_id;
- lease_generation;
- fencing_token;
- worker_instance_id.

The tuple is copied into the work order's active lease fields, the attempt row,
the execution envelope, and the result/reconciliation record.

fencing_token is a newly generated unpredictable UUID per attempt. It is never
reused. lease_generation is monotonically increased per work order. A new
attempt always receives a new attempt_id, generation, and token.

worker_instance_id identifies one process incarnation. It changes on every
worker process start, including restart on the same host and seat.

### B.2 Required persistence extensions

Extend work_orders with:

- active_attempt_id uuid nullable;
- lease_generation bigint nullable;
- fencing_token uuid nullable;
- worker_instance_id uuid nullable;
- seat_id text nullable;
- role text nullable;
- last_progress_at timestamptz nullable;
- progress_count integer not null default 0;
- blocked_reason text nullable.

Extend work_order_attempts with:

- attempt_id uuid unique;
- lease_generation bigint;
- fencing_token uuid;
- worker_instance_id uuid;
- seat_id text;
- role text;
- last_heartbeat_at timestamptz;
- last_progress_at timestamptz;
- progress_count integer not null default 0;
- terminal_state text nullable;
- late_or_stale boolean not null default false;
- late_result_ref text nullable.

The existing generated attempt identity may be retained as an implementation
identifier only if it is promoted to the explicit attempt_id required here.

Extend execution_envelopes with attempt_id, lease_generation, fencing_token,
worker_instance_id, role, and validation_basis_hash.

Extend execution_results with attempt_id, lease_generation, fencing_token,
worker_instance_id, late_or_stale, and authoritative_result boolean.

A late result is stored in execution_results or the corresponding attempt/result
record with authoritative_result=false. No separate result table is required.

### B.3 Claim transaction

Claiming is one transaction:

1. Lock one eligible queued work order with FOR UPDATE SKIP LOCKED.
2. Confirm dependencies and role/seat eligibility.
3. Confirm no active attempt exists.
4. Increment lease_generation.
5. Generate attempt_id, fencing_token, and receive the caller's
   worker_instance_id.
6. Insert work_order_attempts.
7. Update work_orders to claimed and copy the exact fencing tuple.
8. Create the attempt's execution envelope and immutable validation-basis
   reference.
9. Append one idempotent claimed/state-transition event.
10. Commit.

No process may execute before the transaction commits.

Conceptual SQL:

    BEGIN;
    SELECT work_order_id, status
      FROM work_orders
     WHERE work_order_id = :id
       AND status = 'queued'
       AND active_attempt_id IS NULL
     FOR UPDATE;

    -- validate dependencies, role, seat, and retry policy

    UPDATE work_orders
       SET status = 'claimed',
           active_attempt_id = :attempt_id,
           lease_generation = lease_generation + 1,
           fencing_token = :token,
           worker_instance_id = :worker_instance_id,
           seat_id = :seat_id,
           role = :role,
           lease_owner = :worker_instance_id,
           lease_expires_at = now() + :lease_interval,
           last_heartbeat_at = now(),
           updated_at = now()
     WHERE work_order_id = :work_order_id
       AND status = 'queued'
       AND active_attempt_id IS NULL;

    INSERT INTO work_order_attempts (... exact tuple ...)
    VALUES (...);

    COMMIT;

The implementation must verify that exactly one work-order row was updated.

### B.4 Heartbeat

A heartbeat updates only liveness fields and lease expiry:

    UPDATE work_orders
       SET last_heartbeat_at = now(),
           lease_expires_at = now() + :lease_interval,
           updated_at = now()
     WHERE work_order_id = :work_order_id
       AND status IN ('claimed','running',...)
       AND active_attempt_id = :attempt_id
       AND lease_generation = :generation
       AND fencing_token = :token
       AND worker_instance_id = :worker_instance_id;

    UPDATE work_order_attempts
       SET last_heartbeat_at = now()
     WHERE attempt_id = :attempt_id
       AND work_order_id = :work_order_id
       AND lease_generation = :generation
       AND fencing_token = :token
       AND worker_instance_id = :worker_instance_id;

If either ownership check fails, the worker is fenced and must stop publishing
results. A heartbeat never increments progress_count and never changes the
authoritative lifecycle state.

Target heartbeat interval while active: approximately two minutes. The lease
interval must be materially longer than the heartbeat interval.

### B.5 Progress

A progress update must include an idempotency key and meaningful detail. It
updates last_progress_at and increments progress_count exactly once:

    UPDATE work_order_attempts
       SET last_progress_at = now(),
           progress_count = progress_count + 1
     WHERE attempt_id = :attempt_id
       AND exact active tuple matches;

    UPDATE work_orders
       SET last_progress_at = now(),
           progress_count = progress_count + 1,
           updated_at = now()
     WHERE work_order_id = :work_order_id
       AND exact active tuple matches;

    INSERT INTO river_events (... runner.progress ...)
    ON CONFLICT (idempotency_key) DO NOTHING;

Progress is not acceptance and does not imply a lifecycle transition.

### B.6 Lease expiry

A reconciliation/sweeper transaction identifies active attempts whose
lease_expires_at < now().

It must:

- lock the work order;
- re-check the exact current lease;
- mark the attempt timed_out or stale-released;
- clear the active lease fields;
- record a diagnostic and timeout/state event;
- create a retryable or blocked outcome according to retry policy;
- never accept the attempt;
- never reconcile or publish a late result.

An expired attempt is not automatically retried if the action is not retry-safe,
the retry threshold is exceeded, or repository side effects are ambiguous.

### B.7 New attempt and retry

A retry creates a new attempt row and a new execution envelope. It does not
overwrite the prior attempt.

The new attempt receives:

- a new attempt_id;
- lease_generation + 1;
- a new fencing_token;
- a new worker_instance_id;
- a new attempt start time.

The prior attempt remains immutable history.

### B.8 Terminal completion

Terminal completion is a transaction that first locks the work order and
verifies the full active tuple:

    BEGIN;
    SELECT status, active_attempt_id, lease_generation, fencing_token,
           worker_instance_id
      FROM work_orders
     WHERE work_order_id = :work_order_id
     FOR UPDATE;

    IF any selected value differs from the submitted exact tuple:
        INSERT late/stale result with authoritative_result=false;
        INSERT runner.late_result event;
        COMMIT;
        return fenced/rejected;

    -- persist result and evidence
    -- reconcile repository only after ownership check succeeds
    -- transition authoritative state only if result category is valid

    UPDATE work_orders
       SET status = :next_state,
           active_attempt_id = NULL,
           lease_owner = NULL,
           lease_expires_at = NULL,
           finished_at = now(),
           updated_at = now()
     WHERE work_order_id = :work_order_id
       AND active_attempt_id = :attempt_id
       AND lease_generation = :generation
       AND fencing_token = :token
       AND worker_instance_id = :worker_instance_id;

    UPDATE work_order_attempts
       SET finished_at = now(),
           terminal_state = :terminal_state
     WHERE attempt_id = :attempt_id
       AND exact tuple matches;

    INSERT state-transition event;
    COMMIT;

The implementation must verify row counts for every ownership-sensitive update.

A stale result must not trigger repository reconciliation, acceptance, report
publication, or downstream dispatch.

## C. Worker and seat model

### C.1 Seats

The only logical seats are C1, C2, and C3.

Reuse the existing mapping:

- C1: A:\AI\CodexProfiles\C1
- C2: A:\AI\CodexProfiles\C2
- C3: A:\AI\CodexProfiles\C3

Authenticated seat handling is outside this specification.

### C.2 Worker identity

worker_instance_id is a UUID generated at process startup. It is distinct from:

- seat_id;
- worker_id/logical worker registration;
- package role;
- process ID;
- Codex conversation/session identity.

A restart always creates a new worker_instance_id.

Extend relay_workers with seat_id, worker_instance_id, supported_roles,
started_at, last_heartbeat_at, current_work_order_id, and stale state. The
existing relay_workers table remains the worker registry.

### C.3 Roles

Supported roles:

- writer;
- validator;
- repair_writer;
- revalidator;
- arbitrator.

Role is persisted on the work order, attempt, execution envelope, and result.
A worker may be capable of multiple roles, but each attempt has exactly one
role.

### C.4 Startup and shutdown

Startup:

1. Generate worker_instance_id.
2. Register/update relay_workers with worker ID, seat, process ID, host,
   supported roles, and state=starting.
3. Verify PostgreSQL connectivity.
4. Transition to idle.
5. Begin claim loop and heartbeat loop.

Shutdown:

1. Stop claiming new work.
2. Continue heartbeat while safely winding down an active child, if possible.
3. Persist stopped state.
4. Do not mark unfinished work complete.
5. Let lease/reconciliation recover unfinished attempts.

Stale worker detection is timestamp-based. A worker with heartbeat older than
the stale threshold is stale regardless of model-generated claims.

## D. Writer/validator enforcement

### D.1 Mandatory gate

No transition from a writer result to accepted is permitted.

A writer terminal result transitions the package to validation_pending and
creates a validator work order. The validator must be assigned a different
worker_instance_id from the writer attempt. The validator's seat may be C1,
C2, or C3 subject to eligibility, but identity independence is mandatory.

The validator must not be the same attempt, worker instance, or logical process
incarnation as the writer.

### D.2 Validation input

The validator receives:

- immutable specification snapshot and hash;
- acceptance criteria;
- evidence requirements;
- original base SHA;
- allowed paths;
- expected outputs;
- validation commands;
- writer result and changed-path inventory;
- actual resulting tree/commit;
- durable evidence references.

The validator does not receive authority to rewrite acceptance criteria or the
original specification.

### D.3 PASS

A validator PASS creates a durable validation result referencing the exact
basis hash, tree/commit, validator attempt, and evidence.

For a first-pass success, the package may transition to accepted only after the
fenced validation result is persisted and all acceptance invariants hold.

For a repaired package, only revalidation PASS may transition it to accepted.

### D.4 FAIL and defects

A validator FAIL persists structured defects and transitions the package to
defects_found. It must not directly alter the writer result.

The runner creates repair_pending and then assigns a repair_writer attempt.
After repair completion, the runner creates revalidation_pending and assigns a
new independent revalidator attempt.

The validator who produced defects may revalidate only if implementation policy
permits the same validator identity and the revalidation remains a new attempt;
the writer who made the repair may never revalidate its own repair.

To preserve maximal independence, the default policy assigns a different
worker_instance_id for revalidation.

## E. Immutable validation basis

### E.1 Basis contents

Each package receives one immutable validation basis containing:

- package/work ID;
- specification content or durable local reference;
- specification hash;
- acceptance criteria;
- evidence requirements;
- original base SHA;
- allowed paths;
- validation commands;
- expected outputs;
- basis revision;
- created timestamp;
- creator/requester identity.

The basis is referenced by hash from every writer, validator, repair, and
revalidation attempt.

### E.2 Snapshot timing

The basis is created transactionally when the campaign/package is admitted
before the first writer claim. The content is canonicalized and hashed before
being stored or referenced.

The implementation may use the existing execution_envelope JSON fields for
the durable snapshot. No external mutable document may be the only source.

### E.3 Requirement changes

A basis is immutable. It cannot be edited in place.

A legitimate requirement change creates a new package/basis revision with:

- a new basis hash;
- a new revision identifier;
- a new admission event;
- explicit supersession linkage;
- a new base SHA if the implementation branch changed.

In-flight attempts tied to the prior basis are completed as historical results or
blocked for re-admission. They are not silently reinterpreted under the new
requirements.

## F. Validation defects and repair cycles

### F.1 Defect record

Structured defects are stored in the existing execution result evidence JSON
unless a later implementation proves a separate normalized table necessary.
RUN-003 shall not add a defect table by default.

Each defect object contains:

- defect_id;
- validation_attempt_id;
- acceptance_criterion_ref;
- severity;
- expected_behavior;
- observed_behavior;
- evidence_ref;
- required_repair;
- state: unresolved, resolved, superseded;
- created_at;
- resolved_at;
- resolution_attempt_id.

Defects are append-only. A repair creates a new resolution record; it does
not overwrite the original finding.

### F.2 Cycle linkage

Every result references:

- campaign/objective;
- package/stage;
- writer attempt;
- validator attempt;
- defect set, if any;
- repair attempt, if any;
- revalidation attempt, if any;
- validation basis hash.

The complete chain is queryable from PostgreSQL and River events.

### F.3 Repair threshold

A configured package repair threshold may block the package and require
arbitration or Steward attention. Normal writer failure, validator failure,
and ordinary repair cycles do not invoke arbitration.

## G. Arbitration

### G.1 Exceptional triggers

Arbitration may be requested only for:

- repeated writer/validator disagreement;
- ambiguous or internally inconsistent original specification;
- conflicting validation evidence;
- repair loop exceeding the configured threshold;
- unresolved disagreement after independent revalidation.

Arbitration is not required for ordinary failure, timeout, or one repair cycle.

### G.2 Arbitrator

The default arbitrator seat is C3, with role=arbitrator. C3 assignment is
subject to the same attempt fencing and worker identity rules. The arbitrator
must not be the writer attempt and should not be the validator attempt that
created the disagreement.

### G.3 Arbitration input

The arbitrator receives:

- immutable validation basis;
- writer and repair results;
- validator and revalidator findings;
- actual tree/commit evidence;
- all defect history;
- disagreement reason;
- relevant River event history.

### G.4 Arbitration output

The arbitrator produces one structured decision:

- accept;
- require repair;
- reject/block;
- specification revision required.

The decision includes rationale, evidence references, arbitrator identity,
attempt identity, and basis hash.

Only a fenced arbitrator decision may transition a package to accepted. A
specification revision decision creates a new basis revision and does not mutate
the current one.

## H. Telemetry

### H.1 Persistence semantics

Heartbeat is persisted in worker, work-order, and attempt timestamps. Routine
heartbeats do not need one River event per interval.

Meaningful progress and authoritative state transitions append River events.
Late/stale result rejection appends a River event and diagnostic.

### H.2 Minimum event envelope

Progress, state-transition, validation, defect, recovery, and late-result
events contain:

- event_id;
- event_kind;
- timestamp;
- campaign/objective ID;
- package/stage ID;
- work_order_id;
- attempt_id when applicable;
- seat_id;
- role;
- worker_instance_id;
- message;
- structured detail;
- correlation_id;
- causation_id;
- idempotency_key.

Required event kinds include:

- runner.attempt.claimed;
- runner.attempt.heartbeat_observed when explicitly emitted;
- runner.progress;
- runner.state_transition;
- runner.validation.pass;
- runner.validation.defects;
- runner.repair.started;
- runner.revalidation.pass;
- runner.revalidation.defects;
- runner.arbitration.requested;
- runner.arbitration.decided;
- runner.attempt.timed_out;
- runner.result.late_rejected;
- runner.report.local_complete;
- runner.report.github_publication_succeeded;
- runner.report.github_publication_failed;
- runner.notification.failed.

### H.3 Required projections

Current projections expose:

- last_heartbeat_at;
- last_progress_at;
- last_state_transition_at;
- progress_count;
- current state;
- blocked reason;
- stale threshold;
- worker_instance_id;
- seat_id;
- role;
- recent activity.

## I. Three-level progress

### I.1 Overall roadmap

Overall roadmap progress is authoritative and derived only from defined campaign
packages:

    accepted required packages / total required packages

The dashboard displays numerator, denominator, and percentage. Skipped,
cancelled, or undefined work is not silently counted as accepted.

The campaign/objective status remains authoritative; the percentage is a
projection.

### I.2 Current phase

Current phase is the phase_key of the first ordered phase containing an
incomplete required package.

Phase progress is:

    accepted required packages in current phase /
    total required packages in current phase

A phase is complete only when all its required packages are accepted.

### I.3 Current step

Current step is an approximate activity counter for the active package:

- estimate: objective_stages.estimated_progress_units;
- numerator: progress_count for the active package/attempt chain;
- increment: one idempotent meaningful progress event.

Display rules:

- progress_count <= estimate: N / ~estimate;
- progress_count > estimate: +N and counting.

The current-step counter is not an authoritative completion percentage and never
permits acceptance by itself.

## J. Dashboard

Reuse and extend src/riverview/status/server.py and status_snapshot.

V1 is read-only and binds to localhost only. No control buttons are required.

Display:

- campaign name and state;
- overall roadmap progress bar;
- current phase name and progress bar;
- current-step approximate counter;
- current package;
- current phase;
- active seat;
- active role;
- worker_instance_id;
- last heartbeat;
- last meaningful progress;
- last state transition;
- campaign/package timestamps;
- recent chronological activity feed;
- blocked reason;
- stale/possible-stall indication;
- current attempt and lease age.

Refresh behavior:

- browser polls /api/status every three seconds, matching the existing surface;
- each response is one read-only PostgreSQL snapshot;
- no browser action mutates state;
- stale and blocked classification is calculated from timestamps and state,
  not from model text.

## K. Deterministic status classification

Classification precedence is:

1. COMPLETE
2. BLOCKED
3. FAILED
4. STALE
5. ALIVE BUT NO RECENT PROGRESS
6. WORKING

Configured defaults:

- heartbeat target: 120 seconds;
- stale threshold: 360 seconds without a valid heartbeat;
- no-progress threshold: 600 seconds while active.

Rules:

WORKING:
authoritative state is active, heartbeat age <= 360 seconds, and progress age
<= 600 seconds or progress has occurred during the current active interval.

ALIVE BUT NO RECENT PROGRESS:
authoritative state is active, heartbeat age <= 360 seconds, and progress age
> 600 seconds.

STALE:
authoritative state is active and heartbeat age > 360 seconds.

BLOCKED:
authoritative state is blocked, regardless of heartbeat freshness, with a
non-empty blocked reason.

FAILED:
authoritative state is failed or unrecoverably timed_out.

COMPLETE:
campaign/package is accepted/completed according to authoritative state and
acceptance invariants.

A completed or blocked state is not relabeled merely because its worker is
offline.

## L. Notifier hook

Use the existing Python presentation path:

    from estate.core.steward_annunciator import WindowsPresenter
    WindowsPresenter().speak("...")

The runner speaks only for:

- STEWARD_REQUIRED;
- automatic recovery exhausted or package blocked;
- useful phase completion;
- campaign completion.

Routine heartbeat, progress, and ordinary state transitions are silent.

Notification is best-effort presentation. The invocation occurs after the
authoritative database transaction commits, using an idempotency key derived
from the event or attention item.

If speaking fails:

- preserve the campaign/runner state;
- append runner.notification.failed diagnostics/event;
- leave the notification pending for later presentation;
- never roll back engineering success or failure because of audio failure.

## M. Reporting

### M.1 One report, two storage locations

Every completed Codex package produces one Markdown report content object,
identified by content hash, with:

1. local workflow copy;
2. GitHub visibility copy.

The copies must have identical content and report hash.

### M.2 Local workflow copy

Seat-local directories:

- C1: A:\Riverview\repo\docs\codex-reports\seat-1\
- C2: A:\Riverview\repo\docs\codex-reports\seat-2\
- C3: A:\Riverview\repo\docs\codex-reports\seat-3\

Seat-to-seat workflow reads local reports. GitHub is not part of the C1/C2/C3
transport loop.

The report contains package ID, campaign ID, role chain, attempt IDs, basis
hash, base SHA, resulting commit/tree, validation result, defects, evidence,
timestamps, and publication status.

### M.3 GitHub visibility copy

Repository: ppow1/Riverview
Remote: origin
Branch: main

Directories:

- docs/codex-reports/seat-1/
- docs/codex-reports/seat-2/
- docs/codex-reports/seat-3/

The GitHub copy is visibility duplication for external reviewers. Publication
failure is separately represented as pending or failed.

Example state:

    WORK COMPLETE
    LOCAL REPORT COMPLETE
    GITHUB PUBLICATION FAILED

This must not become ENGINEERING FAILED.

A publication failure creates a publication event/diagnostic and may be retried
without rerunning engineering work.

## N. Crash, restart, and resume

### N.1 Runner restart

On startup the runner:

1. reads PostgreSQL authoritative state;
2. registers a new runner/worker instance;
3. scans active attempts and lease ages;
4. leaves fresh leases untouched;
5. fences expired attempts;
6. records late-result/recovery evidence;
7. resumes eligible queued, validation, repair, and revalidation work;
8. rebuilds dashboard projections from PostgreSQL and River events.

No Codex conversation history is required.

### N.2 Worker/process crash

A crashed worker stops heartbeating. After lease expiry, reconciliation fences
the attempt and creates a new attempt only when retry policy allows it.

Any later result from the crashed process is preserved as late/stale and cannot
reconcile, accept, or publish.

### N.3 Machine restart

The same recovery path applies. New processes receive new
worker_instance_id values. Existing local evidence is inspected but does not
override PostgreSQL state.

### N.4 Partially completed attempt

Partial output is evidence only until a fenced terminal result and repository
reconciliation exist. The runner must not infer success from files, prose, or
an open process alone.

### N.5 Validator crash

Validator attempts expire and are re-created with a new attempt identity and
new fencing token. The package remains validation_pending or validation_running
until a valid validator result exists.

### N.6 Notifier failure

Notification failure is isolated from campaign state as specified in section L.

### N.7 Dashboard restart

The dashboard is stateless. It re-queries PostgreSQL and River projections on
each request and requires no dashboard-local recovery state.

## O. One-GO operator flow

The operator experience is:

1. create/load campaign specification and immutable validation basis;
2. issue one start/go command;
3. runner claims eligible packages;
4. writer and validator workers claim role-appropriate work;
5. repair and revalidation cycles proceed automatically;
6. C3 arbitration occurs only on configured exceptional conditions;
7. dashboard continuously exposes progress and blockers;
8. notifier summons the Steward only for defined attention conditions;
9. campaign reaches completed/accepted or a meaningful blocked/failed state.

Conceptual commands only:

- create/load;
- start/go;
- status;
- resume.

Exact CLI syntax is deferred to existing Riverview CLI conventions. No manual
copy/paste between Codex conversations is part of the normal flow.

Grace is not required for any of these commands.

## P. Minimal physical database changes

### Reuse unchanged

Reuse without schema duplication:

- river_events;
- diagnostic_events;
- objective_stage_dependencies;
- execution_lanes;
- lane_path_owners;
- steward_escalations;
- steward_notifications;
- migration ledger;
- existing status HTTP server.

### Extend

1. objectives:
   - attention_required;
   - active_stage_id;
   - acceptance_state.

   Necessary for campaign-level attention and explicit acceptance projection.
   Existing objective status does not distinguish accepted from merely
   completed/operationally advanced.

2. objective_stages:
   - phase_key;
   - phase_title;
   - eligible_seats;
   - estimated_progress_units;
   - blocked_reason;
   - last_progress_at;
   - progress_count.

   Necessary to represent ordered phases and package seat eligibility, while
   execution role is represented on each work order/attempt, and to provide
   approximate step telemetry without creating phase/package duplicates.

3. work_orders:
   - active_attempt_id;
   - lease_generation;
   - fencing_token;
   - worker_instance_id;
   - seat_id;
   - role;
   - last_progress_at;
   - progress_count;
   - blocked_reason.

   Necessary because lease_owner alone cannot fence stale completion.

4. work_order_attempts:
   - explicit attempt_id;
   - lease_generation;
   - fencing_token;
   - worker_instance_id;
   - seat_id;
   - role;
   - heartbeat/progress fields;
   - terminal state;
   - late-result markers.

   Necessary to preserve immutable attempt history and late-result evidence.

5. relay_workers:
   - worker_instance_id;
   - seat_id;
   - supported roles;
   - stale/heartbeat projection fields as needed.

   Necessary to distinguish process incarnation, seat, and role.

6. execution_envelopes:
   - attempt_id;
   - fencing_generation/token;
   - worker_instance_id;
   - role;
   - validation_basis_hash.

   Necessary to bind execution and validation to one fenced attempt.

7. execution_results:
   - attempt_id;
   - fencing fields;
   - worker_instance_id;
   - late_or_stale;
   - authoritative_result.

   Necessary to preserve late results without letting them advance state.

### Add indexes and constraints

Add only indexes needed by actual runner queries:

- work_orders active-attempt/lease lookup;
- work_orders dispatch by status and eligibility;
- work_order_attempts lookup by work_order_id and active attempt;
- work_order_attempts lookup by worker_instance_id and heartbeat;
- objective_stages lookup by objective_id, phase_key, status;
- River event lookup by campaign/package correlation.

Add constraints:

- fencing_token is non-null whenever active_attempt_id is non-null;
- worker_instance_id is non-null whenever an attempt is active;
- progress_count >= 0;
- estimated_progress_units > 0;
- acceptance_state uses the closed set;
- package_role uses the closed set;
- seat IDs use C1/C2/C3;
- active attempt identity is unique for a work order;
- attempt_id is unique;
- fencing_token is unique per attempt.

Do not add a campaign_runs table, package table, dependency table, defect table,
artifact platform, or separate telemetry table unless implementation proves an
existing structure cannot satisfy the specific requirement.

### Defer / not needed

Defer:

- generalized provider routing;
- GPU scheduling;
- new Grace abstractions;
- broad repository/worktree hardening;
- advanced merge/publication system;
- notification redesign;
- generalized artifact-management platform;
- additional security framework.

## Q. State transition matrix

Required evidence and fencing are summarized in the matrix. “Exact” means the
full work_order_id, attempt_id, lease_generation, fencing_token, and
worker_instance_id tuple.

| Source | Destination | Actor | Required evidence/fencing | Event | Steward notification |
|---|---|---|---|---|---|
| queued | claimed | eligible worker | claim transaction; no active attempt; new exact tuple | runner.attempt.claimed | No |
| claimed | running | worker | process start; exact tuple | runner.state_transition | No |
| running | validation_pending | writer | fenced writer result; changed tree/evidence persisted | runner.state_transition | No |
| validation_pending | validation_running | independent validator | new validator attempt; writer identity exclusion | runner.attempt.claimed/state_transition | No |
| validation_running | accepted | validator | fenced PASS; immutable basis; actual tree/evidence; no defects | runner.validation.pass/state_transition | No, unless campaign/phase completion |
| validation_running | defects_found | validator | fenced FAIL; structured defect set | runner.validation.defects | No |
| defects_found | repair_pending | runner | persisted unresolved defects and repair eligibility | runner.state_transition | No |
| repair_pending | repair_running | repair writer | new fenced repair attempt | runner.attempt.claimed/state_transition | No |
| repair_running | revalidation_pending | repair writer | fenced repair result; actual tree/evidence | runner.state_transition | No |
| revalidation_pending | revalidation_running | independent revalidator | new attempt; writer identity exclusion | runner.attempt.claimed/state_transition | No |
| revalidation_running | accepted | revalidator | fenced PASS; basis unchanged; defects resolved; evidence | runner.revalidation.pass/state_transition | No, unless completion |
| revalidation_running | defects_found | revalidator | fenced FAIL; new structured findings | runner.revalidation.defects | No |
| any active | timed_out | reconciler | lease expiry; exact lease re-check | runner.attempt.timed_out | Only if recovery exhausted |
| any active | failed | runner/reconciler | fenced terminal failure or unrecoverable diagnostic | runner.state_transition | Yes if attention required |
| any eligible | blocked | runner | explicit blocker, missing basis, retry threshold, or arbitration decision | runner.state_transition | Yes |
| blocked | queued | operator/recovery | blocker resolution and new admission/retry authorization | runner.state_transition | No |
| defects_found | blocked | runner | repair threshold exceeded or ambiguous evidence | runner.state_transition | Yes |
| any active | accepted | no direct writer actor | Prohibited unless validator/revalidator/arbitrator PASS is fenced and complete | no valid event | N/A |
| any active | late result | stale worker | mismatch preserved as non-authoritative evidence | runner.result.late_rejected | No, unless policy says attention |
| accepted package | accepted campaign | runner | all required packages accepted; campaign invariants | runner.campaign.completed | Yes |
| accepted package | next eligible package | runner | dependency and phase evaluation | runner.package.eligible | No |

A writer result may never perform the running → accepted transition.

## R. Acceptance test matrix for RUN-003+

| ID | Test | Required result |
|---|---|---|
| 1 | normal writer → validator → PASS | Package becomes accepted only after validator PASS |
| 2 | writer → defects → repair → revalidation PASS | Full history preserved; package accepted |
| 3 | writer attempts self-validation | Assignment rejected |
| 4 | stale writer result arrives | Result preserved; no authoritative change |
| 5 | expired lease receives retry | New attempt, generation, token, and worker instance |
| 6 | heartbeat without accomplishment | Heartbeat updates only liveness |
| 7 | progress event | Progress count and last progress update once |
| 8 | progress exceeds estimate | Dashboard displays +N and counting |
| 9 | roadmap progress | Derived only from accepted defined packages |
| 10 | phase progress | Derived only from accepted packages in current phase |
| 11 | worker crash | Lease expires; recovery resumes safely |
| 12 | validator crash | New validator attempt; no self-acceptance |
| 13 | blocked package | Notifier invoked after committed blocked state |
| 14 | normal heartbeat | No notifier invocation |
| 15 | stale worker | Dashboard shows stale classification |
| 16 | Grace unavailable | Runner starts and advances work independently |
| 17 | GitHub publication fails | Local report remains usable |
| 18 | publication failure | Engineering verdict remains unchanged |
| 19 | normal repair cycle | C3 arbitration is not invoked |
| 20 | one GO command | Campaign proceeds without manual copy/paste handoffs |
| 21 | mismatched generation | Heartbeat and completion are fenced |
| 22 | mismatched fencing token | Result becomes late/stale evidence |
| 23 | mismatched worker instance | Result cannot reconcile or publish |
| 24 | changed basis content | Hash mismatch blocks validation |
| 25 | changed acceptance criteria | New basis revision required |
| 26 | validator sees actual resulting tree | PASS/FAIL binds to actual code/tree |
| 27 | notifier process failure | Campaign state remains intact |
| 28 | dashboard restart | Projection rebuilds from PostgreSQL |
| 29 | revalidation by repair writer | Assignment rejected |
| 30 | arbitrary writer prose claiming success | No acceptance transition |

## Readiness

This specification is READY_FOR_INDEPENDENT_VALIDATION.

It is design-only. It creates no migrations, modifies no runtime code, redesigns
no Grace behavior, and defers RUN-001R future-hardening items.
