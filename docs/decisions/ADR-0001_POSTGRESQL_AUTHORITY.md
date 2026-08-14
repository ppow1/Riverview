<!-- Version: 0.1.0 -->
# ADR-0001: PostgreSQL Is the Authoritative River State Store

Status: Accepted

## Decision

PostgreSQL stores authoritative operational state for events, objectives, workflows, work, leases, mailbox messages, diagnostics, Cookbook knowledge, and audit provenance.

SQLite is permitted only for isolated caches, offline adapters, and tests that do not claim PostgreSQL concurrency equivalence. JSON remains a bounded payload and interchange format, not the workflow database.

## Reason

Riverview requires concurrent writers, transactional claims, leases, idempotency, indexing, recovery, and durable correlation. PostgreSQL provides these without constructing a custom file-state system.

## Consequences

- All schema changes use ordered migrations.
- Important searchable state uses typed columns.
- JSONB is permitted for bounded extensible payloads.
- Large artifacts remain outside PostgreSQL and are referenced by metadata.
- Concurrency and recovery acceptance run against PostgreSQL.
