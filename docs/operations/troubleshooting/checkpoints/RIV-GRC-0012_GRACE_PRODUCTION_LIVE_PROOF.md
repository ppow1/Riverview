# RIV-GRC-0012 — Grace production live proof

Grace core on `main` is the authoritative production implementation. Runtime
claims must reconcile to that repository revision and PostgreSQL operational
evidence; branches, provider completion prose, and browser state are not
authority.

## Runtime topology and health invariants

The expected topology has one `riverview.runtime.supervisor` owner for one
Operator service, one CME supervisor tree with one live CME consumer, one
Comms5 HTTP/transport pair, and one Relay worker owner. There must be no
duplicate owner or listener. Health requires the declared dependencies and
loopback endpoints to be available, a current CME heartbeat, a monotonic River
cursor caught up through durable events, and PostgreSQL-backed projections that
do not claim stale state as current.

## One-approval engineering flow

One explicit Steward approval for one exact specification creates the durable
authority grant. Grace consumes it to form the bounded intent, Relay queues and
leases the declared action, Codex executes only the approved repository/base,
path, criteria, evidence, and `write_policy=bounded_write` scope, and independent
reconciliation accepts completion only from authoritative repository evidence.
The unchanged valid scope needs no second approval; stale base, scope drift,
missing evidence, or reconciliation failure fails closed.

## Operator recovery invariant

After a transient CME recycle, Operator Activity and `/cme` must automatically
move through unavailable/reconnecting state and converge on the current
PostgreSQL-backed CME and River projections. Recovery must use bounded retry,
cache-safe polling, and cursor reconciliation; it must not require a manual
browser refresh.
