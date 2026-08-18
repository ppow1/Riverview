# RIV-RUN-0001 — Unified Riverview lifecycle boundary

## Symptom

Riverview services are running as unrelated Windows startup tasks, a required
service has no owner, or a component is healthy but its lifecycle owner is
ambiguous.

## Authority

`riverview.runtime.supervisor` is the single Riverview top-level lifecycle
owner. The Windows task `Riverview Runtime Supervisor` hosts it. CME retains
its subordinate `CMESupervisor` child-recovery boundary; it is not a peer
top-level owner.

## Diagnostic procedure

1. Read `runtime/riverview-supervisor/status.json` and verify the supervisor
   revision, service identities, dependency state, PIDs, and failure metadata.
2. Verify exactly one `Riverview Runtime Supervisor` task and one supervisor
   lock owner.
3. Verify each registered service has at most one matching process/listener.
4. Inspect only credential availability metadata; never read or print secret
   values.
5. Compare the registry with the installed topology and the expected health
   probes.

## Recovery

Use `Install-RiverviewRuntimeSupervisor.ps1` for idempotent installation or
start the installed `Riverview Runtime Supervisor` task through Task Scheduler.
The installer backs up peer task definitions, disables the Riverview CME/Comms5
peer tasks when migration is requested, and starts the unified owner. Do not
invoke component modules directly during recovery. A stale lock is recoverable
only when its recorded owner PID is no longer alive; a live lock is an
escalation, not permission to create a second supervisor.

Operator obtains `RIVERVIEW_OPENWEBUI_TOKEN` in memory from the approved local
credential handoff defined by RIV-UI-0014. The value never appears in command
lines, status, logs, snapshots, or River.

## Healthy verification

The status projection is present, its `supervisor_pid` and lock owner agree,
the supervisor Git SHA matches the accepted repository, Operator is healthy on
`127.0.0.1:18082`, Comms5 owns only `127.0.0.1:11826`, CME reports a healthy
heartbeat, and the peer tasks are disabled after migration. A second start
produces no duplicate process tree. If PostgreSQL or the approved remote
transport is unavailable, the status projection must retain the bounded
failure and dependency state rather than claiming healthy operation.

## Escalation

Escalate if the registry is invalid, the credential source is unavailable, a
foreign process owns a required port, the supervisor lock is contested, or a
peer task cannot be safely reconciled. Do not create a second scheduler or
manually mutate PostgreSQL.
