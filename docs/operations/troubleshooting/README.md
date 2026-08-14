<!-- Version: 0.3.0 -->
# Riverview Troubleshooting Cookbook

Status: Designed; initial kernel entries pending implementation evidence.

The Cookbook is a living operational knowledge system connected to implementation revisions, diagnostic events, induced-failure tests, and recovery verification.

## Required checkpoint knowledge

Every checkpoint records:

- Stable checkpoint ID
- Component and seam ownership
- Triggering operation
- Known failure classes
- Evidence captured automatically
- Safe distinguishing probes
- Smallest permitted repair
- Recovery verification
- Escalation boundary
- Applicable implementation revisions
- Validation and staleness state

## Initial checkpoint namespace

- `RIV-DB-*` — database, migration, transaction, and projection
- `RIV-DIA-*` — diagnostic persistence and emergency evidence spooling
- `RIV-BLD-*` — build, packaging, and dependency-environment failures
- `RIV-EVT-*` — event acceptance and delivery
- `RIV-WRK-*` — worker assignment, attempts, ownership, and leases
- `RIV-CME-*` — momentum detection and recovery
- `RIV-MCP-*` — mailbox, correlation, claims, and responses
- `RIV-PLY-*` — Playwright doorbell and conversation state
- `RIV-LOC-*` — local execution adapters
- `RIV-SEC-*` — classification and Undercurrent boundaries

## Acceptance rule

No capability is operationally complete until a new AI conversation can identify the checkpoint, distinguish modeled failures, perform the smallest safe repair, and verify recovery from repository guidance and captured evidence.
