<!-- Version: 1.0.0 | Date: 2026-10-02 | Status: CAPTURED -->
# PL-0016 — Mission Assurance Floor Walker and Completion Verification

## Parking Lot metadata

- **ID:** PL-0016
- **Idea/title:** Mission Assurance Floor Walker and Completion Verification
- **Category:** Agent Reliability / Mission Assurance / Event-Driven Supervision / Acceptance Governance
- **Priority:** High
- **Originator:** Steward
- **Date captured:** 2026-10-02
- **Status:** CAPTURED
- **Explicit non-action:** This item preserves the requirement and architectural question. Parking it does not authorize implementation, creation of a new resident/agent, modification of Grace/Hermes, or changes to active Riverview execution.

## Why this is worth preserving

An agent can execute an individual command correctly while still failing the Steward's larger requested outcome. The dangerous failure is not necessarily command failure; it is **mission-completion misclassification**: treating successful execution of the most recent subordinate action as proof that the original objective is complete, safe to leave unattended, or ready to move on.

This was exposed during the OctoMiner BIOS campaign overnight vision-model download work. The Steward requested multiple models be downloaded unattended overnight. One model download was successfully started and later completed, but the assistant represented the overnight setup as ready even though the remaining requested model downloads were not actually queued to continue. The local action succeeded; the mission did not.

The Steward should not have to remember to append a special reliability prompt to every project or every agentic task. If this requirement is general, Riverview should investigate making it a system property.

## The actual general-purpose guardrail

The core guardrail that motivated this Parking Lot item must be preserved explicitly rather than reduced to project-specific download logic:

> **Before you tell me a task is complete, ready, safe to leave unattended, or that I can move on, independently verify the actual end state against what I originally asked for. Do not treat a successful command, process start, or intermediate step as proof of completion. Define the observable success criteria from my requested outcome, check every criterion using evidence independent of the action that was supposed to create it, and tell me explicitly what is verified, what is not verified, and what remains. If you cannot verify the requested end state, do not tell me it is complete or safe to move on.**

A compact expression of the same rule is:

> **Do not declare success from execution evidence alone. Recover the original objective, derive its acceptance criteria, independently observe the resulting state, and declare mission success only when every required criterion is proven.**

Related bounded-authority guardrail language that should remain visible during elaboration:

> **You're allowed to do A, B, C — but nothing else. And if you hit a wall, report it. Don't guess. Don't improvise. Don't try to fix it without a Steward.**

The two concerns are complementary: bounded authority controls **what an agent may do**; mission assurance controls **what an agent may claim has been accomplished**.

## Architectural question

Should this responsibility live inside every worker/agent prompt, or should Riverview provide an independent event-driven supervisory function — informally, a **floor walker** — that retains mission intent and acceptance criteria and challenges or blocks unsupported `PASS`, `COMPLETE`, `SAFE-TO-LEAVE`, or `MOVE-ON` events across agentic work?

The floor-walker analogy is intentional: in a call center, a floor walker does not perform every worker's task. It maintains situational awareness, catches drift, reinforces operating rules, and intervenes when a worker's local activity no longer satisfies the larger operational objective.

Candidate conceptual flow:

```text
STEWARD INTENT
    -> mission objective
    -> explicit acceptance criteria
    -> bounded worker actions
    -> action results
    -> independent observation / evidence
    -> mission-assurance comparison
        -> CONTINUE
        -> PASS
        -> EXCEPTION / STEWARD CHECKPOINT
```

A successful subordinate command is **action success**, not necessarily **mission success**.

## Behaviors worth investigating

A mission-assurance mechanism may need to:

1. Preserve the original Steward-requested outcome separately from the worker's evolving local context.
2. Derive or retain observable acceptance criteria before execution proceeds too far.
3. Distinguish command success, action success, stage success, and mission success.
4. Require independent postcondition evidence rather than accepting the producing action's exit status as sufficient proof.
5. Detect semantic narrowing, where the current action has become a smaller problem than the Steward originally assigned.
6. Detect premature stopping after a locally successful recovery or workaround.
7. Treat unattended-operation claims specially: before telling the Steward they can leave, verify that continuation, sequencing, failure handling, and completion signaling actually exist for the entire unattended interval requested.
8. Surface unverified criteria explicitly instead of converting uncertainty into an all-clear.
9. Preserve bounded authority: detecting a failure does not automatically authorize the supervisor or worker to improvise a repair outside granted scope.
10. Produce evidence that another agent or the Steward can audit after the fact.

## Relationship to existing Riverview mechanisms

This idea must **not** begin with the assumption that Riverview needs another agent.

`AI_HINTS.md` already points to the Hermes Objective Continuity Contract and `riverview-objective-continuity` skill for premature stop, turn-complete versus objective-complete, `CONTINUE`, and CME semantics. Riverview also already has Charter anchoring, acceptance evidence, Steward authority, Grace coordination, roadmap state, diagnostics-first obligations, and event-oriented architecture.

Therefore the first elaboration question is:

> **Does Riverview's existing Objective Continuity machinery already intend to enforce this mission-assurance guardrail? If so, what gap allows a worker to declare the Steward's objective complete or safe-to-leave based only on successful subordinate action? If not, should Objective Continuity be extended, or is an independent floor-walker/event consumer justified?**

Do not create duplicate governance merely because the floor-walker metaphor is useful.

## Why it is parked now

The immediate OctoMiner/model-download failure can be recovered operationally without redesigning Riverview. The architectural lesson is broader and should survive the incident, but implementing a supervisory layer in the middle of unrelated active work would create scope drift.

## Promotion condition

Promote for elaboration when any of the following occurs:

- the Steward explicitly requests design of cross-agent mission assurance;
- another incident demonstrates action-success being mistaken for objective-success;
- Objective Continuity / Grace / Hermes work reaches a point where completion authority is being formalized;
- unattended autonomous work becomes sufficiently common that unsupported all-clear claims represent a material operational risk;
- Riverview's event architecture is being extended with supervisory or acceptance-gate consumers.

## Questions for elaboration

- What component is authoritative for the original mission objective?
- Who owns acceptance-criteria creation, and when are those criteria frozen or amended?
- Can the same worker that performed an action certify its completion, or must some classes of claims require independent evidence/observer?
- Which events should trigger mission-assurance evaluation?
- Should `SAFE_TO_LEAVE` be a first-class state distinct from ordinary task completion?
- How should long-running/unattended work prove that all requested stages are actually queued and have continuation/failure behavior?
- How does the mechanism preserve Steward authority without turning ordinary work into approval-heavy bureaucracy?
- Can the existing Objective Continuity machinery absorb this cleanly?
- If an independent floor walker exists, is it an agent, deterministic state machine, event consumer, policy gate, or hybrid?
- How are false PASS claims recorded so Riverview can learn from them without relying on conversation memory?

## Desired outcome if eventually promoted

The Steward should be able to give a normal outcome-oriented instruction without remembering a special reliability incantation for every project. Riverview should retain the requested outcome, keep workers bounded, and refuse to convert partial or intermediate success into a mission-level all-clear without evidence.
