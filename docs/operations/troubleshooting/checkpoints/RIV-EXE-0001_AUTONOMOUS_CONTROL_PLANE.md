# RIV-EXE-0001 — Autonomous control-plane boundary

Owner: Grace momentum, capability registry, and the named Codex engineering adapter.

## SYMPTOM

An objective appears ready, but no bounded provider can be selected or an execution
result cannot be reconciled to its envelope.

## LIKELY BOUNDARY

PostgreSQL capability/capacity state, the execution envelope base SHA/path scope, or
the local Codex CLI process boundary.

## SAFE DIAGNOSTIC

Inspect the `capabilities`, `capability_capacity`, `execution_envelopes`, and
`execution_results` projections. Verify the repository identity, expected base SHA,
relative allowed paths, measured capability health, and bounded deadline.

## EXPECTED HEALTHY RESULT

One enabled healthy capability with current capacity is selected deterministically;
one durable envelope is created for its retry key; and one typed result is persisted.

## KNOWN FAILURE

`RIV-EXE-0001` rejects malformed envelopes; `RIV-EXE-0002` rejects a missing or
non-Git repository; `RIV-EXE-0003` records a bounded Codex timeout; `RIV-EXE-0004`
records a nonzero Codex exit; `RIV-EXE-0005` rejects an unverifiable publication claim;
`RIV-CAP-0002` rejects missing or overcommitted capacity.

For `RIV-EXE-0003`, inspect the persisted bounded timeout summary before assigning
the slow phase. It records the provider PID, elapsed time, last structured event
type, bounded redacted stdout/stderr tails, changed paths observed in the isolated
worktree, and whether each approved target existed at timeout. Windows timeout
cleanup terminates the provider process tree; no timeout result is copied back,
committed, or published.

The first Windows acceptance attempt also failed before process start because the
installed CLI was exposed as `codex.cmd`, while a bare `codex` name is not directly
launchable by `CreateProcess`. This is classified as executable discovery, not a
provider or authority failure.

## REPAIR

Repair only the failing bounded layer: resolve the installed `codex.cmd`/`codex.exe`
entry point without changing the instruction or repository scope; then register
measured capability evidence, refresh
capacity, re-anchor the expected SHA, or recover the named local Codex CLI. Use the
same retry key for a retry-safe transport/provider failure and no more than one retry.

## VERIFY

Confirm the envelope is unique by retry key, the result correlation matches, changed
paths remain within the envelope, validation evidence is durable, and no remote
publication is claimed without an independently verified SHA.

## DO NOT

Do not turn an envelope into shell text, accept a provider label without measured
evidence, bypass the base-SHA/path boundary, add an OpenAI API route, or expose this
execution capability through a generic MCP tool.

## EVIDENCE

Authoritative evidence is PostgreSQL state in the five control-plane tables and the
correlated River/checkpoint references. Adapter stdout/stderr is bounded diagnostic
evidence only and never operational authority.
