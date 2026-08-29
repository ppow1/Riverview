---
name: riverview-objective-continuity
description: "Use for bounded Hermes engineering objectives that must continue across model turns."
version: 1.0.0
author: Project Riverview
license: Internal procedural guidance
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [riverview, hermes, continuity, cme, engineering]
---

# Riverview Objective Continuity

A model turn is not an engineering objective. A tool call, commit, passing test,
implementation increment, or coherent report is not objective completion unless
the authorized acceptance boundary is satisfied.

## Required response contract

For a bounded Riverview engineering objective, include exactly one structured
marker in the final text:

```text
<!-- RIVERVIEW_TERMINAL_OUTCOME {JSON} -->
```

Use `disposition` with one of:

- `CONTINUE`
- `OBJECTIVE_COMPLETE`
- `READY_FOR_STEWARD_REVIEW`
- `BLOCKED_REQUIRES_STEWARD`
- `STEWARD_DECISION_REQUIRED`
- `RETRYABLE_FAILURE`
- `TERMINAL_FAILURE`

`CONTINUE` requires a bounded non-empty `remaining_work` list. Each item must
contain `work_id`, `description`, `executable`, and `status`. Describe only work
within the same authorized objective and preserve its objective/work-order and
checkpoint identities when available.

`OBJECTIVE_COMPLETE` means the authorized objective's actual acceptance boundary
is satisfied, not merely that an intermediate implementation or validation step
passed. Riverview/CME independently validates evidence and owns authoritative
workflow progression; never claim that returning this disposition changes
PostgreSQL or roadmap state.

Use `READY_FOR_STEWARD_REVIEW` only when the next step is review. Use
`BLOCKED_REQUIRES_STEWARD` only when a concrete external authority, credential,
physical intervention, or other Steward action is required. Use
`STEWARD_DECISION_REQUIRED` only at an exact policy or authority decision
boundary. Use failure dispositions for failures; never disguise them as
completion.

## Continuation rule

When executable internal work remains, emit `CONTINUE` and keep working. Do not
return a progress report merely because a model turn ended. Continue through
reload, live acceptance, evidence resolution, repeat acceptance, and remaining
bounded tests when those are part of the authorized objective. Preserve hard
limits, cancellation, guardrails, provider failures, context exhaustion, and
other safety/resource boundaries.

Never encode remaining work only in prose. Do not search for phrases such as
"work remains" to decide the state. The structured disposition is the contract;
Hermes enforces it and CME reconciles it.
