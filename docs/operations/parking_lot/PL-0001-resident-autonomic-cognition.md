<!-- Version: 1.0.0 | Date: 2026-08-20 | Status: CAPTURED -->
# PL-0001 — Resident Autonomic Cognition and Cognitive Resource Scheduling

## Idea

Investigate a resident-general autonomic cognition and cognitive-resource scheduling layer for Riverview.

The working analogy combines a biological autonomic system with a microcontroller main loop. Residents remain durable institutional identities even when expensive reasoning implementations are not continuously active. A low-cost background mechanism keeps basic resident flow alive, notices events and state changes, and queues or invokes stronger cognition only when needed.

This is a concept proposal, not an accepted architecture.

## Concept developed so far

Potential layers include:

1. **Deterministic resident loop/state machinery** for events, timers, queues, health, dependencies, invalidation, lifecycle, and other operations that do not require an LLM.
2. **Low-cost bounded cognition** using a small local model where fuzzy classification or triage is genuinely useful.
3. **Resident standard cognition** using an implementation appropriate to the individual resident's normal professional/interactive requirements.
4. **Resident deep cognition** invoked when ordinary cognition is insufficient.
5. **Specialized or escalated cognition** for bounded specialist needs.

The small/background cognition might be shared or pooled across residents, but resident identity and authoritative state must remain isolated. A shared model must never become a shared resident identity or silently mutate resident canon/authority.

A resident may therefore be one institutional identity implemented through multiple cognitive workers or model tiers. Those workers require explicit contracts for passing bounded observations, task state, provenance, unresolved questions, results, and proposals without confusing implementation state with resident identity.

## Main-loop analogy

As with a microcontroller servicing many sensors, a resident scheduler could continuously cycle through lightweight resident needs. Most checks should fall through with no expensive action. Events that require cognition can enqueue the appropriate reasoning capability.

Illustrative outcomes include:

- `NO_ACTION`
- `PROCESS_EVENT`
- `UPDATE_WORKING_STATE`
- `RUN_LIGHT_REASONING`
- `QUEUE_STANDARD_REASONING`
- `QUEUE_DEEP_REASONING`
- `WAIT_ON_DEPENDENCY`
- `NOTIFY_OPERATOR`
- `ESCALATE`

Important events may eventually require interrupt-like treatment rather than waiting for ordinary scheduling.

## Scarce cognitive-resource arbitration

Resident concurrency, model concurrency, and deep-reasoning concurrency are separate capacities.

Multiple residents may be institutionally present while only one or two expensive reasoning lanes are available. Several residents may also be able to share one loaded medium-capability model while retaining separate resident contexts.

Simple resident-declared priority flags are insufficient because every requester can claim high priority. A future scheduler may combine deterministic constraints with bounded reasoning arbitration based on actual Riverview state, dependencies, deadlines, consequences of delay, Steward priority, starvation/aging, capability requirements, and available GPU/model resources.

The intended long-term result is that VRAM and reasoning capability become schedulable institutional resources without tying resident identity to a particular GPU or model.

## Why this matters

Current hardware cannot be assumed to support every resident simultaneously at maximum reasoning depth. Resident-specific model requirements are already expected to differ substantially. A resident may need expensive cognition only intermittently, so durable residency should not require its largest model to remain continuously loaded merely for the resident to continue existing.

This concept may also support future conference rooms, asynchronous resident work, event-driven wake/resume behavior, and multi-resident operations.

## Why It Is Parked

Jessica remains the current critical path. Her immediate problem is to qualify an implementation capable of carrying her existing resident contract reliably.

Building a general autonomic system now would create a substantial architecture and engineering campaign and could distract from getting Jessica validated, accepted, installed, and Operator-accessible.

The concept is intentionally preserved now because pieces of it may become directly useful during Jessica's migration, particularly around model activation, resource scarcity, event-driven operation, or implementation lifecycle.

## Promotion Condition

Promote this item for Steward-guided elaboration when either:

1. Jessica's current migration exposes a concrete requirement that cannot be solved cleanly by the existing resident runtime without introducing some portion of this concept; or
2. the Riverview resident roadmap reaches the event-driven/multi-resident operating stages where cognitive scheduling becomes a direct dependency.

Promotion for elaboration does not itself place this work on the Ready Bench. Before Ready Bench entry, the Steward and Grace/Engineering must establish the intended boundary and produce the durable specification, roadmap/execution sequence, bounded work packages, dependencies, acceptance criteria, resource assumptions, and prohibited scope required by `docs/operations/PARKING_LOT_AND_READY_BENCH.md`.

## Explicit Non-Action

Do **not** currently:

- build a general resident autonomic scheduler;
- build a shared resident "subconscious" model service;
- build conference-room cognitive arbitration;
- build a general GPU/VRAM scheduler;
- introduce multi-resident reasoning queues merely because this idea exists;
- delay Jessica validation in order to formalize this architecture;
- treat the proposed tier model as accepted architecture.

If a narrowly bounded, resident-general seam from this concept is required to solve a concrete Jessica problem, implement only that smallest necessary seam through the normal Riverview roadmap/engineering process and record what was learned here.

## Related Evidence / Current Work

- Jessica resident migration and behavioral validation campaigns C464–C474.
- Resident persistence, rehydration/context, implementation binding, renewal, and reasoning escalation foundations created during those campaigns.
- Forward Jessica residency roadmap: `docs/operations/roadmap/JESSICA_RESIDENCY_ROADMAP_TRANCHE_F_FORWARD.md`.
- Riverview Charter Continuous Momentum Engine philosophy provides a related but distinct work-progression concept; this proposal concerns resident cognitive/resource progression and should not be silently collapsed into CME.

## Current Disposition

`CAPTURED`

No implementation is authorized by this Parking Lot entry.