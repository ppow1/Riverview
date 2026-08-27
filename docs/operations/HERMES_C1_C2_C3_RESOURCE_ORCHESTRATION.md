<!-- Version: 1.0.0 | Date: 2026-08-27 | Status: Accepted operational summary -->
# Hermes C1/C2/C3 Codex Resource Orchestration and Grace Visibility

## Purpose

This document is the durable operational summary for how Riverview and Hermes use the three authenticated Codex resource identities C1, C2, and C3; how Riverview selects and binds work to one of those resources; how Hermes preserves the selected authentication all the way into native Codex execution; and how Grace, the Steward, and Operator-facing projections can observe and govern that resource usage.

This is a summary of the accepted C1/C2/C3 implementation published to `ppow1/Riverview:main` in commit `31606a06a6b83e80cf206ed2db2a1b9b8cfa9fca` (`feat(riverview): close C1 C2 C3 Hermes binding lane`). The detailed acceptance evidence remains in:

`docs/operations/roadmap/evidence/C1_C2_C3_HERMES_NATIVE_BINDING_2026-08-27.md`

The authoritative local Riverview root is:

`A:\Riverview\standalone`

Hermes is installed separately at:

`A:\AI\Tools\Hermes\hermes-agent`

## Executive model

C1, C2, and C3 are three distinct authenticated Codex resource identities. Each identity has its own `CODEX_HOME`, its own authentication material, its own safe login fingerprint, and independently observed Codex quota/reset telemetry.

The accepted mappings are:

| Resource | `CODEX_HOME` | Safe fingerprint |
|---|---|---|
| C1 | `A:\AI\CodexProfiles\C1` | `000f32ae28fba7b8` |
| C2 | `A:\AI\CodexProfiles\C2` | `20521e97b56e0445` |
| C3 | `A:\AI\CodexProfiles\C3` | `ac91c17202d67add` |

The fingerprints are deliberately non-secret. Raw email addresses, access tokens, refresh tokens, ID tokens, cookies, passwords, API keys, and provider account identifiers are not part of Riverview resource telemetry or execution provenance.

The important invariant is:

`Riverview-selected C1/C2/C3 -> Hermes receives the same resource -> Hermes resolves the matching CODEX_HOME -> native Codex runs under that authentication -> safe fingerprint matches the selected resource`

This was proven live for C1, C2, and C3, and the final production acceptance succeeded through C3 with the exact response `OK`.

## What “multiple jobs through C1/C2/C3” means

Riverview can admit multiple engineering work items and make an independent resource-selection decision for each work item. A work item may be explicitly pinned to C1/C2/C3 or may ask the durable resource planner to choose an eligible Codex resource automatically.

The current production path is:

`Steward / Grace governed intent`

`-> objective / stage / authority`

`-> EngineeringIntent`

`-> Relay work order`

`-> RestrictedRunner`

`-> DurableResourcePlanner`

`-> C1/C2/C3 selection and current lease/binding record`

`-> HermesCampaignRoleExecutor`

`-> HermesReasoningProvider`

`-> authenticated Hermes HTTP`

`-> Hermes strict C1/C2/C3 resolver`

`-> CodexAppServerSession`

`-> native Codex app-server under the selected CODEX_HOME`

Each work item carries its selected resource identity forward. An explicit resource request remains pinned; an automatic request is selected by policy from current telemetry.

### Current concurrency caveat

The current implementation uses `SeatClaimStore` and a database uniqueness/lease mechanism around C1/C2/C3 while a production execution is active. This means the present scheduler behaves conservatively and can temporarily treat a selected resource as unavailable to another planner while an active claim is present.

That conservative exclusivity is **not** intended to be the final conceptual model of the Codex accounts. The Steward has explicitly clarified that C1/C2/C3 are authenticated resource/token pools and that multiple Hermes executions may ultimately be allowed to share one login when the provider/runtime supports it safely. The future correction is parked as:

`PL-0013 — Codex Resource Binding and Reset-First Capacity Policy`

Until PL-0013 is elaborated and implemented, document the current behavior honestly: Riverview supports multiple jobs across the C1/C2/C3 fleet, while the accepted production scheduler currently fences active use with claim/lease semantics.

## Telemetry: what Riverview knows about C1/C2/C3

Riverview does not infer account state from labels. It consumes the Estate Codex telemetry artifact:

`A:\theestate\runtime\engineering_capacity\codex_seat_telemetry.json`

`ResourceRegistry.from_codex_telemetry()` projects each C1/C2/C3 record into an `ExecutionResource` containing the data needed for selection and reporting, including:

- resource/seat identity;
- availability and health;
- observation timestamp and freshness;
- observed remaining capacity;
- reset/rollover timestamp;
- all retained native quota windows;
- safe identity fingerprint;
- optional current execution state;
- observed refill evidence;
- provider-reported reset-credit count and metadata when available.

The telemetry producer remains read-only with respect to provider authentication and quotas.

### Native quota windows and reset times

Riverview preserves the independent native Codex windows rather than collapsing them into one percentage. The accepted implementation has observed a short primary window and a longer secondary/weekly window, each with its own reset time.

Reset timestamps are useful for planning, but an advertised reset time is not treated as proof that a refill actually occurred. `reset_refill_observed()` uses a material upward change in observed capacity as evidence of refill.

### Reset credits

Provider-reported reset credits are retained as **read-only telemetry**. During acceptance the system observed one available reset credit for each of C1, C2, and C3. Reset-credit consumption is not an ordinary scheduling operation and was not used during acceptance.

The exact provider ownership scope, eligibility rules, and restoration semantics of those credits remain separately governed. A scheduler or Grace must not consume a reset credit merely because one is visible.

## Resource policy and scheduling modes

The authoritative resource policy is stored durably in PostgreSQL in the `resource_policy` aggregate with policy ID:

`codex-fleet`

The policy is revisioned and audited. The accepted live policy at final C1/C2/C3 acceptance was:

- policy ID: `codex-fleet`
- revision: `7`
- mode: `HIGHEST_CAPACITY`
- Steward lock: `false`

Supported policy modes are:

| Mode | Intended behavior |
|---|---|
| `HIGHEST_CAPACITY` | Prefer the eligible resource with the most observed remaining capacity. |
| `BALANCED` | Uses the current capacity/workload ordering to favor the strongest available candidate; retained as a named strategic mode. |
| `ROUND_ROBIN` | Rotate deterministically across eligible C1/C2/C3 resources using the durable round-robin cursor in production planning. |
| `DRAIN` | Prefer a specified target resource so it can intentionally be spent down. |
| `PRESERVE` | Avoid a specified target resource when another eligible resource exists. |
| `SOONEST_ROLLOVER` | Prefer the eligible resource whose observed quota window resets soonest. |
| `MAXIMIZE_RUNWAY` | Prefer the resource with the strongest minimum remaining capacity across its observed quota windows. |
| `PRIORITY` | Follow an explicit configured C1/C2/C3 priority order. |

Eligibility is evaluated before strategic ranking. Resources that are unhealthy, unavailable, stale, role-incompatible, explicitly excluded, or currently represented as busy/running/claimed/starting are not eligible for selection under the current scheduler.

### Why reset timing matters

The three authenticated resources do not necessarily roll over at the same time. A resource can be a day or more ahead of another resource's reset. Consequently, the raw percentage remaining is not enough to maximize usable subscription capacity.

`SOONEST_ROLLOVER` is already implemented, but the Steward wants the future normal/default strategy to go further: prefer capacity that is most at risk of expiring unused, taking both remaining capacity and time-to-reset into account. That work is explicitly parked in PL-0013 and is not yet the current default.

## Explicit selection versus automatic selection

There are two supported ways to choose C1/C2/C3.

### Explicit selection

A caller can request C1, C2, or C3 explicitly. Riverview validates the resource ID and sends it to Hermes as request-scoped `codex_seat_id` metadata. Hermes resolves the selected resource again and fails closed if the selected home is missing, unusable, or inconsistent with caller-supplied state.

An explicit selection cannot silently fall back to:

- another C1/C2/C3 identity;
- Hermes' global/default credential pool;
- the default Codex home;
- an unqualified Codex credential.

### Automatic selection

When a work item asks for a Codex resource rather than naming C1/C2/C3, `DurableResourcePlanner` reads the current durable policy and the current `ResourceRegistry` telemetry, selects an eligible resource, creates durable decision provenance, and binds that selection to the work execution.

A planner decision records, among other things:

- policy ID/revision/mode;
- candidate state;
- ranking;
- claim/binding attempts;
- selected resource;
- selected safe fingerprint;
- execution correlation;
- fallback/race information;
- human-readable selection reason.

This makes automatic resource choice explainable after the fact.

## How Hermes preserves the selected authentication

Riverview's `HermesReasoningProvider` forwards the selected resource as request-scoped `model_options.codex_seat_id`.

Hermes has a strict resolver for C1/C2/C3. The resolver maps the selected ID to the canonical `CODEX_HOME` and verifies that the home and its authentication material exist before starting the child.

The native execution path is:

`Riverview HermesReasoningProvider`

`-> Hermes HTTP API`

`-> Hermes AIAgent`

`-> strict C1/C2/C3 resolver`

`-> CodexAppServerSession(codex_home=...)`

`-> child process with child-only CODEX_HOME`

`-> native Codex app-server`

The Hermes HTTP transport has its own API authentication. That API key answers a different question: “is Riverview allowed to call this Hermes gateway?” It does **not** choose C1/C2/C3. C1/C2/C3 authentication remains controlled by the selected resource and `CODEX_HOME`.

The Runtime Supervisor projects the Hermes API credential into the Relay worker environment from Hermes-owned configuration. The credential value is not placed into work orders, prompts, model options, planner provenance, or ordinary operator output.

## Live acceptance proof

The implementation was accepted at several levels.

### Direct native C1/C2/C3 proof

Each of C1, C2, and C3 completed a real native Codex app-server request using the corresponding home and fingerprint:

- C1 -> `A:\AI\CodexProfiles\C1` -> `000f32ae28fba7b8` -> `OK`
- C2 -> `A:\AI\CodexProfiles\C2` -> `20521e97b56e0445` -> `OK`
- C3 -> `A:\AI\CodexProfiles\C3` -> `ac91c17202d67add` -> `OK`

### Riverview-originated HTTP proof

Riverview originated real requests to Hermes for C1/C2/C3. For every request, the Riverview-selected resource, transmitted `codex_seat_id`, Hermes-resolved resource, exact child home, safe fingerprint, provider, execution mode, and result agreed.

### Final governed production acceptance

The final governed acceptance preserved the original approved EngineeringIntent and authority, recovered from an infrastructure failure through the existing governed successor mechanism, selected C3 under `HIGHEST_CAPACITY` revision 7, and completed native Hermes/Codex execution successfully.

Final accepted evidence included:

- selected resource: C3;
- safe fingerprint: `ac91c17202d67add`;
- Hermes resource identity: `codex:C3`;
- execution mode: `hermes-http`;
- native mechanism: Codex app-server;
- exact result: `OK`;
- terminal successor state: succeeded;
- resource claim released after completion;
- exactly-one initial-work-order invariant preserved.

The final acceptance is `CLOSED / PASSED`.

## Work formation, exactly-once execution, and recovery

C1/C2/C3 selection is part of a larger governed engineering path. A Steward-approved specification and promoted objective are deterministically formed into an `EngineeringIntent`, which creates exactly one **initial** work order.

The implementation enforces one initial work order per EngineeringIntent at the database level. Grace/CME observes an already-enqueued EngineeringIntent and reuses its canonical initial work rather than creating another initial order.

A failed initial execution can still have a legitimate **successor/recovery** order. This does not violate the one-initial-order rule. The accepted recovery path preserves the original failed attempt and exact authority/scope, then creates one idempotent bounded successor when the failure class is eligible.

This matters operationally because Grace can continue governed work without silently duplicating initial executions.

## How Grace sees what is happening

Grace should reason from the same durable state that drives execution rather than from private Hermes console state.

The principal read surfaces are:

1. **Comms5 resource policy status** — `resource_policy_status` returns the authoritative Codex fleet policy and audit metadata.
2. **Objective/work status** — Comms5 objective/seed/CME status operations expose bounded governance and execution state.
3. **Campaign Runner / Operator projection** — `read_campaign_runner_snapshot()` reads current PostgreSQL work orders and projects work-order ID, objective/stage, state, attempt, worker, `seat_id`, provider/model/resource metadata, capacity, repair state, acceptance state, and Steward-attention state.
4. **Planner decision provenance** — `resource_planner_decisions` records why C1/C2/C3 was selected, including policy revision, candidates, ranking, selected fingerprint, and execution correlation.
5. **Resource claim/binding state** — the current implementation records active C1/C2/C3 work bindings/leases and their release/failure/expiry state.
6. **Estate Codex telemetry** — provides the current capacity/reset/fingerprint evidence that the scheduler itself consumes.

The Operator-facing Hermes projection is explicitly secret-safe: fields such as API keys, authorization headers, passwords, client secrets, access/refresh tokens, and credential objects are redacted.

Grace therefore does not need to inspect raw `auth.json` files or Hermes credentials to understand resource use. She can reason from:

- which work is queued/claimed/running/succeeded/failed;
- which C1/C2/C3 resource was selected;
- current policy and revision;
- current quota/reset telemetry;
- planner selection reason;
- work and attempt correlation;
- whether a resource binding is active or released;
- whether a recovery/successor exists;
- whether Steward attention is required.

## How Grace can influence resource utilization

The resource policy is deliberately durable and high-level rather than hidden in YAML or JSON-only runtime configuration.

Comms5 exposes:

- `resource_policy_status` — read the current durable policy;
- `set_resource_policy` — change the durable policy through the governed control surface;
- `set_resource_policy_lock` — Steward lock/unlock of the policy.

Policy changes are revisioned and appended to `resource_policy_audit` with actor, authority, rationale, and source request metadata.

The Steward lock prevents lower-authority changes while active. Only the Steward may change the lock itself.

### Grace authority boundary

The **read/control seam exists**, but the existence of the seam is not itself permission for Grace to mutate policy.

Grace may read the policy and execution state needed to reason about capacity. When a valid Grace authority rule/transport seam authorizes policy mutation, the same durable policy surface is the intended control point. Until that authority is established, mutation remains fail-closed.

This preserves the architectural requirement that Grace can understand the fleet without gaining authority merely because she can observe it.

## Typical operating patterns

### Normal automatic engineering work

1. Governed work reaches Relay/RestrictedRunner.
2. Current C1/C2/C3 telemetry is loaded.
3. Durable policy is read.
4. Ineligible/stale resources are removed.
5. Planner selects an eligible C1/C2/C3 resource.
6. Decision and current binding/lease provenance are persisted.
7. The same resource ID is forwarded to Hermes.
8. Hermes resolves the matching `CODEX_HOME` and runs native Codex.
9. Result and execution evidence are written back.
10. The current binding/lease is released on terminal completion/failure.

### Explicitly drain one account

Use `DRAIN` with a target C1/C2/C3 resource. When that resource is eligible, the planner prefers it. This is useful when the Steward intentionally wants to spend down one subscription/resource before reducing the number of accounts in service.

### Preserve one account

Use `PRESERVE` with a target resource. The planner avoids that resource when an alternative is eligible.

### Rotate evenly

Use `ROUND_ROBIN` to rotate through eligible resources using the durable cursor.

### Favor the next rollover

Use `SOONEST_ROLLOVER` when the explicit objective is to spend capacity from the resource whose observed quota window rolls over first.

### Protect maximum runway

Use `MAXIMIZE_RUNWAY` when the objective is to choose the resource with the strongest minimum remaining capacity across observed windows.

### Manual priority

Use `PRIORITY` with an ordered list when the Steward wants an explicit resource preference independent of the ordinary capacity policy.

## Failure behavior

The system is intentionally fail-closed at the resource/authentication boundary.

Examples:

- unknown C1/C2/C3 ID -> rejected;
- selected home missing/unusable -> rejected before Codex child creation;
- explicit selected resource mismatch -> rejected;
- stale/unhealthy/unavailable telemetry -> resource excluded;
- active claim conflict under the current scheduler -> planner re-evaluates remaining eligible resources;
- Hermes API authentication failure -> terminal execution failure, not credential fallback;
- provider/runtime failure -> existing work/recovery semantics preserve lineage and cleanup;
- duplicate initial work -> database and Grace/CME exactly-once protections prevent a second admissible initial order;
- expired resource lease -> application-level stale lease recovery is available.

No resource error is allowed to silently substitute another authentication identity when a work item explicitly requested C1/C2/C3.

## Security and privacy boundaries

The implementation deliberately separates three kinds of identity:

1. **Steward / governance authority** — determines who may approve or change governed work/policy.
2. **Hermes transport authentication** — allows Riverview to call the Hermes gateway.
3. **C1/C2/C3 provider authentication** — determines which Codex subscription/login actually performs the model execution.

They are not interchangeable.

Safe resource fingerprints are sufficient for operational correspondence. Raw provider identity and credential material must not be included in Command Center output, ordinary logs, work orders, evidence reports, or prompts.

## Current limitations and parked follow-up

The C1/C2/C3 acceptance is passed, but several items remain intentionally separate:

- The current execution result schema does not durably surface `CODEX_HOME` on every legacy execution path even though live acceptance proved it at the runtime boundary.
- The legacy campaign execution-envelope/result join is incomplete for this path.
- Comms5 resource-policy discovery still has an open `parameters` object requiring separate schema cleanup.
- PostgreSQL startup/churn stability may warrant additional hardening even though bounded connection retry supported final acceptance.
- The current active-resource claim abstraction is more exclusive than the Steward's intended long-term resource-pool model.
- The desired reset-first / expiring-capacity-first **default** is not yet implemented.

The final two resource-model items are preserved in:

`docs/operations/parking_lot/PL-0013-codex-resource-binding-and-reset-first-capacity-policy.md`

Parking does not authorize implementation.

## Operational references

For detailed evidence and code-level archaeology, use these sources:

- `docs/operations/roadmap/evidence/C1_C2_C3_HERMES_NATIVE_BINDING_2026-08-27.md`
- `src/riverview/resources/registry.py`
- `src/riverview/resources/control.py`
- `src/riverview/reasoning/hermes.py`
- `src/riverview/campaign/hermes_executor.py`
- `src/riverview/runner.py`
- `src/riverview/mcp/comms5.py`
- `src/riverview/mcp/comms5_server.py`
- `src/riverview/operator/hermes_projection.py`
- `database/migrations/0049_resource_policy_and_seat_claims.sql`
- `database/migrations/0050_resource_decisions_and_round_robin.sql`
- `database/migrations/0051_initial_work_order_reconciliation.sql`
- `database/migrations/0052_one_initial_work_order_per_intent.sql`
- `docs/operations/parking_lot/PL-0013-codex-resource-binding-and-reset-first-capacity-policy.md`

## Fast recovery summary

When a future session needs to understand the C1/C2/C3 system quickly, remember:

- C1/C2/C3 are three distinct authenticated Codex resource identities with separate `CODEX_HOME` values and safe fingerprints.
- Riverview may explicitly select one or automatically select one under a durable policy.
- The selected resource ID is preserved through Hermes and into native Codex app-server execution.
- Telemetry includes capacity, freshness, independent reset windows, safe fingerprint, and read-only reset-credit evidence.
- Policy is PostgreSQL-backed, revisioned, audited, Steward-lockable, and exposed through Comms5.
- Grace can read the same policy/work/planner/resource state used by execution; policy mutation remains authority-gated.
- One initial work order per EngineeringIntent is enforced; bounded successors handle legitimate recovery.
- The final production acceptance selected C3 and returned exactly `OK` through native Codex app-server execution.
- Current resource claims/leases are a conservative execution fence, not the final desired semantic model for shared Codex pools.
- PL-0013 owns the future non-exclusive resource-binding and reset-first-default elaboration.
