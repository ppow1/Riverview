<!-- Version: 1.0.0 -->
# Riverview authoritative roadmap reconciliation — 2026-08-20

## Finding

The checked-in master roadmap was a stale source projection. PostgreSQL held
the authoritative append-only transition ledger and showed accepted transitions
through the Grace, Relay, Comms/MCP, provider, recovery, operator, migration,
and operational-maturity work that the JSON still labelled `pending`.

The reconciliation preserves that history. It updates the versioned JSON
projection to the statuses already established by PostgreSQL; it does not create
new acceptance transitions or reinterpret historical evidence.

## Authority and evidence

- Starting published source: `6931ed74ef38b3297772f4b1d7997157ab8e1488`.
- PostgreSQL database: `riverview` on `127.0.0.1:5432`; `SELECT 1` passed.
- The `roadmap_transitions` ledger contains 101 append-only transitions.
- The source evidence is referenced by those transitions and includes the
  Grace production proof, MCP/Playwright checkpoints, provider/capacity and
  execution evidence, recovery evidence, topology/observability evidence,
  and the later roadmap evidence directory.
- Runtime supervisor, CME, Comms5 HTTP/transport, Relay worker, and Operator
  were running at verification; the supervisor SHA matched published main.

## Remaining frontier

The only non-terminal rows after reconciliation are:

- `RV-016` — pending because its final child acceptance is still open.
- `RV-016.5` — genuinely incomplete. The factual audit records that the
  current implementation is a Python model/prototype without real Quest,
  headset, frame/comfort, or end-to-end experiential evidence. The earlier
  machine-only completion was explicitly reopened and remains historical.
- `RV-018` — pending because final Estate acceptance remains open.
- `RV-018.6` — genuinely incomplete. Final Steward acceptance and the full
  human resident/room workflow remain unobserved and explicitly unclaimed.

`RV-016.5` is the first unfinished dependency-ready leaf. No Ready Bench item
was manufactured because the board remains empty and no new Steward-committed
specification was supplied.

## Scope boundary

This reconciliation changed roadmap projection metadata/statuses only. It did
not reopen Grace, Comms5 transport, PostgreSQL, or already-proven production
mechanisms, and it did not alter authority semantics or unrelated worktree
files.
