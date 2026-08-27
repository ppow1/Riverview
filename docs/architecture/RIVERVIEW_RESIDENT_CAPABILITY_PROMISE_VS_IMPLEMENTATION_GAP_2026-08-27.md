# Riverview Resident Capability Promise vs Implementation Gap

Date: 2026-08-27  
Status: CROSS-CUTTING FORENSIC RECONCILIATION / STEWARD REVIEW  
Scope: Grace and Jessica occupational competence  
Implementation: none; documentation only

## Executive conclusion

Riverview’s accumulated intent is stronger than the current resident surface.
The durable record did not merely promise title-aware chatbots:

- Grace was made the bounded operational coordinator of progression, CME,
  capability-aware routing, work state, recovery, and Steward exception handling.
- Jessica was made the first resident of a reusable continuity substrate and the
  Chief Character Architect responsible for professional character/continuity
  work, evidence, methods, proposals, review, and later visual-canon recovery.
- Riverview built substantial supporting control-plane machinery for those roles.

The implementation stopped one boundary short:

```text
Riverview capability exists
but resident cognitive integration is absent
```

The current live resident path is:

```text
/api/chat
 -> ResidentConversationGateway
 -> authoritative state/context assembly
 -> one HOME Cognition packet
 -> one Qwen generation
 -> speech validation/composition
 -> persistence
```

It is not:

```text
resident HOME reasoning
 -> model-selected role capability
 -> bounded authoritative retrieval
 -> second reasoning pass
 -> grounded speech
```

## Required summary matrix

| Capability | Promised? | Evidence | Designed? | Built? | Bounded interface exists? | Available to resident? | Model-selectable? | Authority class | Gap | Recovery effort |
|---|---|---|---|---|---|---|---|---|---|---|
| Grace identity/office/authority | YES | Charter; RV-005.1; migration 0009 | YES | YES | YES, gateway/state source | YES for identity | NO | READ/ADVISE | No complete occupational package | Low: package identity reuse |
| Grace CME monitoring | YES | Charter §6; Engineering Contract §5; migrations 0024/0025; RIV-GRC-0008 | YES | YES | YES, `/api/cme/status`, Comms5, vNext | PARTIAL; preassembled only | NO | READ/ADVISE | No resident CME read capability | Medium |
| Grace roadmap position | YES | Charter North Star; Engineering Contract; roadmap | YES | PARTIAL | PARTIAL projections/roadmap state | NO general HOME access | NO | READ/ADVISE | No bounded resident query | Medium |
| Grace active/ready/blocked/recent work | YES | Charter North Star; Phase 1/2; RIV-GRC-0004 | YES | YES underlying state | PARTIAL, known-ID/status/operator snapshot | NO | NO | READ/ADVISE | No resident work projection/tool | Medium/High |
| Grace Comms5/ChatGPT ingress and lineage | YES | Phase 4; Comms5 contract; Grace template; commits `2bc6436`, `6e88719` | YES | YES | YES through Comms5 | NO | NO | READ | No resident Comms5 client | Medium |
| Grace resource/fuel awareness | YES | Engineering Contract §10; C1/C2/C3 history/report; commits `2749c03`, `31606a0` | YES | YES | YES control-plane/resource projections | PARTIAL references only | NO | READ/ADVISE | Planner is infrastructure-only | Medium |
| Grace governed engineering proposal | YES | Grace template; RIV-GRC-0004; engineering architecture | YES | YES | YES Comms5/direct formation | PARTIAL route-specific | NO | PROPOSE; execution separate | No generic HOME proposal capability | High |
| Grace Cookbook/diagnostics | YES | Charter North Star; ADR-0002; migrations 0002/0008; Cookbook sync | YES | YES | YES MCP/Cookbook read | NO | NO | READ | No resident retrieval adapter | Medium |
| Grace Steward attention | YES | Charter/CME notification policy; migration 0023/0048 | YES | YES | YES attention/Presenter | NO | NO | READ/ESCALATE | No resident attention view | Medium |
| Jessica stable identity/office | YES | Jessica roadmap §§3/G/H | YES | YES | YES gateway/route | YES for identity | NO | READ | Identity only | Low |
| Jessica current accepted canon | YES | JCA-028; Tranche B–D; roadmap | YES | YES `CharacterStore.current()` | YES separate workflow route | NO conversationally | NO | READ | No target-bound HOME canon read | Medium |
| Jessica versions/proposals/review/publication | YES | `CharacterDesignerWorkflow`; commits `f9a4f13`, `4c68a2b` | YES | YES | YES `/api/jessica/character-development` | NO conversationally | NO | READ/PROPOSE/REVIEW/PUBLISH separated | Workflow is category B | Medium |
| Jessica evidence/source classification | YES | JCA-001–005; JCA-028; work packages | PARTIAL | PARTIAL source refs/statuses | PARTIAL | NO | NO | READ/ADVISE | No unified evidence reader/taxonomy | High |
| Jessica professional doctrine/methods | YES | Tranche E; WP-JCA-003; JCA-027 | YES | PARTIAL planning/corpus references | NO unified adapter | NO | NO | READ/ADVISE | Corpus not resident-retrievable | High |
| Jessica behavior/relationships/cognition continuity | YES | roadmap §§2, 5.3, Tranche E; WP-JCA-002/003 | YES | PARTIAL continuity primitives | PARTIAL | NO | NO | READ/ADVISE/PROPOSE | No professional corpus retrieval | High |
| Jessica visual canon/character bible | YES as professional recovery target | Tranche E; WP-JCA-003; WP-JCA-024; `54747e6` roadmap | PARTIAL | PARTIAL evidence/planning only | NO complete current projection | NO | NO | READ/PROPOSE; publish governed | No visual-canon authority/corpus/tool surface | High; separate design needed |
| Jessica visual generation/approval | PARTIAL / future | roadmap visual-canon references; Spatial/ComfyUI searches | AMBIGUOUS | NO complete Riverview implementation found | NO | NO | NO | PROPOSE/REVIEW/PUBLISH if later designed | No authoritative visual pipeline proven | High/design review |
| Jessica resident-to-system operations | YES later | Jessica Tranche J/L | PLANNED | NO | NO | NO | NO | READ/ADVISE/PROPOSE | Later residency tranche | High/later |
| Other offices’ occupational tools | PARTIAL | resident archetype WP-RC-000; roadmap §6 | PLANNED | mixed underlying services | NO resident broker | NO | office-specific | varies | System-wide gap likely | Reuse shared package after decision |

## What Riverview promised

### Grace

Durable promise categories:

1. Grace coordinates accepted work progression without becoming universal authority.
2. Grace is CME-aware and can evaluate readiness, blockage, stale state, and
   checkpoint routing.
3. Grace can use capability-aware provider/resource dispatch, including local AI,
   Codex, 4090/P100 capacity, and observed fuel/capacity.
4. Grace follows Comms5/MCP seed and objective lineage rather than manual
   copy/paste or blind continuation.
5. Grace can observe work, validation, recovery, dependencies, reports, and
   Steward-attention boundaries.
6. Grace can form governed engineering proposals and consume approved authority,
   while execution and acceptance remain separate.
7. Grace can consult bounded Cookbook/diagnostic knowledge and explain state.

Evidence is distributed across the Charter, Engineering Contract, Grace authority
migration, Phase 2/3/4 plan, Grace task template, CME checkpoints, Comms5 design,
autonomous-control-plane commits, and C1/C2/C3 resource report.

### Jessica

Durable promise categories:

1. Jessica is the Chief Character Architect, not a generic role-play persona.
2. She owns/recoveries professional Character Architecture doctrine and methods.
3. She distinguishes office, occupant, implementation, state, canon, proposal,
   observation, history, uncertainty, and Steward-authorized facts.
4. She inspects, discusses, proposes, and participates in independent review,
   Steward review, and publication through governed workflow.
5. Her professional corpus includes character identity, personality, behavior,
   relationships, cognition, continuity, voice/mannerism, character-bible
   methods, visual canon, validation, and creative work where evidenced.
6. She is a reusable resident-substrate tenant whose implementation can change
   without changing her identity.
7. She eventually participates in resident/system and event-driven operations.

Evidence is distributed across the resident-localization master roadmap, Jessica
execution specification, Tranche 0/A work packages, Jessica residency roadmap,
JCA tranche definitions, visual-canon method references, and character workflow
commits.

## Promise/design/build/connection diagnosis

### Grace

| Layer | Finding |
|---|---|
| Promise | Explicit and broad: operational coordination, CME, routing, work, resources, diagnostics, Cookbook, Comms5, escalation |
| Design | Explicit control-plane contracts and Grace authority/momentum designs exist |
| Built | Most underlying machinery exists and is separately tested |
| Connected to resident | Identity and selected context only; no dynamic occupational capability access |

### Jessica

| Layer | Finding |
|---|---|
| Promise | Explicit professional recovery and reusable resident continuity; visual/professional work included |
| Design | Roadmaps, work packages, continuity invariants, and governed workflow exist |
| Built | Character store/workflow and Operator route exist; broader professional corpus/visual pipeline is incomplete |
| Connected to resident | Separate workflow is reachable by Operator/Hermes, not conversational Jessica cognition |

## CME-specific reconciliation

### Was CME designed for Grace?

YES.

Evidence:

- Charter §6 describes Grace coordination and CME mandate together;
- Engineering Contract §5 says Grace is the operational coordinator and CME is the
  state-aware successor to blind continuation;
- migration 0024 creates a durable CME status model with state, current objective,
  stage, action, progress, waiting reason, and Steward attention;
- RIV-GRC-0004 explicitly describes Grace evaluation of objective/stage readiness;
- RIV-GRC-0008 explicitly requires CME event wakeup, cursor replay, and recovery;
- graph view `06_character_development.mmd` includes Grace/CME evaluation,
  objective state, providers, diagnostics, notifications, and verification.

### What was implemented?

- River event trigger and CME consumer;
- durable heartbeat/status/cursor;
- objective/stage evaluation through `GraceMomentum`;
- declared-action and typed formation path;
- Relay/Runner lifecycle;
- notification and diagnostic checkpoints;
- Operator/vNext CME and activity projections;
- Comms5 `cme_status` and lineage views.

### What reached Grace?

- Grace authority and HOME identity state;
- selected CME meaning/status in preassembled context;
- direct control-plane Grace evaluation methods in code;
- no general model-selected CME/work query in conversational HOME.

### How did CME acceptance pass?

CME acceptance proved runtime liveness, event wakeup, cursor recovery, heartbeat,
objective evaluation, work lifecycle, and control-plane transitions. It did not
require Grace to ask a novel operational question, select CME/work capabilities,
receive a typed result, and explain it. CME was accepted as a component/control
plane, not as a resident occupational instrument.

## Fuel/resource-specific reconciliation

### What was built

The C1/C2/C3 lane and related history built:

- observed seat/fuel telemetry;
- reset-window and freshness handling;
- resource registry and execution-resource model;
- provider/model/capability metadata;
- resource policy and audit;
- exclusive seat claims, leases, and release;
- resource planner and deterministic selection;
- Hermes/Codex binding and execution reports;
- Operator/Comms5 resource-policy projections.

Relevant implementation:

- `src/riverview/resources/registry.py`
- `src/riverview/resources/control.py`
- `src/riverview/autonomy/control.py`
- `src/riverview/campaign/hermes_executor.py`
- `src/riverview/operator/hermes_projection.py`
- migrations 0049–0052
- C1/C2/C3 report and commits `31606a0`, `07a9828`

### Who can use it today?

- Hermes/Runner can use resource selection and claims for execution;
- control-plane code can read policy, capacity, and claims;
- Comms5/Operator can project bounded resource metadata;
- Grace HOME can see selected capability references and resource-class provenance,
  but cannot dynamically query or reason over the fleet state;
- no model-selected Grace resource query exists.

This work is not wasted. It is reusable as a read-only occupational resource
projection after a resident capability contract is approved.

## Cookbook/troubleshooting reconciliation

Cookbook intent is explicit:

- Charter North Star requires a new authorized AI conversation or engineer to
  consult a bounded Troubleshooting Cookbook failure tree;
- ADR-0002 makes Cookbook coverage part of implementation;
- migrations 0002 and 0008 define durable Cookbook entries/read surfaces;
- `mcp/cookbook_sync.py` projects stable checkpoints, symptoms, probes, repairs,
  and verification procedures;
- Comms5/MCP exposes bounded Cookbook-related reads.

Built:

- PostgreSQL `cookbook_entries` schema;
- diagnostic-to-Cookbook references;
- sync and read surfaces;
- many stable checkpoint documents.

Connected to Grace HOME:

- NO. Cookbook references may appear in reports/context, but no model-selected
  resident retrieval adapter exists.

The correct future integration is a classification/freshness-aware read capability,
not a prompt dump of every Cookbook entry.

## Acceptance failure analysis

The recurring failure pattern is:

1. A durable requirement names Grace/Jessica as the intended consumer.
2. A component or control-plane implementation is built.
3. Its endpoint, unit tests, transport, or persistence is accepted.
4. No acceptance criterion requires the resident herself to discover and use it
   on a novel job-related question.
5. The separate workflow is mistaken for resident capability.
6. The resulting resident can state the title but cannot perform the office.

Specific patterns:

| Failure pattern | Evidence | Effect |
|---|---|---|
| Component acceptance only | CME/resource/Comms5/character tests | Machinery green, resident boundary untested |
| Endpoint mistaken for resident capability | `/api/jessica/character-development`, Comms5 methods, `/api/cme/status` | Operator/Hermes can call it; resident cannot |
| Static context mistaken for access | HOME packet contains selected references/facts | Model sees fragments but cannot retrieve current state dynamically |
| Workflow mistaken for resident cognition | `CharacterDesignerWorkflow`, Grace formation path | Dedicated code can do job; conversational resident cannot |
| No horizontal resident gate | baseline report accepted HOME identity/metadata and persistence | No occupational competence test |
| Requirements distributed across phases | Charter, roadmap, work packages, migrations, Cookbook | No single work-package acceptance joined promise to resident |
| Grace-first gate interpreted as execution gate | Jessica roadmap/execution spec | Grace orchestration machinery accepted without resident tool workspace |
| Visual/professional corpus deferred | JCA roadmap Tranche E/F onward | Jessica title and workflow exist before professional corpus retrieval |
| Canon/authority safety dominated acceptance | character review tests and authority tests | Correct safety, but not positive occupational usefulness |

This is architectural drift through acceptance fragmentation, not evidence that the
requirements existed only in a forgotten conversation.

## Context and memory architecture check

### A. Development context

Durable intent was substantially preserved. The Charter, contracts, roadmap,
migrations, Cookbook, Git history, and work packages contain the requirements.
The gap is that those requirements were not bound to a cross-cutting resident
acceptance invariant or resident capability work package.

### B. Resident runtime context

HOME has bounded identity, authority, continuity, and selected institutional
context. Context limits are real, but the observed defect is not solved by simply
increasing the context window.

### C. Capability access

This is the primary defect. The information exists in authoritative systems, but
resident cognition has no model-selected named capability path.

### D. Durable state

PostgreSQL, River, Git, Comms5, Cookbook, resource telemetry, and character stores
preserve substantial state. The resident boundary does not retrieve it dynamically.

### Would a larger Qwen context solve this?

NO.

A larger static context could increase available facts but would not provide:

- per-request capability authorization;
- freshness/lease semantics;
- model-selected retrieval;
- typed tool-result provenance;
- second reasoning pass;
- protection against irrelevant/protected state overexposure;
- resident-use acceptance evidence.

The missing architecture is capability access and reasoning continuation, not merely
token capacity.

## Other offices likely affected

| Resident/office | Existing tools/workflows | Resident-access gap | Severity |
|---|---|---|---|
| Grace / Operations | CME, objectives, work, Comms5, resources, Runner, Cookbook | No occupational workspace | Critical |
| Jessica / Character Architecture | CharacterStore/workflow, residency roadmap, visual method corpus | Workflow not callable from resident cognition; corpus incomplete | Critical |
| Engineering architects | Codex/Runner/formation/resource machinery | Execution/control plane exists, office cognition/tool boundary not established | High |
| Alfred / Administration | registry/room/coordination surfaces | No office-specific professional package found | Medium/High |
| Marie / Research | resident registry and research role | No research corpus/tool workspace found | Medium |
| Eleanor / Archives | registry/archive role references | No archive retrieval workspace found | Medium |
| Counsel / legal-risk | role-first roadmap references | No bounded legal/risk package found | Medium/High |
| Ingrid / Security | future gatekeeper architecture and security hooks | Deliberately deferred; no resident capability expected yet | Deferred |
| Comptroller / resources | role-first resource oversight references | Resource machinery exists, resident office integration absent | High |
| Evelyn / deeply developed resident | historical character/visual corpus | Migration/continuity not complete | High/Later |

This is therefore a likely system-wide resident occupational-capability gap, with
Grace and Jessica exposing it first because their supporting machinery is most mature.

## Proposed permanent acceptance invariant

Do not modify governance in this tranche. The evidence supports placing this
invariant in:

- `RIVERVIEW_ENGINEERING_INTERACTION_CONTRACT.md`;
- resident-localization work-package common acceptance contract;
- capability-specific acceptance templates;
- possibly a concise ADR if the Steward wants it elevated to architecture policy.

Recommended wording:

> No Riverview capability is complete when its accepted design requires a resident
> to observe, reason over, advise on, propose through, or otherwise use that
> capability until the resident integration is also verified on a novel
> job-related question with authoritative result, provenance, authority,
> freshness, and failure evidence.

This does not grant authority. It requires proof that the designed resident can
actually use the designed capability.

## Proposed recovery sequence

1. Steward reviews this forensic map and approves the resident capability
   architecture direction.
2. Bind each accepted resident-office promise to a durable capability acceptance
   row/work package, not only to a component package.
3. Define reusable resident capability package, broker, tool request/result, and
   reason/retrieve/reason continuation contracts.
4. Implement Grace current-work read slice.
5. Implement Jessica current-canon read slice.
6. Add generalization/paraphrase and negative authority/freshness tests.
7. Require live resident model/tool/model provenance before declaring a capability
   complete.
8. Expand only after the first two slices prove the shared architecture.

## Final boundary

- Three audit artifacts are the only new deliverables.
- No ResidentOfficeCapabilityPackage implemented.
- No ResidentCapabilityBroker implemented.
- No model tool calling implemented.
- No operations.current-work.read implemented.
- No character.canon.read implemented.
- No Grace/Jessica speech recovery added.
- No phrase routing added.
- No canon invented or published.
- No authority expanded.
- No runtime lifecycle work opened.
- No resident returned for human acceptance.

Status: `READY_FOR_STEWARD_REVIEW` for the forensic architecture map only; not
technical acceptance of resident occupational competence.
