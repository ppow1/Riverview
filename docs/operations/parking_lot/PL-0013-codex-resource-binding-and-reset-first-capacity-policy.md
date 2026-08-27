<!-- Version: 1.0.0 | Date: 2026-08-27 | Status: CAPTURED -->
# PL-0013 — Codex Resource Binding and Reset-First Capacity Policy

## Parking Lot metadata

- **ID:** PL-0013
- **Idea/title:** Codex Resource Binding and Reset-First Capacity Policy
- **Category:** Resource Scheduling / Hermes / Codex / Capacity Management
- **Priority:** High
- **Originator:** Steward
- **Date captured:** 2026-08-27
- **Status:** CAPTURED
- **Explicit non-action:** This artifact preserves a future correction/elaboration to the C1/C2/C3 resource model and default scheduling policy. It does not authorize changing the currently active C1/C2/C3 production-acceptance incident, changing authentication, consuming reset credits, changing current resource-policy state, altering live claims/reservations, or interrupting the ongoing exactly-once work-order reconciliation.

## Why this is worth preserving

Current C1/C2/C3 work has established three separately authenticated Codex environments with independent observed capacity and reset timing. The resource-management implementation also supports multiple policy modes, including round-robin, drain/deplete, preserve, highest-capacity, soonest-rollover, maximize-runway, and priority-oriented behavior.

A conceptual issue remains in the current resource model: language and implementation centered on a seat "claim" may imply that selecting C1, C2, or C3 makes that login exclusively unavailable to other Hermes executions. That is not the intended operating model.

C1/C2/C3 are authenticated Codex resource identities/token pools. Binding one Hermes execution to C1 should not, by itself, mean that no other Hermes execution may use C1 concurrently. Multiple executions may legitimately share one authenticated login/token pool, subject to provider limits, workload pressure, and any explicitly configured concurrency guard. The scheduling abstraction should therefore distinguish **execution-to-resource binding** from **exclusive reservation**.

A second issue is the desired normal/default consumption strategy. When multiple Codex pools have different reset/rollover times, Riverview should generally avoid leaving usable tokens on the table immediately before a pool resets. A reset-aware policy should prefer capacity that is closest to expiring/refilling when there is no stronger operational reason to choose another pool.

The Steward described this as a policy that should be usable as the normal/default behavior until another configured strategy is intentionally selected.

## Future investigation and design questions

### 1. Binding versus exclusive claim semantics

Determine whether the current `SeatClaimStore`, planner, Command Center, and related terminology enforce or merely imply exclusive ownership of a C1/C2/C3 login.

The future design should distinguish at least:

- **resource binding:** this execution uses C1/C2/C3 authentication;
- **work/execution identity:** which job is currently using the resource;
- **concurrency/load observation:** how many active executions are using the same pool;
- **exclusive reservation:** only when a specific provider/runtime constraint actually requires exclusivity.

Do not assume a login is exclusive merely because an execution is bound to it.

### 2. Concurrent Hermes use of one Codex pool

Verify the real provider/runtime behavior for multiple simultaneous Hermes/Codex executions using the same `CODEX_HOME`.

Investigate:

- safe supported concurrency;
- rate-limit interaction;
- app-server/session isolation;
- authentication-file safety;
- whether any child/runtime state requires serialization;
- how concurrent usage should be represented in telemetry;
- whether per-resource workload counts are sufficient or a bounded concurrency limit is needed.

The objective is to prevent the scheduler from artificially wasting usable capacity while still respecting real technical constraints.

### 3. Reset-first / expiring-capacity-first policy

Add or refine a scheduling mode whose normal objective is to consume the capacity most likely to be lost at the next reset.

Conceptually, selection should consider:

1. eligibility/health/freshness;
2. current observed remaining capacity in each native window;
3. each pool's independently observed reset/rollover timestamp;
4. how much capacity remains relative to time until reset;
5. current load/concurrency;
6. configured preservation/drain/priority overrides;
7. evidence of actual refill versus merely advertised reset time.

The intent is not simply `SOONEST_ROLLOVER`. A pool with an earlier reset but nearly no remaining capacity may be less urgent than a pool with substantial unused capacity that resets shortly afterward. Elaboration should define a defensible expiring-capacity score rather than rely on one timestamp alone.

### 4. Default/configured scheduling strategy

Determine whether Riverview should have an explicit durable default policy such as:

- `RESET_FIRST`;
- `EXPIRING_CAPACITY_FIRST`;
- or another canonical name consistent with existing planner conventions.

The Steward's desired behavior is approximately:

> Use the reset-aware/expiring-capacity policy as the normal setting until there is a reason to select another policy.

The policy should remain configurable through the same high-level durable resource-policy surface available to the Steward and, when properly authorized, Grace. It should not live only in YAML/JSON or require a code change.

### 5. Preserve existing strategy choices

Any new default must preserve the usefulness of existing modes, including current equivalents of:

- highest capacity;
- balanced;
- round robin;
- drain/deplete a selected seat;
- preserve a selected seat;
- soonest rollover;
- maximize runway;
- explicit priority.

Examples of intended use:

- **Reset-first:** normal operation to reduce stranded expiring capacity.
- **Drain/deplete:** intentionally spend down C3 if the Steward expects to stop paying for or stop using that account.
- **Preserve:** keep one account relatively untouched for future work.
- **Round robin/balanced:** distribute usage evenly when desired.
- **Priority:** explicitly favor a configured resource independent of normal reset economics.

### 6. Multiple provider windows

Current telemetry work has observed separate native Codex windows, including a short primary window and a longer secondary/weekly window with independent reset timestamps. Future elaboration should use the windows the provider actually reports and must not invent a monthly window if one is not present in authoritative telemetry.

The policy should define how competing reset windows are combined. For example, a pool may have ample weekly capacity but be close to a short-window limit, or vice versa.

### 7. Reset credits remain separate

Provider-reported reset credits are a separate mechanism from normal rollover-aware scheduling.

This parking item does **not** authorize consuming reset credits. Future work should continue treating reset-credit availability, eligibility, ownership scope, and consumption semantics as separately governed until those semantics are proven and explicitly authorized.

### 8. Grace-facing policy control

The resource policy must remain visible and understandable at a high enough control-plane level for Grace to reason about it when her mutation authority is legitimately enabled.

Future design should support:

- reading the active strategy;
- reading per-seat reset/capacity evidence;
- explaining why a resource was selected;
- proposing a policy change;
- applying a policy change only through established authority/lock semantics;
- honoring Steward locks/overrides.

This does not broaden Grace's current authority.

### 9. Telemetry and Command Center implications

The Resource & Work Command Center should eventually distinguish:

- authenticated resource identity;
- current active execution count/load;
- any true exclusive reservation, if applicable;
- remaining capacity by native window;
- advertised reset timestamps;
- observed refill evidence;
- selected scheduling strategy;
- selection reason/score.

Terminology should avoid telling the operator that a login is "owned" or unavailable when it is merely being used concurrently.

## Candidate acceptance questions for future elaboration

Before implementation, an elaborated specification should answer at minimum:

1. Can multiple Hermes executions safely use one C1/C2/C3 `CODEX_HOME` concurrently?
2. What real constraints, if any, require exclusive reservation?
3. Which current claim semantics should be retained for work ownership and which should be replaced by non-exclusive resource binding/load tracking?
4. How is an expiring-capacity/reset-first score computed across multiple native provider windows?
5. How are rollover timestamps weighted against remaining percentage and active workload?
6. What policy becomes the durable default?
7. How does the Steward change the active policy without editing files?
8. How does Grace read and, when authorized, modify the same durable policy?
9. How do drain, preserve, round-robin, balanced, highest-capacity, and priority modes continue to work?
10. How does the system explain every automatic selection in durable provenance?
11. How are true provider resets distinguished from advertised reset timestamps?
12. How are reset credits kept separate and non-consumable without explicit authority?
13. How are concurrent executions represented in Command Center/operator telemetry?
14. What regression tests prove the scheduler does not strand capacity unnecessarily at rollover?

## Why it is parked now

The current active C1/C2/C3 acceptance is handling a separate exactly-once work-order incident between governed formation and Grace/CME redispatch. Changing the resource-binding model or default scheduler policy during that incident would broaden scope and complicate forensic acceptance.

The concept should be preserved now and elaborated only after the current production acceptance/reconciliation reaches a clean checkpoint.

## Promotion condition

Promote for elaboration when any of the following occurs:

- the current C1/C2/C3 production acceptance and exactly-once incident are closed;
- exclusive seat-claim semantics demonstrably prevent legitimate concurrent use of a Codex pool;
- reset/rollover timing causes measurable stranded capacity;
- the Steward explicitly directs resource-policy/default-scheduler elaboration;
- Grace resource-policy control becomes an active dependency.

Promotion should produce a bounded design covering concurrency semantics, durable policy state, reset-first scoring, migration from current claim terminology/semantics, Command Center projection, Grace/Steward control, regression tests, and rollback/compatibility behavior.

## Explicit non-action

Parking this idea does not authorize implementation. In particular, it does not authorize changing the current active resource policy, removing existing claim tables, allowing unbounded concurrency, consuming provider reset credits, modifying C1/C2/C3 authentication, or interrupting the current production-acceptance incident.