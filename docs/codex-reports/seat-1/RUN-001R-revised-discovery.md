# RUN-001R — Revised Architecture Recommendation

## Purpose

This report revises RUN-001 only for the validated requirements needed to establish a safe basis for RUN-002. Riverview remains the reusable foundation. The Campaign Runner should extend the existing Relay, execution-envelope, reconciliation, River-event, and status-projection paths. It should not create a parallel runner architecture.

## Blocking requirements

### 1. Fenced attempt completion

Terminal updates must match the exact active attempt using all of:

- `work_order_id`
- `attempt_id`
- `lease_generation`
- `fencing_token`
- `worker_instance_id`

Results from expired, superseded, or mismatched attempts may be preserved as late-result evidence, but must not advance authoritative work, campaign, stage, or acceptance state.

### 2. Independent writer and validator lifecycle

The required lifecycle is:

```text
writer result
  → independent validator
  → PASS or structured defects
  → repair attempt
  → independent revalidation
  → accepted
```

The writer may not validate its own attempt. Writer completion is never equivalent to acceptance.

### 3. Immutable validation basis

Validation must bind to the original specification and specification hash, acceptance criteria, original base SHA, actual resulting code/tree, declared changed paths, validation commands, evidence, and validator identity/attempt.

Writer completion prose is a summary only and is not acceptance evidence.

### 4. Grace-independent operation

The Campaign Runner must start, dispatch, execute, validate, repair, recover, and expose status without Grace. Grace may later consume runner events or orchestrate campaigns, but no runner-critical path may require Grace identity, conversation, intent formation, or objective evaluation.

### 5. Distinct liveness and lifecycle signals

The runner must separately maintain:

- `last_heartbeat_at` — worker is alive;
- `last_progress_at` — meaningful activity occurred;
- `progress_count` — meaningful progress count;
- current authoritative state;
- blocked reason.

Heartbeat, progress, and authoritative state transition must remain distinct.

## Required implementation details

### Reuse the Riverview foundation

Reuse the existing PostgreSQL-authoritative objects and code paths:

- `work_orders`, `work_order_attempts`, `RelayStore.claim`, `heartbeat`, `complete`, and retry handling;
- `execution_envelopes`, `execution_results`, and `reconciliation_records`;
- `objectives`, `objective_stages`, and `objective_stage_dependencies`;
- `execution_lanes` and `lane_path_owners`;
- `river_events`, `diagnostic_events`, Steward escalations, and notification records;
- the existing restricted subprocess runner and Codex adapter;
- the existing localhost-only Riverview status server.

The existing lease-owner check is not sufficient. Extend the existing attempt/work-order execution records with the fencing tuple and verify it transactionally on heartbeat, terminal result, and reconciliation operations.

### Writer and validator roles

Represent writer, validator, repair writer, and revalidator as explicit execution roles. Validator work must reference the writer result and immutable validation basis. Revalidation must use a new validator attempt and must not reuse writer authority.

### State model

The runner must support, at minimum:

```text
queued
claimed
running
validation_pending
validation_running
defects_found
repair_pending
revalidation_pending
accepted
blocked
failed
timed_out
```

Only fenced, transactionally valid transitions may advance state.

### Dashboard

Extend the existing read-only Riverview status projection to show:

- overall roadmap progress;
- current phase progress;
- approximate current-step counter;
- generated, started, and updated timestamps;
- active seat and role;
- recent activity;
- stale heartbeat visibility;
- blocked state and reason.

The existing standard-library `ThreadingHTTPServer` remains sufficient.

### Multi-seat Codex

Concurrent independent C1/C2/C3 operation is an accepted operating fact established by the Steward's repeated daily operation. It is not an architectural blocker or open risk for RUN-002.

Use the existing seat mappings:

- `C1` → `A:\\AI\\CodexProfiles\\C1`
- `C2` → `A:\\AI\\CodexProfiles\\C2`
- `C3` → `A:\\AI\\CodexProfiles\\C3`

Record seat identity and worker-instance identity for attribution and fencing.

## Future hardening / non-blocking observations

The following are intentionally outside RUN-002 unless later required by an actual runner failure:

- broader repository/worktree collision hardening;
- richer artifact cataloging;
- additional supervisor policy;
- advanced merge/publication controls;
- generalized provider routing;
- further Grace integration;
- replacement of existing JSON evidence surfaces;
- security mechanisms beyond those required for attempt fencing and bounded execution.

These are follow-up observations, not prerequisites for the runner specified here.

## RUN-002 boundary

RUN-002 should implement only:

1. fenced attempt identity and terminal updates;
2. independent writer/validator/revalidation flow;
3. immutable validation-basis capture;
4. distinct heartbeat, progress, and state fields;
5. read-only dashboard projection;
6. Grace-independent startup and operation;
7. existing C1/C2/C3 seat assignment and attribution.

No parallel job system, unrelated runtime changes, or additional abstractions are required by this recommendation.

## Existing source evidence

- PostgreSQL connection and transactions: `src/riverview/database/connection.py`
- Work orders, leases, attempts, and retries: `src/riverview/relay/store.py`
- Worker dispatch and heartbeat: `src/riverview/relay/worker.py`
- Codex execution: `src/riverview/runner.py`
- Codex command and seat identity: `../theestate/src/estate/core/codex_bridge.py`
- Objective/dependency model: `src/riverview/grace/objectives.py`
- Execution envelopes and results: `database/migrations/0014_autonomous_control_plane.sql`
- Execution lanes and path ownership: `database/migrations/0017_lanes_reconciliation.sql`
- Read-only status server: `src/riverview/status/server.py`

