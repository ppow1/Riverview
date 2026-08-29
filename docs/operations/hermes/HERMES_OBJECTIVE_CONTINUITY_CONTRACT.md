# Hermes Objective-Continuity Contract

Status: Implemented bounded contract, v1.0

## Purpose

Separate completion of one Hermes model turn from completion of the authorized
Riverview engineering objective. A normal assistant response with
`finish_reason=stop` ends only the model turn. It does not independently prove
that the objective is complete.

## Dispositions

The closed disposition set is:

- `CONTINUE`: executable work remains within the same authorized objective.
- `OBJECTIVE_COMPLETE`: Hermes reports that the objective acceptance boundary
  is satisfied; Riverview/CME must independently validate it.
- `READY_FOR_STEWARD_REVIEW`: work is ready for review and pauses there.
- `BLOCKED_REQUIRES_STEWARD`: a concrete Steward action is required.
- `STEWARD_DECISION_REQUIRED`: an exact policy/authority decision is required.
- `RETRYABLE_FAILURE`: bounded failure may be retried under existing policy.
- `TERMINAL_FAILURE`: execution cannot continue safely in this run.

`COMPLETED_NO_ATTENTION` remains a compatibility alias for an objective-complete
run-boundary notification. New envelopes should use `OBJECTIVE_COMPLETE`.

## Structured envelope

The model emits one marker:

```text
<!-- RIVERVIEW_TERMINAL_OUTCOME {
  "disposition": "CONTINUE",
  "objective_id": "...",
  "work_order_id": "...",
  "checkpoint_id": "RIV-...",
  "summary": "...",
  "evidence_refs": ["..."],
  "remaining_work": [
    {"work_id": "live-acceptance", "description": "Run live acceptance",
     "executable": true, "status": "pending"}
  ],
  "blocked_reason": null,
  "decision_required": null
} -->
```

All lists and text are bounded. `CONTINUE` is invalid unless at least one
remaining-work item is executable and pending/in progress. Missing or malformed
structured state fails closed when the Riverview objective-continuity plugin is
active; ordinary non-Riverview Hermes sessions retain legacy behavior.

## Runtime lifecycle

1. Hermes receives one authorized objective/work-order context.
2. The model performs tools and delegated work within hard limits.
3. A no-tool response completes one model turn.
4. Hermes parses the structured disposition before its legacy text-response exit.
5. `CONTINUE` persists the real checkpoint in memory, adds private bounded
   continuation scaffolding, and requests another internal model turn.
6. Terminal dispositions return through the existing finalizer and plugin bridge.
7. The bridge strips the marker from human text and emits existing attention or
   run-boundary signals exactly once.
8. CME consumes the structured outcome using root/correlation/work-order
   correspondence and its bounded anti-spin policy.

Hard-stop precedence is unchanged: max iterations/shared budget, timeout or
provider deadline, context/compression exhaustion, provider/subprocess failure,
interrupt/cancellation, guardrail halt, persistence failure, and interpreter
shutdown terminate safely and are not converted into successful completion.

## Responsibilities and authority

Hermes owns execution of the authorized objective, internal continuation, and
turn/run diagnostics. Hermes does not advance Riverview's authoritative
workflow merely because it emits `OBJECTIVE_COMPLETE`.

CME owns objective/work-order reconciliation, evidence validation, acceptance,
retry policy, attention state, and authoritative progression. `OBJECTIVE_COMPLETE`
becomes progression only after CME's existing acceptance/reconciliation gate
succeeds. `CONTINUE` is internal execution state and must retain root,
correlation, request, result, and work-order identity.

The Steward remains the authority for review, policy, credential, physical, and
scope decisions.

## Result semantics and diagnostics

`completed` remains backward-compatible and means that the Hermes model turn
returned a result. Consumers requiring objective semantics must use:

- `turn_completed`;
- `objective_completed`;
- `objective_disposition`;
- `continuation_gate_evaluated`;
- `continuation_decision`.

Turn diagnostics include session/turn identity, finish reason, turn-exit
reason, effective API/budget counters, disposition, gate decision, and bounded
remaining-work information. No secrets or private prompts are recorded.

## Acceptance criteria

- A structured `CONTINUE` after an intermediate commit/test causes another
  internal model turn without returning control to the Steward.
- Hard stops still terminate and remain explicit.
- Objective-complete reports do not directly mutate authoritative Riverview
  state.
- Attention dispositions use the existing exactly-once notification bridge.
- CME remains root-scoped and bounded against no-progress loops.
- Missing/malformed dispositions fail closed in active objective mode.
- Codex app-server and standard Hermes paths use equivalent objective semantics
  where the structured envelope is available.
