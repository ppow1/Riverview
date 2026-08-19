# Jessica Localization Campaign Execution Specification

Status: Planning architecture — not authorization for execution  
Date: 2026-08-19  
Primary execution owner: Grace, once autonomous engineering capability is accepted  
Roadmap reference: `docs/architecture/riverview_resident_localization_master_roadmap.md`

## 1. Purpose

This specification defines how the Jessica / Chief Character Architect localization roadmap is to be executed once Grace is authorized to manage autonomous engineering campaigns.

The campaign is intentionally event-driven, tranche-based, dependency-aware, and capable of using governed escalated reasoning for clarification, independent review, and double-checking of consequential decisions.

This document does not authorize implementation. It defines the execution mechanism that downstream work packages and Grace automation should follow.

## 2. Core execution model

The campaign hierarchy is:

`Roadmap -> Campaign -> Tranche -> Work Package -> Evidence -> Gate -> Next Tranche`

A tranche is a dependency and knowledge boundary, not merely a scheduling batch.

Work packages inside a tranche may execute concurrently when their dependencies, repository collision profile, and acceptance rules allow it.

Grace must react to state transitions rather than blindly stream work packages one after another.

Example:

`JCA-001 + JCA-002 + JCA-003 + JCA-004 accepted -> JCA-005 becomes READY`

`JCA-005 accepted -> Archaeology Gate becomes COMPLETE`

`Archaeology Gate complete -> Tranche B may be refined / instantiated`

## 3. Progressive elaboration rule

Do not fully freeze all downstream work packages before upstream evidence exists.

Three levels are used:

1. **Roadmap package** — stable name, purpose, broad dependencies, and expected outcome.
2. **Tranche-ready package** — executable contract with resolved scope, inputs, acceptance criteria, evidence requirements, cookbook obligations, and dependency state.
3. **Dispatched work order** — instantiated execution object with current repository paths, provider / lane assignment, resolved evidence, correlation IDs, and current runtime context.

Downstream packages may be refined after an upstream tranche produces new authoritative evidence, provided the roadmap intent and Steward-approved boundaries are preserved.

Grace may not silently expand campaign scope beyond the roadmap.

## 4. Grace autonomous authority inside the campaign

Once the campaign is explicitly authorized, Grace may autonomously:

- identify READY work packages from the campaign DAG;
- dispatch parallel-safe work to approved engineering providers;
- choose among approved execution lanes according to provider policy, scope, cost, privacy, capability, and current availability;
- observe lifecycle events and completion evidence;
- request validation and bounded rework;
- retry transient failures within accepted retry policy;
- update objective / campaign state through approved Riverview mechanisms;
- advance dependent work when acceptance gates are satisfied;
- request escalated reasoning at any stage permitted by this specification;
- notify the Steward only when a genuine decision / acceptance / authority boundary is reached or a stop condition occurs.

Grace may not autonomously:

- redefine Jessica's canonical identity;
- grant herself or another resident new institutional authority;
- bypass a Steward acceptance gate;
- reinterpret uncertain Estate evidence as fact without preserving uncertainty;
- authorize work outside the campaign boundary;
- weaken privacy, classification, or data-egress controls;
- convert advisory reasoning into institutional authority;
- create a second competing source of truth for roadmap, objective, lifecycle, or cookbook state.

## 5. Reasoning Escalation Policy

### 5.1 Principle

Grace is explicitly permitted and encouraged to seek escalated reasoning when she has questions, encounters ambiguity, wants an independent critique, or wants to double-check her own conclusion before advancing consequential work.

Escalated reasoning is an institutional cognitive service, not a new authority lane.

**Reasoning escalation provides advice, not authority.**

The requesting resident remains responsible for reconciling the advisory result against Riverview evidence, contracts, current state, and authority boundaries.

### 5.2 Approved use classes

#### A. Clarification / uncertainty resolution

Use when Grace encounters:

- conflicting repository evidence;
- ambiguous Estate provenance;
- unclear dependency state;
- unclear acceptance criteria;
- uncertain interpretation of a historical reflection or work package;
- a design question not sufficiently answered by the roadmap, cookbook, repository, or runtime state;
- incomplete knowledge that could materially change the next action.

#### B. Independent review / double-check

Use proactively when Grace has a proposed answer or plan but wants a separate reasoning pass before proceeding.

This is especially appropriate for:

- architecture choices with broad downstream effects;
- database / continuity model changes;
- provenance classification decisions;
- migration disposition decisions;
- identity or authority-related interpretation;
- rehydration / memory architecture;
- large tranche transitions;
- final acceptance recommendations.

#### C. Exception handling

Use when:

- validation fails unexpectedly;
- multiple retries fail;
- evidence contradicts the roadmap assumption;
- a work package appears to require scope expansion;
- a provider returns materially conflicting results;
- the campaign appears to be drifting from its objective;
- Grace must choose between retry, replan, defer, or Steward escalation.

### 5.3 Optional / recommended / mandatory escalation

#### Optional

Grace may escalate whenever a second opinion would improve confidence at reasonable cost.

#### Recommended

Grace should normally escalate when:

- confidence is materially below normal operating threshold;
- two plausible interpretations could produce different downstream work;
- the decision is expensive to reverse;
- the decision affects more than one resident or shared continuity primitive;
- the campaign is about to cross a major tranche gate;
- a novel failure has no close cookbook precedent.

#### Mandatory

Before proceeding without Steward review, Grace must obtain an independent reasoning check for at least:

1. final Estate artifact disposition / provenance synthesis before JCA-005 acceptance;
2. proposed shared PostgreSQL continuity model before schema implementation;
3. any rule governing resident self-modification or canonical identity mutation;
4. final rehydration / implementation-transition design;
5. pre-Steward Jessica residency acceptance assessment;
6. any proposed change that would materially affect the known future resident substrate rather than Jessica alone;
7. any case where historical evidence conflicts with a Steward-authorized fact.

Mandatory reasoning review does not replace a Steward gate where one already exists.

## 6. Reasoning provider abstraction

The campaign must not hard-code one reasoning provider as permanent.

A reasoning request should use an approved provider contract capable of routing to, for example:

- ChatGPT / OpenAI high-reasoning capability;
- Codex for repository-grounded technical review where appropriate;
- stronger local reasoning models as they become available;
- future specialized external reasoning services;
- multiple providers for adversarial or comparative review where justified.

Provider selection should consider:

- required reasoning depth;
- repository context requirements;
- data classification / privacy;
- egress restrictions;
- cost;
- latency;
- provider availability;
- need for independent perspective;
- whether the provider is also the implementation author and therefore not sufficiently independent for the desired review.

## 7. Reasoning request evidence contract

Every escalated reasoning request used to influence a consequential campaign decision should produce an auditable advisory record containing at least:

- request ID;
- campaign / tranche / work-package reference;
- requesting resident / service;
- reason for escalation;
- question posed;
- bounded evidence / context supplied;
- provider identity / model class where available;
- classification / egress decision;
- response summary;
- confidence / uncertainty if available;
- citations / repository references where applicable;
- Grace's reconciliation decision;
- whether the advisory result changed the proposed action;
- whether Steward review was triggered.

The full raw provider response need not always become durable canonical state. Preserve enough evidence to audit why a consequential decision was made without creating uncontrolled context accumulation.

## 8. Independent review semantics

When Grace requests a double-check, the review should be meaningfully independent where practical.

Do not merely ask the same implementation worker to affirm its own work and call that independent review.

Preferred order for consequential review:

1. retrieve current authoritative evidence and cookbook guidance;
2. form Grace's provisional conclusion;
3. send a bounded question to an independent reasoning provider or reviewer;
4. compare the returned reasoning against Grace's conclusion;
5. reconcile disagreements explicitly;
6. proceed within authority or stop at the appropriate gate.

Disagreement itself is useful evidence and must not be flattened into false consensus.

## 9. Event-driven tranche behavior

The campaign should operate through lifecycle events.

Examples:

- `work_package.accepted`
- `work_package.failed`
- `validation.failed`
- `dependency.cleared`
- `provider.unavailable`
- `reasoning.review.completed`
- `tranche.ready`
- `tranche.completed`
- `steward.decision.required`

The target loop is:

`event -> Grace evaluates state -> local reasoning / cookbook lookup -> optional or required escalated reasoning -> permitted action -> new event`

The Steward should not be used as the polling loop.

## 10. Notification policy

Notifications are the human interrupt channel, not a substitute for autonomous continuation.

Grace should notify the Steward when:

- explicit Steward authority is required;
- a tranche acceptance checkpoint is defined as Steward-owned;
- evidence is materially contradictory and cannot be safely reconciled;
- campaign scope would need to change;
- privacy / security / egress policy blocks required work;
- repeated failure exceeds accepted recovery policy;
- mandatory reasoning review recommends stopping or substantially changing direction;
- the campaign reaches final Jessica residency acceptance.

Grace should not notify the Steward merely because:

- a normal work package completed;
- a routine validation passed;
- a transient retry succeeded;
- a dependency became ready and the next package is already authorized;
- an advisory reasoning request returned and Grace can reconcile it within authority.

## 11. Initial tranche structure

### Tranche 0 — Population and architecture guardrails

- WP-RC-000
- WP-RC-001
- WP-RC-002

These may execute in parallel where their detailed package contracts permit it.

Gate: shared resident-continuity invariants accepted and no known future-resident blocker identified.

### Tranche A — Jessica / Estate archaeology

Parallel discovery group:

- WP-JCA-001 — Office of Character Architecture source inventory
- WP-JCA-002 — Jessica officeholder continuity evidence inventory
- WP-JCA-003 — Character Architecture work-product and method inventory
- WP-JCA-004 — Estate artifact provenance and disposition classification

Synthesis dependency:

- WP-JCA-005 — Jessica recovery corpus manifest and gaps report

JCA-005 becomes READY only when required discovery evidence is accepted.

Gate: bounded Jessica recovery corpus accepted and sufficient to refine Tranche B.

### Later tranches

Tranches B onward remain roadmap-defined but are progressively elaborated using accepted upstream evidence.

Do not dispatch later tranches merely because files exist. Their tranche-ready contracts must be generated / revalidated against the latest accepted evidence.

## 12. Cookbook integration

The campaign specification itself should become a cookbook waypoint once implementation begins.

Every implementation package affecting resident infrastructure must update the cookbook with first-pass operational understanding before package acceptance.

If an autonomous run discovers that cookbook guidance is incomplete or wrong, the resulting correction is part of the work, not an optional documentation follow-up.

Novel failures should leave behind searchable troubleshooting evidence so the next campaign does not rediscover the same architecture manually.

## 13. Campaign stop / replan conditions

Grace must stop autonomous forward progression and request appropriate review when:

- a Steward-approved identity fact would be contradicted or overwritten;
- a required source cannot be accessed and proceeding would require invention;
- the roadmap's shared architectural invariant is no longer viable;
- a package unexpectedly requires a security / privacy capability not currently available;
- a change would materially expand the campaign beyond Jessica / resident-continuity scope;
- a mandatory independent review identifies unresolved high-impact risk;
- the evidence indicates that a previously planned downstream tranche is based on a materially false assumption;
- Grace cannot distinguish implementation history from resident identity with sufficient confidence;
- autonomous execution itself is not functioning reliably enough to preserve campaign state.

A stop condition is not failure. Correctly stopping at the right authority or evidence boundary is successful autonomous behavior.

## 14. Campaign performance measures

Do not judge the campaign only by package count or commit count.

Track separately:

- accepted work packages;
- machine-active execution minutes;
- validation / rework minutes;
- critical-path wall-clock time;
- parallelism achieved versus available;
- provider utilization;
- autonomous continuation duration;
- number and purpose of reasoning escalations;
- percentage of escalations resolved without Steward interruption;
- Steward intervention count;
- Steward-touch minutes;
- archaeology avoided through cookbook reuse;
- novel cookbook knowledge created;
- number of stop conditions correctly detected before unsafe action.

A key long-term metric is **Steward Intervention Density**: Steward attention required per unit of accepted institutional progress.

## 15. Immediate follow-on work

Once this specification is accepted as planning truth, the next authoring step is:

1. write complete tranche-ready specifications for WP-RC-000 through WP-RC-002;
2. write complete tranche-ready specifications for WP-JCA-001 through WP-JCA-005;
3. write the machine-readable / implementation-consumable Jessica campaign manifest that expresses dependencies, gates, reasoning-review requirements, stop conditions, and notification ownership;
4. do not dispatch the campaign until Grace's autonomous engineering workflow is repaired and accepted.

The intended first real test is not whether Grace can execute one package. It is whether Grace can take one bounded multi-stage campaign, exploit safe parallelism, obtain additional reasoning when useful, double-check consequential decisions, react to lifecycle events, and return to the Steward only at the correct judgment boundary.
