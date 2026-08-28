# Riverview Closed-Loop Archaeology and Reuse Map

Date: 2026-08-28
Status: Phase 1 scaffolded-autonomy foundation; no full loop implementation yet

## Authority boundary

Riverview PostgreSQL, River events, CME, Comms5, Campaign Runner, resource
policy, Activity Projection, resident HOME, and Steward notification remain
authoritative. Hermes, Codex, local workers, and ChatGPT are replaceable
execution/reasoning adapters. Conversation text and GitHub are evidence and
mirror surfaces, not queue authority.

## Estate predecessor mapping

| Estate component | Riverview equivalent | Decision |
|---|---|---|
| `grace_consultation_loop.py` | Grace HOME + future Riverview consultation adapter | ADAPT; preserve Grace-originated lineage and continuation semantics |
| `autonomous_chatgpt_mailbox_worker.py` | No current Riverview equivalent | MISSING; add one bounded worker adapter only after state contract is defined |
| `ConsultationStore` | PostgreSQL/River/Comms8-compatible durable lineage | ADAPT; do not create Hermes-local authority |
| `autonomous_reason_execute_loop.py` | Resident HOME reasoner + Campaign Runner execution boundary | ADAPT; map decisions, do not grant ChatGPT authority |
| `consultation_escalation.py` | Steward attention + bounded consultation escalation | ADAPT; preserve `STEWARD_DECISION_REQUIRED` and evidence limits |
| `AI_COMMUNICATION_HINTS.md` | `AI_HINTS.md` plus this operations contract | ADAPT; concise recovery pointers only |
| `Engineering_Communication_and_Escalation_Standard_v1.md` | Riverview Engineering Interaction Contract | ADAPT; preserve authority/evidence/acceptance distinctions |
| Estate Comms8 consultation/mailbox lifecycle | Riverview Comms5/River plus future consultation tables/events | PARTIAL; transport and durable namespace must be reconciled before implementation |
| Estate local worker state JSON | Riverview runtime status/Activity projection | SUPERSEDED as authority; local state may be restart evidence only |
| Estate GitHub projection | Riverview GitHub mirror | MISSING; local-first mailbox must remain authoritative |

## Required Riverview loop objects

The next bounded implementation should define, not yet broadly execute:

- root autonomous task;
- roadmap and checkpoint;
- local request/result artifact references;
- Hermes run and execution adapter;
- result/evidence and validation;
- consultation request/result;
- continuation relation;
- Steward steerage event;
- terminal outcome/run boundary;
- mirror state;
- monitor projection.

Every object needs stable identity, correlation, idempotency, lifecycle state,
classification, timestamps, provenance, and explicit authority boundaries.

## Reuse rules

1. Use existing River events and Activity Projection for chronology.
2. Use Comms5/Campaign Runner for governed engineering formation and execution.
3. Use ResourceRegistry/Planner/PolicyStore for adapter/resource choice.
4. Use existing notification and WindowsPresenter paths for milestones and
   Steward boundaries.
5. Use local artifacts as reconstructable evidence, never as concurrency
   authority.
6. Use GitHub only as mirror/audit/recovery visibility.
7. Keep ChatGPT consultation structured and bounded; its result is advisory.
8. Make scaffolded/assisted/mature autonomy policy variations over one schema.
9. Keep run boundary, semantic task outcome, milestone, notification policy,
   and automatic continuation independent.
10. Do not begin the full Now board, fabrication pipeline, or autonomous loop
    breadth until the smallest root-task vertical slice is proven.

## Current blockers and deferred work

- Hermes real interactive post-render acceptance is blocked by a provider/CLI
  turn that hung for more than fourteen minutes and did not unwind through the
  normal interrupt path.
- Grace same-object supervision remains an occupational acceptance gap.
- Bambu/P2S remains user-reported and not authoritative in Riverview.
- Jessica final live acceptance remains incomplete.
- The full loop state schema and local mailbox adapter are the next bounded
  implementation slice; no code for them is introduced by this map.
