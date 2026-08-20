<!-- Version: 1.0.0 | Date: 2026-08-20 | Status: Active operating mechanism -->
# Riverview Parking Lot and Ready Bench

## Purpose

Riverview needs two distinct places for valuable work that is not on the current execution path.

The **Parking Lot** preserves worthwhile ideas without committing Riverview to implement them.

The **Ready Bench** preserves work that the Steward has explicitly committed to doing, has been sufficiently elaborated into executable form, but is not currently active because capacity, dependencies, hardware, Operator bandwidth, or another blocking condition prevents execution.

These mechanisms exist to prevent scope creep without losing valuable thinking.

## State Model

`Idea -> Parking Lot -> Steward promotion for elaboration -> design/specification -> Ready Bench -> Active Work -> Complete`

The transition from Parking Lot to Ready Bench is not automatic.

## Parking Lot

Meaning: **preserved possibility**.

Use the Parking Lot when an idea is valuable enough to retain but Riverview has not committed to implementing it.

A Parking Lot item may later be promoted, revised, combined with another idea, reconsidered, or closed.

Parking an idea does not authorize implementation.

### Parking Lot entry requirements

Each entry records at minimum:

- ID
- Idea/title
- Category
- Priority
- Originator
- Date captured
- Status
- Why it is worth preserving
- Why it is parked now
- Promotion condition
- Explicit non-action
- Related evidence or current work, when applicable

Nontrivial ideas should receive a dedicated file under `docs/operations/parking_lot/` in addition to the board row.

### Parking Lot statuses

- `CAPTURED`
- `CLARIFY_LATER`
- `RECONSIDER`
- `PROMOTED_FOR_ELABORATION`
- `CLOSED`

## Elaboration / Design

Promotion from the Parking Lot first means the Steward has said, in substance:

> This is worth doing. Discuss it with me and turn it into executable work.

During elaboration, the idea is converted into a bounded specification and execution plan. It is not yet on the Ready Bench merely because the Steward likes the idea.

## Ready Bench

Meaning: **accepted future intent**.

A Ready Bench item is work Riverview intends to execute. The design question is sufficiently settled that available engineering capacity should not need to rediscover what is being built.

The Ready Bench is not the active-work board. An item can remain on the Ready Bench while no worker is currently assigned to it.

### Promotion criteria for Ready Bench

An item may enter the Ready Bench only after all applicable criteria are met:

1. The Steward has explicitly confirmed that Riverview intends to implement it.
2. The idea has been discussed/elaborated enough to establish the intended outcome and boundaries.
3. A durable specification exists.
4. A roadmap or execution sequence exists.
5. The work packages or equivalent bounded implementation packages are defined sufficiently for execution.
6. Dependencies and ordering are identified.
7. Acceptance criteria are identified.
8. Prohibited scope or major boundaries are identified.
9. Known blockers/resource requirements are recorded.
10. The work can be resumed later without reconstructing its intent from conversation history.

### Ready Bench blockers

Ready Bench does **not** mean immediately executable. Examples of legitimate blocking conditions include:

- waiting for hardware or parts;
- insufficient disk/storage capacity;
- prerequisite software not complete;
- another roadmap dependency not accepted;
- unavailable provider/model capacity;
- unavailable engineering capacity;
- Operator/Steward bandwidth required at frequent interruption points;
- Grace/autonomous engineering capability not sufficiently reliable yet;
- an explicit external dependency.

### Ready Bench statuses

- `READY`
- `WAITING_DEPENDENCY`
- `WAITING_HARDWARE`
- `WAITING_RESOURCE`
- `WAITING_OPERATOR_CAPACITY`
- `WAITING_ENGINEERING_CAPACITY`
- `BLOCKED`
- `PULLED_TO_ACTIVE_WORK`
- `CLOSED`

## Grace / autonomous engineering use

The Ready Bench is intended to become a durable source of already-designed work that Grace can consume when autonomous engineering is functioning correctly.

The intended future interaction is approximately:

> Grace, work the Ready Bench while I am away. Progress any dependency-ready items within your authority and stop only at genuine Steward checkpoints or exceptions.

Grace must still follow the Charter, authoritative roadmap state, engineering contract, dependencies, acceptance requirements, diagnostics-first/Cookbook obligations, and bounded authority. Presence on the Ready Bench does not grant permission to ignore those controls.

## Parking Lot vs Ready Bench

| Question | Parking Lot | Ready Bench |
|---|---|---|
| Is the idea worth preserving? | Yes | Yes |
| Has Riverview committed to doing it? | Not necessarily | Yes |
| Has the Steward explicitly endorsed implementation intent? | Not required | Required |
| Is the design/specification complete enough to resume without rediscovery? | Not required | Required |
| Are roadmap/work packages sufficiently defined? | Not required | Required |
| Can it be closed without ever being implemented? | Yes | Only by an explicit later decision |
| Is it active work right now? | No | Not necessarily |
| May Grace eventually pull it when capacity exists? | No, not merely because it is parked | Yes, subject to dependencies/authority/readiness |

## Authority

The Steward controls the commitment transition.

Workers may capture ideas in the Parking Lot when appropriate, but they may not promote an item to the Ready Bench merely because they believe it is valuable.

Steward approval to elaborate an idea is distinct from Steward confirmation that the resulting specification belongs on the Ready Bench.

## Non-goal

This mechanism must not become a second roadmap, a second operational database, or a replacement for authoritative PostgreSQL execution state.

Parking Lot and Ready Bench documents preserve intent and resumable planning. Active execution continues to follow the Riverview roadmap, engineering contract, and authoritative operational state.