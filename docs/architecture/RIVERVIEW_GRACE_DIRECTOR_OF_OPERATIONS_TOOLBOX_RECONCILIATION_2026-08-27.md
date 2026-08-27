# Grace — Director of Operations Toolbox Reconciliation

Date: 2026-08-27  
Status: FORENSIC AUDIT / STEWARD REVIEW  
Scope: promised vs designed vs built vs resident-available  
No implementation performed in this tranche.

## Executive finding

Riverview explicitly promised Grace an operational-coordinator role, not merely a
resident title. Durable sources describe Grace as the coordinator of progression,
CME-aware state evaluation, capability-aware dispatch, recovery, routing,
engineering-work progression, and Steward exception notification while remaining
below Steward authority.

Substantial supporting machinery exists:

- authoritative PostgreSQL objective/stage/work state;
- River events and CME runtime/status;
- Grace authority rules and momentum evaluation;
- read-only MCP Relay and Comms5 projections;
- typed engineering formation and Relay/Runner execution;
- resource registry, capacity/fuel telemetry, policy, and exclusive claims;
- diagnostics and Cookbook projections;
- resident registry and continuity;
- Operator/vNext and attention projections.

The missing link is not primarily data persistence. The missing link is the
resident cognitive integration. Current HOME Cognition assembles a bounded packet,
performs one Qwen generation, and composes speech. It does not expose a Grace
occupational toolbox, model-selected read capabilities, or a bounded
reason/retrieve/reason continuation.

Consequently most Grace capabilities are:

```text
built in control-plane/operator form
but not connected to Grace's cognitive workspace
```

## Evidence order and scope

Authoritative and durable sources inspected:

- `docs/governance/RIVERVIEW_CHARTER.md`
- `docs/architecture/RIVERVIEW_FOUNDATION.md`
- `docs/operations/RIVERVIEW_EXECUTION_PLAN.md`
- `docs/operations/RIVERVIEW_ENGINEERING_INTERACTION_CONTRACT.md`
- `docs/operations/roadmap/RIVERVIEW_MASTER_ROADMAP.json`
- `docs/operations/GRACE_ENGINEERING_TASK_SUBMISSION_TEMPLATE.md`
- `docs/operations/troubleshooting/checkpoints/RIV-GRC-0004_MOMENTUM_CONTROL.md`
- `docs/operations/troubleshooting/checkpoints/RIV-GRC-0008_RIVER_CME_WAKEUP.md`
- `docs/operations/troubleshooting/checkpoints/RIV-CAP-0001_CAPABILITY_DISPATCH.md`
- `docs/operations/troubleshooting/checkpoints/RIV-MCP-0004_COOKBOOK_READ.md`
- `docs/operations/roadmap/evidence/C1_C2_C3_HERMES_NATIVE_BINDING_2026-08-27.md`
- historical Git commits listed below;
- current migrations and source implementation;
- current live Operator health/projection and managed process state.

Repository/runtime at audit:

- repository: `A:\Riverview\standalone`
- repository HEAD after audit-document commits: `81daa4197d0fc8366158783ddee497add74281a6`
- live service SHA during audit: `42af760954f1eacd30cb69340cc0cfc11d216347`
- branch: `main`
- `origin/main`: `c88be3ffe6720419a55d9e0f4660a88616b70ce3`
- runtime owner: `windows-task:Riverview Runtime Supervisor`
- provider/model: `ollama:qwen3-coder:30b-qwencode-20k`
- HOME service: `HomeCognitionService`
- local resource evidence: `local:RTX4090`

## Durable reconstruction of the Grace promise

### Charter and foundation

`RIVERVIEW_CHARTER.md` establishes:

- Grace coordinates progression but does not replace the River, database, Estate,
  or Steward;
- CME keeps accepted work moving through event-driven, dependency-aware,
  resumable, idempotent, provider-aware progression;
- capabilities are incomplete until their real boundary and failure behavior are
  verified;
- local AI is a first-class reasoning and execution provider;
- PostgreSQL owns operational state and GitHub owns source/history/contracts.

`RIVERVIEW_FOUNDATION.md` assigns the initial kernel:

- objective/workflow state;
- work assignment, ownership, attempts, and leases;
- diagnostics and Cookbook linkage;
- capability/provider registration;
- Grace and CME progression contracts;
- MCP mailbox correlation.

Its operational sentence is explicit: PostgreSQL is durable River memory and Grace
controls progression.

### Engineering Contract

`RIVERVIEW_ENGINEERING_INTERACTION_CONTRACT.md` states that:

- Grace is the operational coordinator;
- Grace may dispatch to Codex CLI, local AI on the 4090/P100, or approved adapters
  according to capability, cost, policy, and capacity;
- local AI can perform analysis as well as execution;
- read-only MCP should retrieve authoritative roadmap state, current position,
  worker state, work-order status, completed reports, open Steward escalations,
  recent diagnostics, and bounded Cookbook knowledge;
- MCP must expose bounded named capabilities rather than general database,
  filesystem, shell, or secret access;
- dashboard/projections must distinguish planned, ready, active, blocked,
  completed, and accepted work;
- data and execution authority remain separate.

### Roadmap and operating template

`RIVERVIEW_EXECUTION_PLAN.md` makes Grace progression and capability-aware worker
routing a Phase 2 objective, followed by local-AI/Codex adapters and a Phase 4
MCP reasoning bridge.

`GRACE_ENGINEERING_TASK_SUBMISSION_TEMPLATE.md` defines the durable operational
sequence:

```text
conversation / engineering intent
 -> stored specification
 -> Steward-reviewable draft
 -> one approval
 -> seed promotion / durable authority
 -> Grace engineering intent
 -> work order
 -> Relay
 -> provider execution
 -> authoritative evidence
 -> reconciliation
```

The template repeatedly describes Grace as the production engineering orchestrator
and requires her to follow the same seed/objective/correlation lineage through
formation, execution, recovery, and completion.

### Historical implementation commits

The following commit history establishes staged implementation intent rather than
an isolated conversational request:

- `34b672f` — Complete RV-005.1 Grace authority contract
- `2bc6436` — Implement RV-008 MCP resource and mailbox tranche
- `2749c03` — Build Riverview autonomous Grace Codex execution loop
- `e6b7285` — Record bounded Grace conversational event lineage
- `ea0e521` — Let Grace redispatch declared engineering stages
- `ce068c7` — Harden Grace continuation checkpoint boundaries
- `2749c03` — add autonomous control plane, capability dispatch, and Grace momentum
- `7fa78a2` — integrate bounded Hermes Campaign Runner
- `31606a0` — close C1/C2/C3 Hermes native binding/resource lane

These commits built the underlying control machinery, but their acceptance was
primarily control-plane, provider, lifecycle, or endpoint acceptance.

## Grace toolbox ledger

Status vocabulary:

- `EXISTS + WIRED`: capability and resident cognitive connection both proven;
- `EXISTS + NOT WIRED`: usable implementation exists but not through Grace HOME;
- `DATA/SERVICE EXISTS + ADAPTER MISSING`: authoritative data exists, bounded
  resident adapter absent;
- `PROMISED/DESIGNED + IMPLEMENTATION MISSING`: durable intent exists but core
  implementation is absent;
- `NEVER PROMISED`: no durable Grace-specific promise found;
- `OBSOLETE/SUPERSEDED`: replaced by a later accepted design;
- `AMBIGUOUS`: evidence is incomplete or conflicting.

| Subsystem/capability | Original Grace intent | Durable evidence | Designed Grace hook/interface | Underlying implementation | Bounded API/adapter/projection | Grace HOME available | Model-selectable | Authority | Status | Missing seam | Recommended recovery |
|---|---|---|---|---|---|---|---|---|---|---|
| Grace identity/authority | Coordinate within bounded authority | Charter; RV-005.1; migration 0009 | `GraceAuthority`; resident gateway | `grace_authority_rules`, `ResidentConversationGateway` | `/api/residents`; Grace state source | YES | NO | READ/ADVISE | EXISTS + WIRED | No complete office package | Retain as package identity/authority anchor |
| CME heartbeat/state | Monitor CME and explain operational state | Charter CME mandate; Engineering Contract §5; migration 0024; RIV-GRC-0008 | CME status/read model | `CMEStatusStore`, `ContinuousMomentumRuntime` | `/api/cme/status`; Comms5 `cme_status`; vNext `cme` | PARTIAL; meaning/status may be preassembled | NO | READ | EXISTS + NOT WIRED | No resident-scoped current-state capability | Add bounded `operations.cme.read` under approved architecture |
| CME event wakeup/progression | Coordinate event-driven progression and anti-stagnation | Charter §6; RIV-GRC-0008; history `4246622` | CME consumer and Grace evaluation | River trigger, CME runtime, cursor/status | `CMEStatusStore`, River events | NO for cognitive use; YES for runtime | NO | READ/ADVISE | EXISTS + NOT WIRED | No reasoning callback/tool result | Expose read projection and continuation result, not raw consumer control |
| Roadmap position | Know current waypoint and dependency-ready work | Charter North Star; Engineering Contract §14; roadmap | Grace progression loop | roadmap JSON, PostgreSQL roadmap ledger, projections | Operator/vNext/activity; partial Comms5 lineage | NO general retrieval | NO | READ/ADVISE | EXISTS + NOT WIRED | No bounded roadmap query in HOME | Add roadmap position read projection |
| Active objectives/projects | Identify what is active | Charter North Star; Phase 1/2 plan; Grace task template | Grace momentum/objective evaluation | `ObjectiveStore`, objective tables | Comms5 `objective_status` requires known ID | NO | NO | READ | DATA/SERVICE EXISTS + ADAPTER MISSING | No bounded list/filter operation | Add active-objective read adapter |
| Ready work | Progress dependency-ready work | Phase 2; `jessica_localization_campaign_execution_spec`; RIV-GRC-0004 | `GraceMomentum.evaluate` | objective stages/readiness | `GraceMomentum.evaluate` | NO | NO | READ/ADVISE | EXISTS + NOT WIRED | Evaluation is direct code, not resident capability | Return bounded readiness records to HOME |
| Blocked/stale work | Detect and route exceptions | Charter CME; RIV-GRC-0004 | checkpoint routing | `grace_checkpoints`, leases, diagnostics | RIV-GRC-0004 procedures; partial Comms5 lineage | NO | NO | READ/ADVISE/ESCALATE | EXISTS + NOT WIRED | No resident checkpoint reader | Add blocked/stale projection with evidence |
| Recent completed work | Explain recent progression | North Star; dashboard requirement | activity/progress view | River events, work-order results | `ActivityProjection`, `read_campaign_runner_snapshot` | NO | NO | READ/ADVISE | EXISTS + NOT WIRED | Operator read is not HOME tool | Add bounded recent-completions read |
| Work orders/attempts/leases | Track work progression and recovery | Foundation; migration 0003; Phase 1 | Relay/Runner/Grace progression | `RelayStore`, `RestrictedRunner`, attempts/leases | `read_campaign_runner_snapshot`, Comms5 lineage | NO | NO | READ/ADVISE | EXISTS + NOT WIRED | No resident projection/continuation | Add role-scoped work-progress result |
| Comms5 ingress | Understand what external AI/ChatGPT submitted | Phase 4; Comms5 contract; commit `6e88719` | mailbox/seed/lineage path | Comms5, mailbox, seed stores | `recent_steward_submissions`, `seed_lineage`, `seed_status` | NO | NO | READ | EXISTS + NOT WIRED | No Grace cognitive client binding | Add read-only Comms5 lineage capability |
| Comms5 lineage | Follow seed/spec/objective/work state | Comms5 docs; Grace template | same-lineage follow-up | `Comms5Service._lineage`, objective/status methods | Comms5 operations | NO | NO | READ | EXISTS + NOT WIRED | Known-ID/API selection unavailable to model | Add bounded lineage query and result grounding |
| Steward attention | Know what requires human action | notification policy; migration 0023/0048; Charter | exception notification | notification store, activity, Presenter | activity and attention paths | NO | NO | READ/ESCALATE | EXISTS + NOT WIRED | No resident attention read capability | Add safe metadata-only attention projection |
| Resource registry | See approved compute/resource availability | Phase 2/3; `C1_C2_C3_HERMES_NATIVE_BINDING` | capability-aware dispatch | `ResourceRegistry`, `ExecutionResource` | `resource_policy_status`, telemetry | PARTIAL references only | NO | READ | EXISTS + NOT WIRED | No Grace selection/read tool | Add capability availability result with freshness |
| C1/C2/C3 fuel/capacity | Make dispatch recommendations from observed fuel | Engineering Contract §10; history `31606a0`, `07a9828` | resource planner/selection | `ResourcePlanner`, `DurableResourcePlanner`, telemetry | Comms5 `resource_policy_status`; resource DB | NO in HOME | NO | READ/ADVISE | EXISTS + NOT WIRED | Planner serves execution, not resident cognition | Add read-only fleet snapshot; keep claims/control separate |
| Resource policy/claims | Respect policy and exclusive ownership | migration 0049/0050; C1/C2/C3 report | policy/claim control | `ResourcePolicyStore`, `SeatClaimStore` | Comms5 resource policy status | NO | NO | READ; mutation Steward-gated | EXISTS + NOT WIRED | No resident advisory view | Project policy/freshness/claims metadata only |
| Model/resource dispatch | Select appropriate local/cloud resource | Execution Contract §10; Phase 2/3 | provider-aware routing | `CapabilityRegistry`, `ResourcePlanner`, binding adapter | capability dispatch and resource planner | NO for Grace decision-making | NO | ADVISE; execute separate | EXISTS + NOT WIRED | Provider selection is infrastructure-only | Expose explainable advisory selection result |
| Engineering formation | Form governed typed proposals | Grace template; RIV-GRC-0004; architecture doc | Grace formation boundary | `EngineeringIntentStore`, Comms5 `form_and_queue_work`, `DirectGraceFormation` | Comms5 and direct Grace route | PARTIAL; route exists, generic HOME selection absent | NO | PROPOSE; execute separately | EXISTS + NOT WIRED | No resident tool request contract | Add proposal-preparation capability only after design approval |
| Validation/revalidation | Request validation/rework and preserve lineage | Grace template; RIV-EXE-0008 | Runner validation lifecycle | `ResultReconciler`, stale-base recovery, Runner | Comms5 revalidation | NO | NO | ADVISE/PROPOSE | EXISTS + NOT WIRED | No resident result/recovery workspace | Add read/recommendation surface; keep transitions governed |
| Diagnostics | Receive stable failure checkpoint | ADR-0002; Charter North Star | diagnostic event path | `DiagnosticStore`, checkpoints | diagnostics and activity | NO | NO | READ/ESCALATE | EXISTS + NOT WIRED | No Grace diagnostic retrieval | Add bounded diagnostic search/read |
| Cookbook | Consult how Riverview works/fails/recoveries | Charter North Star; ADR-0002; migration 0002/0008; cookbook sync | read-only Cookbook Relay | `cookbook_entries`, `cookbook_sync.py`, Comms5/MCP read surfaces | Comms5/MCP Cookbook reads | NO | NO | READ | EXISTS + NOT WIRED | No HOME retrieval adapter | Add classified cookbook search/read capability |
| Resident responsibility | Know office/resident ownership and suitability | migrations 0009/0041; capability-suitability reports | registry/context | gateway, registry, claim grounding | `/api/residents`, context material | PARTIAL | NO | READ | EXISTS + NOT WIRED | No responsibility query during reasoning | Add responsibility/suitability read projection |
| Operator/runtime status | Explain current service state | dashboard/status requirements; vNext docs | Operator projection | Supervisor status, `/health`, vNext | `/api/runtime/status`, `/health`, vNext | NO general HOME use | NO | READ | EXISTS + NOT WIRED | No Grace runtime-read capability | Add bounded status read if approved |
| Spatial/remote compute | Coordinate relevant physical/remote capability | roadmap/parking-lot evidence; explicit future adapters | no settled Grace office hook found | Spatial service, Octominer docs/parking-lot | separate Operator surfaces | NO | NO | AMBIGUOUS / future | PROMISED/DESIGNED + IMPLEMENTATION MISSING or NEVER PROMISED for Grace specifically | No durable resident-specific contract | Keep out of first package until explicit office scope |
| Notifications/audio | Notify Steward on exception/checkpoint | Phase 5; notification adapter; history `7fa78a2` | Presenter/attention path | notification store, WindowsPresenter | `/api`/plugin path | NO resident read; delivery exists | NO | ESCALATE | EXISTS + NOT WIRED | No Grace attention decision integration | Expose attention metadata and retain Presenter boundary |

## What was built versus what Grace can use

### Built and reusable

- durable Grace identity/authority records;
- River event model and PostgreSQL operational state;
- CME runtime, heartbeat, cursor, and state projection;
- objective/stage/work-order/attempt/lease model;
- Grace momentum evaluation;
- Comms5 discovery, read, lineage, and governed write operations;
- MCP Cookbook projections and diagnostic checkpoints;
- resource registry, observed capacity/fuel, durable policy, and exclusive claims;
- typed engineering intent and governed formation;
- Relay/Runner/Codex execution and reconciliation;
- Operator/vNext/activity/runtime projections;
- attention/notification infrastructure;
- resident identity, continuity, context assembly, and HOME Cognition.

### Not connected to Grace cognitive reasoning

- generic current-objective/work retrieval;
- active/ready/blocked/recent work queries;
- Comms5/ChatGPT lineage retrieval;
- Cookbook lookup;
- resource/fuel explanation and advisory selection;
- diagnostic search;
- Steward-attention inspection;
- dynamic operational playbook retrieval;
- model-selected named capability invocation;
- second HOME reasoning pass over a capability result.

## Why Grace acceptance passed without proving occupational competence

The acceptance units and historical checkpoints generally tested one component at
a time:

- Grace authority tables and rules;
- CME heartbeat/event recovery;
- Comms5 transport, schema, and lifecycle operations;
- resource selection and seat claims;
- engineering formation/execution/reconciliation;
- Operator projections;
- bounded resident conversation/HOME metadata.

Those tests prove that the machinery exists and respects local authority rules.
They do not prove that Grace herself can discover, select, invoke, and reason over
the machinery from a novel question.

The acceptance boundary stopped at:

```text
component/API/workflow accepted
```

instead of requiring:

```text
resident asks novel occupational question
 -> resident selects capability
 -> capability returns authoritative result
 -> resident reasons over result
 -> claims/authority validated
```

No durable requirement was found that made this horizontal resident acceptance a
mandatory gate for every Grace-supporting capability. The durable promise was
present, but the acceptance contract was vertically fragmented.

## Context versus capability diagnosis

A. Development context: partially protected. Requirements exist in Charter,
contracts, roadmap, work packages, migrations, Cookbook, and Git history. The
drift cannot be explained solely as a forgotten conversation requirement.

B. Resident runtime context: bounded and partly available. HOME receives identity,
selected state, CME meaning, registry, capability references, and continuity.
Increasing the context window could improve breadth, but it would not create
selection, freshness, authorization, or continuation semantics.

C. Capability access: primary failure. The authoritative capabilities exist but
are not resident-selectable from HOME. They remain control-plane/operator
surfaces.

D. Durable state: mostly present. PostgreSQL, River, Git, documents, Cookbook,
Comms5, and resource stores preserve much of the intended information. The
resident cannot retrieve it through occupational cognition.

Increasing Qwen context length alone would not solve the defect. It might make a
larger static dump available, but it would still be:

- stale or overbroad;
- difficult to authorize per request;
- unable to express tool selection/result lineage;
- unable to distinguish capability from authority;
- unable to prove reason/retrieve/reason behavior;
- likely to leak irrelevant or protected state.

## Recovery sequence

1. Steward reviews and accepts the resident-office-capability architecture
   decision; do not implement it implicitly in speech code.
2. Define one reusable package/broker/typed tool-result contract using the
   existing ContextBundle, capability registry, authority, classification,
   provenance, and Comms5/read-model semantics.
3. Define the minimum read-only projections:
   - Grace current/active/ready/blocked/recent work;
   - Grace CME, Comms5 lineage, Cookbook, attention, resource, and responsibility;
   - Jessica target-resident canon/evidence/proposal status.
4. Implement Grace `operations.current-work.read` as a model-selected, bounded
   vertical slice.
5. Implement Jessica `character.canon.read` as a model-selected, target-bound
   read slice.
6. Add paraphrase/generalization tests, denial/stale/timeout/contradiction
   tests, and model/tool/model provenance.
7. Require resident occupational acceptance for every capability assigned to a
   resident—not just endpoint or component acceptance.
8. Keep proposal, review, publication, execution, Steward attention, and
   acceptance transitions in their existing governed systems.

## Permanent acceptance recommendation for Grace

Adopt the following invariant in the Engineering Interaction Contract, resident
localization acceptance contracts, and capability-specific work-package templates
if the Steward accepts it:

> No Riverview capability is complete when its accepted design requires Grace to
> observe, reason over, advise on, propose through, or otherwise use that
> capability until Grace's own resident cognitive path has been verified using
> the capability on a novel job-related question, with authoritative result,
> provenance, authority, freshness, and failure evidence.

This should be a cross-cutting acceptance invariant, not a Charter expansion.
The Charter can remain concise; the invariant belongs in the Engineering
Interaction Contract and resident/capability work-package acceptance templates.

## Boundary

- Audit/documentation only.
- No resident tool broker implemented.
- No HOME changes.
- No Grace/Jessica character changes.
- No canon publication.
- No authority change.
- No runtime work.
- No additional conversational patching.
