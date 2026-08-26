# PL-0008 — Riverview Web Operator UI Stabilization and Re-architecture

Status: CAPTURED
Classification: Riverview Internal
Category: Web / Operator Reliability / Architecture
Priority: High
Originator: Steward
Date Captured: 2026-08-26

## Problem statement

The current Riverview website has recurring systemic reliability classes:

- inconsistent database rehydration;
- unpredictable page/state loading;
- stale or uncertain activity-log freshness;
- unreliable refresh behavior;
- tab switching that inconsistently loses or restores state;
- conversations that inconsistently restart or rehydrate;
- settings changes that regress unrelated capabilities;
- isolated repairs that cause other capabilities to disappear.

## Future package direction

Treat this as a system-level stabilization and re-architecture package, not
another isolated UI patch. Before implementation, inventory existing behavior,
establish regression/acceptance coverage for capabilities that must survive,
identify state ownership and rehydration, polling/event/streaming duties,
failure/reconnect semantics, tab/session persistence, and preservation of useful
Office/legacy behavior.

A future candidate may use Hermes as a bounded execution substrate through
Campaign Runner. Riverview remains authoritative for state, identity, authority,
privacy, lifecycle, and acceptance.

## Boundaries

No website inspection, redesign, repair, or replacement is authorized by this
parking item. It must not be used to remove existing capability merely because
it is difficult to rehydrate.

## Promotion condition

Promote after a durable inventory and committed regression/acceptance basis are
approved by the Steward.

## Unified Resource & Work Command Center requirement

The future stabilized operator surface must provide a reliable at-a-glance
execution/resource picture so a returning Steward can understand the system in
seconds rather than interpret terminal process IDs or wait-state lines.

It must expose a derived projection over authoritative Riverview state covering
dynamic Codex resources and observed weekly fuel/capacity, freshness, workload,
credential/resource correspondence where proven, local GPU/node health and
telemetry (model, VRAM, utilization, temperature, power, fan/thermal state),
reservation/allocation, loaded model, SSH/WOL/power-management capability, and
future provider resources. It must show Hermes running/waiting/blocked/review-
ready state, current tranche/package, provider/model, context usage, turn/run
budget, active workers/processes, stage, meaningful activity, heartbeat,
blocker, Steward-attention requirement, and notification state. It must show
Campaign Runner objective/package/work-order, role, attempt, repair generation,
candidate and basis, validation/lifecycle state, technical completion versus
institutional acceptance, current worker/resource, and stale/fenced status.
Grace/institutional views should include active contracts, priority, pending
Steward decisions, Engineering waits, validation waits, and acceptance waits.

The exact UI, polling/event model, reconnect behavior, and layout remain future
design work. The implementation must preserve useful legacy Office capability,
use a dependable derived projection rather than a competing source of truth,
and establish regression coverage before replacing fragmented surfaces.
