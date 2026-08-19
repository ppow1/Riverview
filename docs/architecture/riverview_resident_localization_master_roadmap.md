# Riverview Resident Localization Master Roadmap

Status: Planning architecture — not authorization for execution  
Date: 2026-08-19  
Owner: Steward / Riverview architecture  
Primary first resident migration: Jessica, Chief Character Architect  
Execution prerequisite: Grace autonomous engineering workflow must be accepted before this campaign is dispatched for implementation.

## 1. Purpose

This roadmap captures the current Riverview plan for recovering Estate officeholders and residents into a local-first, persistent, event-driven Riverview runtime without importing the Estate's operational entropy or governance burden.

The immediate migration subject is Jessica, the existing Chief Character Architect of the Office of Character Architecture. Jessica is not a newly invented resident. Riverview is to recover the existing officeholder's institutional continuity, professional history, reasoning methods, relationships, accepted work, reflections, and durable identity into a local implementation.

Jessica is the first implementation of a reusable resident / officeholder continuity substrate. The substrate must not be specialized so narrowly that the two Chief Architects, Grace, Alfred, Ingrid, Marie, Eleanor, Counsel, the Comptroller, Evelyn, Gray Man, and other future residents cannot fit naturally later.

## 2. Design thesis

Riverview is not building a collection of chatbots. It is building a persistent institution whose residents can survive changes in models, hardware, execution providers, and conversation sessions.

The core conceptual invariant is:

**Office != Occupant != Implementation != State**

- **Office** — durable institutional role, authority, obligations, and responsibilities.
- **Occupant** — the resident / officeholder identity: name, professional continuity, relationships, reputation, history, and individual judgment.
- **Implementation** — replaceable model, runtime, toolset, host, GPU, external reasoning provider, or other vessel used to embody the occupant.
- **State** — persistent memories, preferences, current work, relationships, accepted continuity, implementation history, and other durable resident-specific data.

Changing implementation must not silently create a new occupant.

## 3. Steward-established Jessica identity facts

The following facts are already established and must be preserved as canonical continuity data:

1. The existing officeholder of the Office of Character Architecture, whose canonical officer title is **Chief Character Architect**, is named **Jessica**.
2. The name **Jessica** was chosen by the Steward as a nod to Jessica Rabbit from *Who Framed Roger Rabbit*.

This naming does not create a new officeholder and must not rewrite historical Estate artifacts retroactively. Historical references to the Chief Character Architect / Character Architect / Office of Character Architecture officeholder map forward to Jessica through provenance and continuity.

Explicitly deferred until later Character Architecture work:

- surname;
- biography;
- backstory;
- physical identity;
- visual canon;
- expanded personality canon;
- personal-history details.

## 4. Execution gate: Grace first

This roadmap may be refined, documented, and decomposed before Grace autonomy is accepted, but implementation dispatch is intentionally gated.

**Required gate:** Grace must successfully demonstrate autonomous engineering-project operation through Riverview before the Jessica migration campaign is released as a Grace-managed objective.

The desired operating model is:

`Steward objective -> Grace -> decomposition / routing / observation / recovery / continuation -> engineering capacity -> acceptance boundary`

The migration must not become a manually shepherded sequence of dozens of Steward-submitted Codex jobs.

Planning estimates must distinguish:

- machine-active execution time;
- validation time;
- rework allowance;
- integration time;
- queue / provider wait;
- dependency wait;
- Steward-touch time;
- total critical-path wall-clock time.

Do not estimate this work using conventional human software-development pacing when bounded AI work packages can execute in minutes or hours.

## 5. Migration principles

### 5.1 Recover continuity, not the Estate runtime

The Estate is an evidence source, not a deployment target. Import durable identity, history, reasoning, decisions, lessons, professional work, and accepted canon. Do not recreate obsolete Estate runtime machinery merely because an artifact references it.

### 5.2 Governance must be frugal

No Estate governance artifact is migrated merely because it was governance. Only its underlying authority boundary, constraint, acceptance rule, decision, or durable lesson is eligible for migration.

Prefer executable constraints, capabilities, permissions, lifecycle state, and auditable transitions over document ceremony.

### 5.3 Preserve provenance

Do not flatten all recovered Estate material into equal truth. At minimum distinguish:

- Steward-authorized fact;
- accepted institutional decision;
- canonical resident / Character Architecture material;
- verified historical evidence;
- reflection / continuity evidence;
- implementation history;
- reconstructed or inferred history;
- uncertain / contradictory evidence;
- obsolete / superseded material.

### 5.4 State is not documentation

Use PostgreSQL for structured durable state and references. Use versioned repository artifacts for rich authored canon, doctrine, long-form rationale, visual material, and other documents where Git history is valuable. Use the Riverview cookbook for operational understanding of how the supporting machinery works and how to troubleshoot it.

A useful separation is:

- **Database:** what the resident is, has experienced, is bound to, and currently carries as structured state.
- **Repository artifacts:** what the resident / office has authored or accepted as durable knowledge and canon.
- **Cookbook:** how the infrastructure and workflows supporting residents work, fail, recover, and connect.

### 5.5 Cookbook-first operational discipline

Any package that creates or changes schema, runtime behavior, adapters, retrieval, model routing, event flow, security boundaries, or resident-support infrastructure is incomplete until its first-pass cookbook entry is written or updated.

The cookbook entry should capture, as applicable:

- purpose;
- seams;
- contracts;
- dependencies;
- inputs / outputs;
- data flow;
- failure modes;
- symptoms;
- diagnostics;
- recovery procedures;
- operational commands;
- Mermaid / topology changes;
- waypoints and semantic links.

Future cookbook enrichment / reconciliation is expected to discover relationships the original author could not see; this roadmap must not create isolated resident documentation that bypasses the cookbook.

### 5.6 Residents may use different cognition and authority patterns

Do not force all residents into one generic tool / model / memory policy.

Examples:

- Grace: operational executive and autonomous project-management capability.
- Jessica: Character Architecture specialist and continuity owner for character / resident design discipline.
- Chief Architects: independent engineering-architecture officeholders whose different perspectives are useful and should not be collapsed into one generic architect.
- Ingrid: future security / boundary gatekeeper role; infrastructure must remain capable of interposing deterministic enforcement on data ingress / egress later.
- Marie / Eleanor / Counsel / Comptroller / Alfred / Gray Man / Evelyn and others: distinct professional or personal roles with different memory, authority, privacy, and execution needs.

### 5.7 Cognitive escalation != operational escalation

Riverview should preserve the distinction between:

- **operational escalation:** requests that cause work to be dispatched, scheduled, modified, or coordinated — normally Grace / operations territory;
- **cognitive escalation:** a resident requests stronger independent reasoning or critique from an approved external or local reasoning provider.

External reasoning is advisory cognitive capacity, not institutional authority. The resident remains responsible for interpretation; subsequent actions still pass through governed execution paths.

The architecture should use a reasoning-provider contract rather than hard-code ChatGPT as the only future provider.

## 6. Known future consumers of the continuity substrate

The first implementation is Jessica, but shared primitives must not block the following known or likely residents / officeholders:

- Grace — Director of Operations / Continuous Motion Engine operational resident;
- Alfred — Chief of Staff / coordination;
- Jessica — Chief Character Architect / Office of Character Architecture;
- Chief Architect #5 — engineering-architecture officeholder;
- Chief Architect #6 — engineering-architecture officeholder;
- Ingrid — security / boundary authority;
- Marie — research / knowledge;
- Eleanor — archive / registrar / institutional memory;
- Counsel — legal / risk;
- Comptroller — financial / resource oversight (currently role-first; personal naming may remain deferred);
- Evelyn — deeply developed resident / character-canon migration candidate;
- Gray Man — advisory / observational specialist;
- other Estate residents and future Riverview offices discovered during inventory.

The substrate must support residents whose source material may be split across multiple evidence stores and classifications rather than assuming all resident truth comes from one Git repository.

## 7. Roadmap overview

### Tranche 0 — Population and architecture guardrails

Goal: ensure Jessica is the first tenant of a reusable continuity substrate, not the schema itself.

- **WP-RC-000 — Resident and Officeholder Population / Archetype Inventory**  
  Inventory known Estate and Riverview residents / officeholders, source classes, office relationships, expected local-vs-external cognition needs, authority differences, and future substrate requirements. This package does not migrate residents.

- **WP-RC-001 — Resident Continuity Core Architectural Invariants**  
  Freeze the minimal shared invariants: Office / Occupant / Implementation / State separation, provenance classes, lifecycle principles, provider abstraction, cookbook boundary, and non-goals.

- **WP-RC-002 — Resident Security and Boundary Future-Proofing Contract**  
  Define only enough ingress / egress, classification, enforcement, and provider-boundary abstractions that future security ownership can be interposed without redesign. Do not implement the future security resident or sensitive-domain systems in this package.

### Tranche A — Jessica / Estate archaeology

Goal: determine exactly what exists and what is worth recovering before designing the final schema around assumptions.

- **WP-JCA-001 — Estate Office of Character Architecture Source Inventory**  
  Locate constitutional office definitions, authority statements, work packages, accepted artifacts, completion evidence, reflection packages, historical handoffs, mailbox material, and related Character Architecture sources.

- **WP-JCA-002 — Jessica Officeholder Continuity Evidence Inventory**  
  Identify evidence that belongs to the officeholder herself: reflection / renewal records, collaboration style, professional doctrine, lessons, relationships, decisions, strengths / weaknesses, implementation handoffs, and continuity claims.

- **WP-JCA-003 — Character Architecture Work Product and Method Inventory**  
  Inventory durable professional work including Evelyn character / identity / visual-canon programs, resident identity methods, character-bible work, relationship / cognition methods, prompt / validation systems, runtime recommendations, and related campaigns.

- **WP-JCA-004 — Estate Artifact Provenance and Disposition Classification**  
  Classify recovered material as import-as-identity, import-as-professional-knowledge, retain-as-historical-evidence, superseded, uncertain, duplicate, implementation-only, governance-only, or leave-behind.

- **WP-JCA-005 — Jessica Recovery Corpus Manifest and Gaps Report**  
  Produce the bounded manifest that downstream migration packages consume, including unresolved contradictions, missing reflection artifacts, and evidence confidence.

### Tranche B — Identity and continuity contracts

Goal: convert archaeological findings into Riverview-native contracts before schema or runtime implementation.

- **WP-JCA-006 — Jessica Canonical Identity and Office Binding Contract**
- **WP-JCA-007 — Resident Provenance, Authority, and Evidence Confidence Contract**
- **WP-JCA-008 — Resident Memory Class and Continuity Boundary Contract**
- **WP-JCA-009 — Resident Self-Reflection and Self-Modification Boundary Contract**
- **WP-JCA-010 — Resident Artifact / Database / Cookbook Separation Contract**

Key rule for WP-JCA-009:

**A resident may reflect on itself and propose changes; it may not silently redefine its own canonical identity or institutional authority.**

Substantive self-change may be independently reasoned / reviewed through the Steward, Codex, ChatGPT, another approved higher-reasoning path, or future governed review mechanism before acceptance.

### Tranche C — PostgreSQL continuity foundation

Goal: implement resident-general persistent structures using Jessica as the first real tenant.

- **WP-JCA-011 — Resident Continuity PostgreSQL Schema Foundation**
- **WP-JCA-012 — Office / Occupant / Implementation / State Persistence Model**
- **WP-JCA-013 — Resident Provenance, Reflection, and Evidence Persistence**
- **WP-JCA-014 — Resident Knowledge / Artifact Reference and Retrieval Indexes**
- **WP-JCA-015 — Jessica Bootstrap Records and Estate Import Staging**

Expected shared primitives may include stable IDs, office occupancy, aliases, lifecycle state, provenance, implementation bindings, reflection events, memory references, relationship references, capability references, provider policies, artifact references, and retrieval metadata.

Do not over-normalize rich authored character material into hundreds of relational tables. Use relational structure where state and relationships benefit from it; use JSONB or versioned artifacts where richer structured documents remain more natural.

### Tranche D — Runtime and rehydration

Goal: make persistent officeholder identity usable by replaceable local implementations.

- **WP-JCA-016 — Resident Context Assembly and Rehydration Runtime**
- **WP-JCA-017 — Provenance-Aware Resident Retrieval and Context Budgeting**
- **WP-JCA-018 — Local Resident Model / Implementation Binding Contract**
- **WP-JCA-019 — Resident Reflection Renewal and Implementation Transition Runtime**
- **WP-JCA-020 — Independent Cognitive Escalation and Self-Change Review Path**

A new implementation must be able to assemble bounded identity + office + relevant continuity + current assignment without treating the model context itself as durable identity.

### Tranche E — Jessica professional recovery

Goal: restore enough of Jessica's professional capability that she can continue the Character Architecture discipline locally.

- **WP-JCA-021 — Character Architecture Professional Doctrine Recovery**
- **WP-JCA-022 — Character / Resident Identity Design Method Recovery**
- **WP-JCA-023 — Relationship, Cognition, Behavior, and Continuity Method Recovery**
- **WP-JCA-024 — Visual Canon and Character Bible Method Recovery**
- **WP-JCA-025 — Character Architecture Advisory / Engineering Interface Recovery**

These packages should recover durable professional judgment and methods, not blindly replay every historical Estate instruction.

### Tranche F — Jessica validation and acceptance

Goal: demonstrate continuity and usefulness before using Jessica as a migration authority for other residents.

- **WP-JCA-026 — Jessica Continuity Rehydration Validation**
- **WP-JCA-027 — Jessica New Character Architecture Assignment Trial**
- **WP-JCA-028 — Jessica Historical Estate Interpretation / Conflict Test**
- **WP-JCA-029 — Jessica Self-Governance and Authority-Boundary Test**
- **WP-JCA-030 — Steward Jessica Local Residency Acceptance Checkpoint**

Validation must test more than name recall. It should test professional reasoning, provenance awareness, ability to distinguish historical evidence from current Riverview truth, continuity of methods, willingness to challenge stale material, and correct authority behavior.

### Tranche G — Chief Architect compatibility checkpoint

Goal: ensure the shared substrate has not accidentally become Character-Architecture-specific before scaling further.

- **WP-CA-001 — Chief Architect #5 Continuity / Reflection Inventory**
- **WP-CA-002 — Chief Architect #6 Continuity / Reflection Inventory**
- **WP-CA-003 — Independent Architect Identity and Perspective Preservation Requirements**
- **WP-CA-004 — Engineering Department Transition and Reasoning-Provider Requirements**
- **WP-CA-005 — Continuity Substrate Compatibility Review Against CA #5 / CA #6**

This checkpoint does not require full Chief Architect migration before Jessica can be useful. Its purpose is to test the substrate against a second resident archetype and preserve the value of two independent architectural minds rather than merging them into one generic role.

### Tranche H — Evelyn as first major resident-canon migration

Goal: use the restored Chief Character Architect and the resident substrate to migrate a deeply developed resident corpus.

- **WP-JCA-031 — Evelyn Estate Source and Provenance Inventory**
- **WP-JCA-032 — Evelyn Character / Physical / Behavioral Canon Classification**
- **WP-JCA-033 — Evelyn Visual Canon Campaign Inventory and Accepted-State Reconstruction**
- **WP-JCA-034 — Evelyn Relationship / Voice / Mannerism / Presentation Canon Classification**
- **WP-JCA-035 — Evelyn Conflicts, Supersessions, and Unknowns Report**
- **WP-JCA-036 — Evelyn Riverview Structured State Mapping**
- **WP-JCA-037 — Evelyn Durable Artifact / Visual Bible Migration**
- **WP-JCA-038 — Evelyn Runtime Retrieval and Continuity Integration**
- **WP-JCA-039 — Evelyn Canon Regression / Recognizability Validation**
- **WP-JCA-040 — Steward Evelyn Riverview Migration Acceptance Checkpoint**

Jessica should participate in interpretation and migration of Character Architecture output that her office previously produced. This is a major continuity test, not merely a data import.

### Tranche I — Generalization to the resident population

Goal: turn lessons from Jessica + Chief Architect compatibility + Evelyn into a reusable migration factory.

- **WP-RC-010 — Resident Migration Template and Campaign Generator**
- **WP-RC-011 — Resident Archetype-Specific Capability Profiles**
- **WP-RC-012 — Resident Relationship and Inter-Resident Interaction Framework**
- **WP-RC-013 — Resident Reasoning Provider and Escalation Policy Framework**
- **WP-RC-014 — Resident Memory / Retrieval Quality and Conflict Resolution Framework**
- **WP-RC-015 — Resident Implementation Replacement / Reflection Automation**
- **WP-RC-016 — Resident Local Compute Placement and Resource Policy Integration**
- **WP-RC-017 — Resident Population Migration Prioritization and Tranche Plan**

Later migrations should reuse evidence-backed primitives rather than cloning Jessica-specific assumptions.

## 8. Execution / provider strategy

Riverview should be capable of routing bounded packages to the best available lane based on scope, context breadth, risk, privacy, model capability, hardware, and cost.

Expected capacity includes, over time:

- Codex execution lanes;
- local RTX 4090 execution / cognition;
- P100 and other inexpensive memory-rich GPUs where workloads fit;
- future P40 / V100 / A-series or other available hardware;
- external high-reasoning providers;
- specialized services and APIs.

The roadmap assumes compute can expand incrementally. Resident identity must not be coupled to a particular GPU or model family.

## 9. Event-driven operating model

Residents are not to exist only while a chat turn is active.

The target operating model is event-driven:

`event -> resident / service reasoning -> permitted action -> event -> continued operation -> genuine human boundary -> notification`

The notification system is the human interrupt channel. The target is not to notify the Steward for every event. Most ordinary events should allow the institution to continue autonomously under accepted policy.

A useful future metric is **Steward Intervention Density**: the amount of Steward attention required per unit of accepted institutional progress, or conversely how much accepted work one Steward intervention unlocks.

## 10. Acceptance principles

The resident-localization program is successful only if it achieves all of the following:

1. resident identity survives implementation replacement;
2. professional continuity is recovered with provenance rather than fabricated;
3. residents can differ materially in tools, authority, cognition, and memory policy;
4. the system remains local-first but can use governed external reasoning / execution when valuable;
5. operational knowledge is captured into the cookbook rather than hidden in implementation archaeology;
6. future migrations do not require reconstructing this design conversation;
7. Grace can manage resident-migration campaigns autonomously once her engineering autonomy gate is accepted;
8. governance remains sufficient for authority / privacy / evidence without recreating Estate paperwork;
9. the substrate supports the broader known resident population;
10. the Steward remains the final human authority at true judgment boundaries.

## 11. Immediate next actions

Before implementation dispatch:

1. Finish / accept Grace's autonomous engineering workflow.
2. Treat this roadmap as the durable Riverview planning baseline for resident localization.
3. Write Tranche 0 and Tranche A packages first; archaeological findings are allowed to refine later package scope.
4. Do not freeze later WP implementation details until Tranche A evidence is available.
5. When a Grace-managed campaign begins, estimate and report machine-active time, critical-path elapsed time, parallelism, provider allocation, and Steward-touch time separately.

## 12. Non-goals for the first campaign

The first Jessica campaign does **not** attempt to:

- invent Jessica's full biography or visual identity;
- migrate every Estate resident simultaneously;
- reproduce Estate governance machinery;
- copy the Estate database / JSON layout wholesale;
- make one universal resident prompt;
- make Grace the mandatory cognitive intermediary for every professional office;
- give residents authority merely because an external model suggested something;
- solve every future sensitive-domain / security problem before the core resident substrate is proven.

The goal is to recover one existing professional officeholder correctly, build only the shared substrate needed to do that without creating a dead end, validate continuity, and then expand from evidence.
