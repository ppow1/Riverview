<!-- Version: 1.1.0 | Date: 2026-10-02 | Status: CAPTURED -->
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

A second recurring failure mode is now explicitly in scope: **unnecessary rediscovery of established facts and premature interruption of execution**. An agent may already possess sufficient evidence and authority to continue, yet reopen a settled question, request evidence again, or hand an unnecessary intermediate decision back to the Steward. This increases conversational turns, consumes Steward attention, introduces context drift, and can make a 20-step engineering workflow behave like a 130-handoff workflow.

A concrete example occurred with a Raspberry Pi 4 compute carrier board. The Steward supplied front/back photographs specifically so the board model could be identified. After the identification had been established, the assistant repeatedly reopened the identity question and requested additional photographs—approximately five requests across the work—rather than treating the established identification as a working fact. Some rechecking could have been justified by image quality, but repeated re-investigation after the fact was established was not additional rigor; it was failure to preserve and reuse state.

The Steward has already responded to this class of behavior architecturally by creating known-facts / proven-facts areas in projects. Those areas are intended not merely as historical documentation but as authoritative working state that prevents settled questions from being researched repeatedly.

The Steward should not have to remember to append a special reliability prompt to every project or every agentic task. If these requirements are general, Riverview should investigate making them system properties.

## The actual general-purpose guardrails

### Guardrail A — Completion verification

> **Before you tell me a task is complete, ready, safe to leave unattended, or that I can move on, independently verify the actual end state against what I originally asked for. Do not treat a successful command, process start, or intermediate step as proof of completion. Define the observable success criteria from my requested outcome, check every criterion using evidence independent of the action that was supposed to create it, and tell me explicitly what is verified, what is not verified, and what remains. If you cannot verify the requested end state, do not tell me it is complete or safe to move on.**

Compact form:

> **Do not declare success from execution evidence alone. Recover the original objective, derive its acceptance criteria, independently observe the resulting state, and declare mission success only when every required criterion is proven.**

### Guardrail B — Established-fact reuse / anti-rediscovery

> **Do not re-investigate an established fact merely because you need that fact for a new action. Retrieve and reuse the authoritative established fact. Reopen it only when new evidence contradicts it, the stored fact is explicitly uncertain, or the new task requires a level of certainty the existing evidence does not support. If you reopen an established fact, state what new evidence or requirement caused you to reopen it.**

This means known/proven facts are not merely documentation. They are **constraints on future investigation**.

Default information path should therefore be:

```text
Need information
    -> check authoritative PROVEN / KNOWN FACTS
    -> check current project state
    -> check prior decisions and retained evidence
    -> reuse established state when sufficient
    -> research / reacquire evidence only for an actual unresolved gap
```

Research itself should have an admission criterion. Uncertainty should not automatically authorize rediscovery when the project already contains an authoritative answer.

### Guardrail C — Continue when sufficiently grounded

> **Do not stop and return work to the Steward merely because another intermediate step exists. If the objective, authority, established facts, and next bounded actions are already sufficient, continue toward the requested outcome. Interrupt the Steward only for an actual decision, required physical intervention, destructive or authority-expanding action, material ambiguity, contradictory evidence, or failure that cannot be resolved within granted scope.**

This guards against the opposite of premature completion: **premature interruption**.

### Guardrail D — Bounded authority

> **You're allowed to do A, B, C — but nothing else. And if you hit a wall, report it. Don't guess. Don't improvise. Don't try to fix it without a Steward.**

These concerns are complementary:

- bounded authority controls **what an agent may do**;
- established-fact reuse controls **what an agent should not unnecessarily rediscover**;
- objective continuity controls **whether an agent should continue or interrupt**;
- mission assurance controls **what an agent may claim has been accomplished**.

## Architectural question

Should these responsibilities live inside every worker/agent prompt, or should Riverview provide an independent event-driven supervisory function — informally, a **floor walker** — that retains mission intent, established facts, authority boundaries, and acceptance criteria and challenges both unsupported completion and unnecessary interruption/research?

The floor-walker analogy is intentional: in a call center, a floor walker does not perform every worker's task. It maintains situational awareness, catches drift, reinforces operating rules, and intervenes when a worker's local activity no longer satisfies the larger operational objective.

Candidate conceptual flow:

```text
STEWARD INTENT
    -> mission objective
    -> authoritative established facts
    -> explicit acceptance criteria
    -> bounded worker actions
    -> action results
    -> independent observation / evidence
    -> mission-assurance comparison
        -> CONTINUE WITHOUT STEWARD INTERRUPTION
        -> RESEARCH JUSTIFIED BY IDENTIFIED GAP
        -> PASS
        -> EXCEPTION / STEWARD CHECKPOINT
```

A successful subordinate command is **action success**, not necessarily **mission success**. Likewise, encountering a new subordinate step is **not automatically a reason to stop**.

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
11. Treat PROVEN FACTS / KNOWN FACTS as authoritative operational state, not passive documentation.
12. Prevent repeated research or repeated requests for photographs, logs, identification evidence, configuration details, or other inputs that have already been established sufficiently for the current task.
13. Require a stated trigger for reopening an established fact: contradictory evidence, explicit uncertainty, or a genuinely higher certainty requirement.
14. Detect unnecessary Steward handoffs when the worker already has sufficient objective, authority, facts, and evidence to continue.
15. Distinguish healthy verification from repetitive re-investigation.
16. Favor execution diligence after discovery is complete: retrieve established state, plan farther ahead, execute multiple bounded steps, and verify the resulting end state.
17. Measure or at least expose conversational/operational handoff inflation: workflows should not expand from a reasonable multi-step implementation into many more Steward-agent turns merely because the worker repeatedly requalifies settled state.

## Relationship to existing Riverview mechanisms

This idea must **not** begin with the assumption that Riverview needs another agent.

`AI_HINTS.md` already points to the Hermes Objective Continuity Contract and `riverview-objective-continuity` skill for premature stop, turn-complete versus objective-complete, `CONTINUE`, and CME semantics. Riverview also already has Charter anchoring, acceptance evidence, Steward authority, Grace coordination, roadmap state, diagnostics-first obligations, event-oriented architecture, and project-level known/proven-facts mechanisms.

Therefore the first elaboration questions are:

> **Does Riverview's existing Objective Continuity machinery already intend to enforce these mission-assurance guardrails? If so, what gap allows a worker to declare the Steward's objective complete or safe-to-leave based only on successful subordinate action?**

and:

> **What mechanism makes an established fact authoritative enough that workers consume it instead of repeatedly reopening it, while still permitting deliberate requalification when genuinely new evidence or certainty requirements arise?**

and:

> **Can Objective Continuity distinguish a legitimate Steward checkpoint from an unnecessary interruption where the worker already possesses enough information and authority to continue?**

Do not create duplicate governance merely because the floor-walker metaphor is useful.

## Why it is parked now

The immediate OctoMiner/model-download failure can be recovered operationally without redesigning Riverview. The carrier-board rediscovery example and similar repeated-research behavior show that the architectural lesson is broader than that single incident. It should survive the incidents, but implementing a supervisory layer in the middle of unrelated active work would create scope drift.

## Promotion condition

Promote for elaboration when any of the following occurs:

- the Steward explicitly requests design of cross-agent mission assurance;
- another incident demonstrates action-success being mistaken for objective-success;
- another established fact is unnecessarily reopened or reacquired despite authoritative retained evidence;
- repeated Steward handoffs materially inflate a workflow that could proceed autonomously within existing authority;
- Objective Continuity / Grace / Hermes work reaches a point where completion authority or continuation authority is being formalized;
- unattended autonomous work becomes sufficiently common that unsupported all-clear claims represent a material operational risk;
- Riverview's event architecture is being extended with supervisory or acceptance-gate consumers.

## Questions for elaboration

- What component is authoritative for the original mission objective?
- What artifact or service is authoritative for established facts?
- What confidence/provenance metadata should a fact carry?
- What events legitimately invalidate or reopen an established fact?
- Who owns acceptance-criteria creation, and when are those criteria frozen or amended?
- Can the same worker that performed an action certify its completion, or must some classes of claims require independent evidence/observer?
- Which events should trigger mission-assurance evaluation?
- Should `SAFE_TO_LEAVE` be a first-class state distinct from ordinary task completion?
- Should `RESEARCH_REQUIRED` require an explicit unresolved-information justification when an applicable proven fact exists?
- Should `STEWARD_CHECKPOINT` require a reason showing why existing authority/evidence is insufficient to continue?
- How should long-running/unattended work prove that all requested stages are actually queued and have continuation/failure behavior?
- How does the mechanism preserve Steward authority without turning ordinary work into approval-heavy bureaucracy?
- Can the existing Objective Continuity machinery absorb this cleanly?
- If an independent floor walker exists, is it an agent, deterministic state machine, event consumer, policy gate, or hybrid?
- How are false PASS claims, unnecessary rediscovery, and unnecessary interruptions recorded so Riverview can learn from them without relying on conversation memory?

## Desired outcome if eventually promoted

The Steward should be able to give a normal outcome-oriented instruction without remembering a special reliability incantation for every project. Riverview should retain the requested outcome, consume established facts instead of repeatedly rediscovering them, keep workers bounded, allow workers to continue through already-authorized intermediate steps, and refuse to convert partial or intermediate success into a mission-level all-clear without evidence.

The desired operating principle is:

> **Remember what has already been proven, do not research it again without cause, keep moving while authority and evidence are sufficient, and do not claim completion until the requested end state is independently verified.**
