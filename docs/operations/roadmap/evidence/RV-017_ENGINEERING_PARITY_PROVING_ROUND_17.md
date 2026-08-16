# RV-017 engineering parity proving round 17

## Scope and decision

The Steward-approved RV-017.6 decision was applied as `NO NEW TRANSFER —
RETAIN CURRENT RIVERVIEW AUTHORITY`. No Estate authority was transferred, no
Estate service was retired, and rollback remains available. RV-017.6 and the
RV-017 parent were promoted from the accepted parity, migration, shadow, and
rollback evidence.

## Real objectives

Three bounded Riverview maintenance objectives were accepted through project
intake and the PostgreSQL-authoritative Grace objective model. The two first
implementation lanes were dispatched concurrently with disjoint path
ownership.

### 1. Service topology cycle safety

- Objective: `rv17-proof-topology-cycle`
- Correlation: `327d8995-3cae-4f5d-84c2-53acf9982a52`
- Provider execution: `41e067d0-3b5a-4a03-8411-1013f61730e1`, `codex-cli-local`
- Change: cyclic service dependencies now fail closed with `RIV-INF-0001`;
  focused tests cover self-cycles, multi-node cycles, and missing dependencies.
- Validation: focused test passed; full suite passed; committed in `518a100`.
- Steward intervention: none.

### 2. Recursive operational redaction

- Objective: `rv17-proof-observability-redaction`
- Correlation: `a0b2aace-6506-4c2f-8ef4-d2ee1d00d949`
- Provider execution: `3458bc60-b893-4691-9062-7b759bed18ac`,
  `codex-cli-local`; the verification process returned `RIV-EXE-0004`.
- Change: observability projection now recursively removes private keys from
  nested mappings and sequences, case-insensitively.
- Recovery: the existing bounded execution checkpoint was recorded, then the
  focused and full project suites were rerun successfully from the Riverview
  environment. The implementation was committed in `518a100`.
- Steward intervention: none.

### 3. Grace continuation after provider return

- Objective: `rv17-proof-grace-continuation`
- Correlation: `69e2425e-b984-4e8e-9002-5e36bd0b9c95`
- Provider execution: `d1f99fff-759a-4b68-8e16-af34dfac4212`,
  `codex-cli-local`; bounded process termination was recorded as
  `RIV-EXE-0004` and recovered with local validation.
- Change: `ContinuousMomentumEngine.cycle_until_quiescent()` now iteratively
  re-queries the authoritative frontier, redispatches declared approved
  actions, stops at no-progress/external boundaries, excludes Steward
  checkpoints, and enforces a cycle bound. Focused tests cover multi-cycle
  continuation, no-progress stopping, checkpoint exclusion, declared-action
  redispatch, and invalid bounds.
- Validation: focused and full suites passed; Ruff and compile passed;
  implementation committed in `518a100`, `ce068c7`, and `ea0e521`.
- Steward intervention: none.

## Grace/Codex result

Intake, objective creation, bounded path ownership, Codex dispatch, result
recording, failure checkpointing, recovery, tests, and objective
reconciliation were exercised. The two independent implementation lanes ran
concurrently without path overlap. The continuation contract is now proven by
real repository code and focused boundary tests. End-to-end autonomous
redispatch against a live external provider is **partially proven**, because
the verification Codex process itself hit `RIV-EXE-0004`; the safe fallback and
declared-action path are covered, but no claim is made that every provider
return is already auto-recovered in production.

## Engineering parity scorecard

| Capability | Result |
|---|---|
| Intake | PROVEN REAL |
| Repository archaeology | PROVEN REAL |
| Task decomposition | PROVEN REAL |
| Provider selection | PROVEN REAL |
| Codex execution | PROVEN REAL |
| Local-AI support | PARTIALLY PROVEN |
| Parallel execution | PROVEN REAL |
| Failure diagnosis | PROVEN REAL |
| Cookbook recovery | PROVEN REAL for the observed execution checkpoint |
| Result reconciliation | PROVEN REAL |
| Git publication | PROVEN REAL for Riverview publication |
| Objective continuation | PARTIALLY PROVEN; bounded contract and tests pass |
| Steward intervention burden | PROVEN REAL: none for these objectives |
| Restart/context recovery | PARTIALLY PROVEN |
| Project isolation | PROVEN REAL |

## Estate comparison

This round proves Riverview can accept bounded objectives, inspect its own
repository, decompose and dispatch work, run real code changes, validate,
diagnose a provider execution failure, recover, reconcile, and publish without
Pat intervening in ordinary stages. No authoritative evidence in this round
establishes an Estate capability that Riverview cannot match for these bounded
software objectives. Quest/3D experiential work remains explicitly deferred;
that is a known pending capability, not a hidden completion claim.
