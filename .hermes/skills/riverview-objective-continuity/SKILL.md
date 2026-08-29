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

For a bounded Riverview engineering objective, include exactly one structured
marker in the final text:

```text
<!-- RIVERVIEW_TERMINAL_OUTCOME {JSON} -->
```

Use `disposition` with one of `CONTINUE`, `OBJECTIVE_COMPLETE`,
`READY_FOR_STEWARD_REVIEW`, `BLOCKED_REQUIRES_STEWARD`,
`STEWARD_DECISION_REQUIRED`, `RETRYABLE_FAILURE`, or `TERMINAL_FAILURE`.

`CONTINUE` requires a bounded non-empty `remaining_work` list. Every item must
contain `work_id`, `description`, `executable`, and `status`. Describe only work
within the same authorized objective and preserve objective/work-order and
checkpoint identities when available.

`OBJECTIVE_COMPLETE` means the actual authorized acceptance boundary is
satisfied, not merely that an intermediate implementation or validation step
passed. Riverview/CME independently validates evidence and owns authoritative
workflow progression; returning this disposition never changes PostgreSQL or
roadmap state by itself.

Use review, blocked, and decision dispositions only at their genuine external
boundaries. Use failure dispositions for failures; never disguise them as
completion.

When executable internal work remains, emit `CONTINUE` and keep working. Do not
return a progress report merely because a model turn ended. Preserve hard
limits, cancellation, guardrails, provider failures, context exhaustion, and
other safety/resource boundaries. Never encode remaining work only in prose and
do not use phrase matching to decide state. Hermes enforces the structured
contract and CME reconciles it.
