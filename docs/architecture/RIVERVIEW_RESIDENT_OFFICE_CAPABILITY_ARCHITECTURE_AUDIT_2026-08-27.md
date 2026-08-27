# Riverview Resident Office Capability / Occupational Competence Audit

Date: 2026-08-27  
Status: ARCHITECTURE REVIEW / PROTOTYPE BLOCKED AT DESIGN BOUNDARY  
Scope: Grace, Director of Operations; Jessica, Chief Character Architect  
Acceptance state: Grace behavioral acceptance paused; no resident returned for human acceptance

## Executive finding

Riverview currently gives residents identity, office/title metadata, bounded HOME
Cognition, selected institutional context, and a speech-composition seam. It does
not yet give a resident an occupational workspace containing dynamically selectable
role-appropriate read/proposal capabilities.

The effective live path is:

```text
Operator /api/chat
  -> ResidentConversationGateway
    -> PostgresAuthoritativeGraceStateSource
      -> ResidentContextAssembler / F2 packet
        -> one HOME Cognition Qwen request
          -> typed internal advisory result
            -> speech composition
              -> durable conversation
```

The path is not currently:

```text
resident reasoning
  -> model-selected bounded capability
    -> authoritative result
      -> further reasoning
        -> validated speech
```

This explains the observed behavior. Grace and Jessica can recite identity and
some preassembled facts, but they cannot reliably perform novel occupational
work because the reasoning boundary has no resident-scoped capability broker or
model-selected retrieval loop.

This is not primarily a character-quality problem and should not be addressed by
more speech cases, phrase routing, or additional canned fallbacks.

## Authority and provenance boundary

Repository/runtime preflight was performed against:

- repository: `A:\Riverview\standalone`
- branch: `main`
- local HEAD at audit start: `42af760954f1eacd30cb69340cc0cfc11d216347`
- `origin/main`: `c88be3ffe6720419a55d9e0f4660a88616b70ce3`
- state at audit start: local `main` ahead 1 and behind 2; unrelated dirty and untracked overlays preserved
- live source root: `A:\Riverview\standalone`
- live source SHA: `42af760954f1eacd30cb69340cc0cfc11d216347`
- launch owner: `windows-task:Riverview Runtime Supervisor`
- provider: `ollama`
- model: `qwen3-coder:30b-qwencode-20k`
- HOME: enabled through `HomeCognitionService`
- runtime listener: one listener on `127.0.0.1:18082`
- final observed Supervisor/Operator state during audit: both running, Operator restart count 0, last failure null

No runtime Supervisor repair was opened. No runtime source, credentials, character
canon, authority, or Jessica workflow was changed during this architecture audit.

## Existing architecture inventory

### Identity, offices, and occupancy

Existing evidence and implementation:

- `src/riverview/residents/gateway.py`
  - `ResidentProfile`
  - `ResidentSession`
  - `ResidentConversationGateway`
  - durable resident discovery through `from_evidence()`
  - Grace durable ID and Director of Operations role normalization
- `src/riverview/residents/context.py`
  - `ContextItem`
  - `ContextBundle`
  - `ContextPolicy`
  - `ResidentContextAssembler`
  - bounded layers, classification, provenance, stale-bundle checks, and context budgets
- `src/riverview/residents/persistence.py`
  - resident implementation bindings and continuity persistence
- `src/riverview/reasoning/grace_state.py`
  - authoritative Grace occupant, office, implementation, authority, and context bundle

These are suitable foundations for an office capability package. They do not
currently describe which tools a resident may select while reasoning.

### Resident implementation bindings

Existing implementation:

- `src/riverview/residents/persistence.py`
  - active implementation bindings
  - provider/model/host/device/capability profile references
  - classification eligibility
  - provenance IDs
- `src/riverview/reasoning/binding.py`
  - `CognitionBindingAdapter`
  - provider/resource candidates and binding decisions

These bind HOME cognition to its provider/resource. They are not occupational
capability bindings. A binding says how cognition runs, not what the office can
read or propose.

### HOME Cognition and context assembly

Existing implementation:

- `src/riverview/reasoning/home_cognition.py`
  - `HomeCognitionInvocation`
  - `HomeCognitionService`
  - `HomeCognitionOutcome`
  - typed HOME result and cognition provenance
  - one provider generation after packet assembly
  - advisory-only authority
- `src/riverview/reasoning/home_runtime.py`
  - `build_grace_home_cognition()`
  - `invocation_for_message()`
- `src/riverview/reasoning/context_assembler.py`
  - `ReasoningAssemblyRequest`
  - `ResidentReasoningPacketAssembler`
  - bounded F2 context projection
- `src/riverview/reasoning/cognition_contracts.py`
  - `ResidentReasoningPacket`
  - cognition request/result/session contracts

HOME Cognition currently receives a bounded packet assembled before the model
request. The packet has context references and selected context material, but no
model tool-request field, tool-result continuation contract, capability catalog,
per-tool authorization decision, or bounded multi-step reason/retrieve/reason
loop.

### Character canon and Jessica workflow

Existing implementation:

- `src/riverview/characters/store.py`
  - `CharacterStore.current()`
  - `proposals()`
  - `review()`
  - `steward_review()`
  - `publish()`
- `src/riverview/characters/workflow.py`
  - `CharacterDesignerWorkflow`
  - stages: inspect, propose, independent review, Steward review, publish
- `src/riverview/operator/openwebui.py`
  - authenticated `/api/jessica/character-development`
  - exposes workflow metadata, current character, and proposals to an Operator client

This is an existing governed character-development capability, but it is a
separate HTTP/workflow surface. Conversational Jessica has no resident-scoped
inspection capability bound into her HOME reasoning workspace.

The current live character store also demonstrates why version provenance must
be explicit: the authoritative runtime store contains accepted Grace `v1`; the
Steward-accepted Grace v2 proposal exists with `published_version=v2`, but no
accepted v2 version is present. This audit does not publish it.

### Institutional context, CME, Comms5, and work lifecycle

Existing implementation:

- `src/riverview/reasoning/grace_state.py`
  - bounded registry, subsystem, CME, and capability projection
  - CME meaning: Continuous Momentum Engine
  - capability: `codex.engineering.v1`
- `src/riverview/autonomy/runtime.py`
  - `CMEStatusStore`
  - `ContinuousMomentumRuntime`
- `src/riverview/autonomy/control.py`
  - `GraceMomentum`
  - `ContinuousMomentumEngine`
  - `CapabilityRegistry`
  - execution envelopes and reconciliation primitives
- `src/riverview/mcp/comms5.py`
  - `Comms5Service`
  - read operations including `cme_status`, `seed_lineage`, `objective_status`, `recent_steward_submissions`, `capabilities`, and `resource_policy_status`
  - governed operations including promotion and work formation
- `src/riverview/intake/engineering.py`
  - `EngineeringIntent`
  - `EngineeringIntentStore`
  - typed formation and Steward authority reconciliation
- `src/riverview/runner.py`
  - `RestrictedRunner`
  - named action execution and result reconciliation
- `src/riverview/operator/hermes_projection.py`
  - `read_campaign_runner_snapshot()`
  - bounded work-order projection
- `src/riverview/operator/vnext_projection.py`
  - CME, runtime, conversation, activity, residents, and resource topology read model

These are mostly category B capabilities today: separate control-plane or
Operator functions that Hermes/tests/UI can call, but that a resident cannot
select while reasoning over a novel question.

### Resources and tools

Existing implementation:

- `src/riverview/resources/registry.py`
  - `ExecutionResource`
  - `ResourceRegistry`
  - `ResourcePlanner`
  - observed health/capacity/freshness and eligibility
- `src/riverview/resources/control.py`
  - `ResourcePolicyStore`
  - `SeatClaimStore`
  - `DurableResourcePlanner`
  - durable policy and exclusive claims
- `src/riverview/mcp/comms5.py`
  - read-only resource-policy projection
- `src/riverview/autonomy/control.py`
  - registered capabilities and deterministic dispatch

These describe execution resources and control-plane capability selection. They
do not constitute a resident cognitive tool catalog. In particular, a resource
selection capability must not be confused with permission for Grace or Jessica
to execute work.

### Projections and procedures

Existing projections:

- `/api/vnext/projection`
- `/api/cme/status`
- `/api/runtime/status`
- `/api/activity`
- `/api/residents`
- `read_campaign_runner_snapshot()`
- Comms5 bounded reads
- Jessica character-development projection

Existing procedures/documented contracts include:

- `docs/architecture/RIVERVIEW_GOVERNED_ENGINEERING_EXECUTION.md`
- `docs/operations/GRACE_ENGINEERING_TASK_SUBMISSION_TEMPLATE.md`
- CME/control-plane documents and checkpoints
- Comms5 contract/help/capability descriptions
- character workflow metadata in `JESSICA_CHARACTER_DEVELOPMENT_WORKFLOW`

The procedures exist as documents and workflow implementations, but they are
not currently packaged as office-scoped procedural knowledge selected by HOME
reasoning.

## Grace occupational competence audit

Required current-office competence was derived from current Riverview contracts,
not generic corporate assumptions.

| Capability | Authoritative source | Read/write class | Existing implementation | Currently available to Grace HOME? | Missing seam | Proposed integration |
|---|---|---|---|---|---|---|
| Identity, office, title, authority | PostgreSQL resident continuity; Grace state source | read | `ResidentConversationGateway`; `PostgresAuthoritativeGraceStateSource` | Yes, preassembled | No office package carrying purpose/responsibilities | Include an office package identity anchor and bounded responsibility metadata in `ContextBundle` |
| Current CME state | `CMEStatusStore`; `/api/cme/status` | read | CME runtime and Operator route | Partial; selected CME meaning/status is preassembled | No resident-selectable CME read capability | Expose `cme.status.read` as a read-only role capability with freshness/provenance |
| Active objectives/projects | PostgreSQL objectives and stages; Comms5 `objective_status` | read | `ObjectiveStore`; `Comms5Service.objective_status` | No general list/query available in HOME | No bounded active-objectives projection/query | Add `operations.objectives.read` with bounded filters and explicit snapshot provenance |
| Ready work | PostgreSQL objective stages; Campaign Runner | read | `GraceMomentum.evaluate`; `read_campaign_runner_snapshot` | No | Operator-only snapshot is not a resident tool | Add `operations.ready-work.read` as a derived read projection |
| Blocked work | PostgreSQL stages/work orders/checkpoints | read | Comms5 lineage/status; Campaign Runner projection | No general resident query | No role-scoped blocked-work read surface | Add `operations.blocked-work.read` with checkpoint, owner, dependency, and evidence fields |
| Recent completed work | PostgreSQL work orders/objectives/events | read | partial in lineage/status methods | No | No bounded recent-completion capability | Add `operations.recent-completions.read` with time/count bounds |
| Work orders and progression state | PostgreSQL `work_orders`, stages, Runner projection | read/advice | `read_campaign_runner_snapshot`; `GraceMomentum` | No | No resident-scoped read adapter or reasoning continuation | Add `operations.work-progress.read`; keep mutation outside the read capability |
| Comms5 ingress and lineage | Comms5 PostgreSQL stores and `Comms5Service` | read | `recent_steward_submissions`, `seed_lineage`, `objective_status` | No | Requires bounded resident query selection and protected-payload policy | Add `operations.comms5-lineage.read` and `operations.recent-submissions.read` |
| Steward attention | notification/attention stores and Operator activity | read | `hermes_attention`, activity projection, vNext activity | No | No Grace-scoped attention read tool | Add `operations.steward-attention.read`; return metadata, not protected payloads |
| Resource/capability availability | `ResourceRegistry`, `ResourcePolicyStore`, Comms5 projection | read | `resource_policy_status`; `CapabilityRegistry` | Partial; only selected capability references appear in context | No resident tool to query current availability/freshness | Add `operations.capability-availability.read`; never expose credentials |
| Resident/office responsibility | durable resident registry and context projection | read | `ResidentConversationGateway.residents`; registry context | Partial; selected names/roles only | No query by responsibility or capability suitability | Add `operations.responsibility-registry.read` with explicit suitability evidence |
| Work lifecycle procedure | governed engineering docs, Comms5 and Runner contracts | advise | documents and control-plane implementations | Partial; prose is not dynamically selected office knowledge | No typed office playbook references and procedure retrieval | Add bounded `professional_methods` package references and procedure read capability |
| Governed engineering proposal formation | Steward authority, Comms5, `EngineeringIntentStore` | propose; execution separately gated | `DirectGraceFormation`; `EngineeringIntentStore.form_and_enqueue`; Comms5 `form_and_queue_work` | Not as a generic resident-selected capability | No model-to-capability proposal request contract; authority source must remain separate | Add `operations.form-proposal.prepare` as advisory/typed proposal only; require existing Steward-gated formation for mutation |
| Execute work | Steward authority, Runner, named Codex action | execute | `RestrictedRunner`, Relay, Codex adapter | Correctly not directly available | Resident cognition must not acquire execution authority | Keep outside HOME read/proposal workspace; expose only status and proposal preflight |
| Explain operational state | all above read projections + HOME reasoning | advise | HOME can reason only over supplied packet | Partial and fragile | Missing dynamic retrieval loop | Tool result must return to HOME for a second reasoning pass, then claim/authority validation |

### Grace conclusion

Grace currently has identity and selected context, not occupational competence. The
most important missing package is a bounded Operations Workspace containing read
capabilities for current work, CME, Comms5 lineage, attention, resources,
responsibility, and procedures. Proposal formation must be a separate capability
with existing Steward-gated authority consumption; it must not be silently
combined with read access or execution.

## Jessica occupational competence audit

| Capability | Authoritative source | Read/write class | Existing implementation | Currently available to conversational Jessica? | Missing seam | Proposed integration |
|---|---|---|---|---|---|---|
| Inspect current accepted character | `CharacterStore.current()` | read | `CharacterDesignerWorkflow.inspect`; `/api/jessica/character-development` | No, separate authenticated route only | No resident-scoped character inspection capability | Add `character.canon.read` to Jessica workspace |
| Inspect versions and version provenance | `CharacterStore.data["versions"]` and accepted-state rules | read | `CharacterStore.current`; store data | No | No bounded version-history read operation | Add `character.versions.read` with identity/version/status/source evidence |
| Inspect proposals | `CharacterStore.proposals()` | read | workflow/store and Jessica route | No | No HOME tool binding | Add `character.proposals.read` with bounded proposal fields |
| Inspect review/publication status | Character store proposal lifecycle | read | `review`, `steward_review`, `publish` | No | No resident tool or typed result | Add `character.review-status.read`; publication remains unavailable to HOME |
| Inspect behavioral evidence | proposal source evidence and durable observation projections | read | evidence references exist; no unified character-evidence reader | No | Missing bounded observation/evidence projection | Add `character.observations.read` with evidence class and provenance |
| Distinguish canon/proposal/observation/Steward direction/unknown | store statuses, evidence refs, source classes | advise | fields exist but not composed for cognition | No | No typed evidence taxonomy in resident workspace | Add source-classed result schema and grounding policy |
| Discuss character gaps | current canon + evidence + uncertainty | advise | workflow supports inspection/proposal outside chat | No | No retrieve-then-reason path | HOME must receive read result and reason over it |
| Form bounded proposal | `CharacterDesignerWorkflow.propose` | propose | existing workflow | No | No resident-scoped proposal preparation capability | Add `character.proposal.prepare`; persist only through existing workflow boundary |
| Independent review | workflow/store review methods | separate governed stage | existing workflow | No, and should not self-review | No explicit role/person separation in resident workspace | Expose status/next-stage information only; retain independent reviewer boundary |
| Steward review | workflow/store Steward review | Steward-gated | existing workflow | No, correctly | No need to give conversational Jessica publication authority | Keep outside HOME tool set |
| Publish | `CharacterStore.publish()` | canon mutation | existing workflow | No, correctly | No missing resident authority; this is an intentional boundary | Keep only in governed workflow, never a generic cognitive tool |
| Maintain target-resident continuity | `ContinuityStore`, character target IDs | read/propose context | existing stores/workflow | Partial | No target binding carried into conversational Jessica context | Add target resident ID and source lineage to workspace binding |
| Avoid invented biography | authoritative current canon and typed unknown | safety/grounding | no general conversational character reader | No | No canon-read tool means model fills gaps from priors | Require canon read result and explicit unknown state before character claims |

### Jessica conclusion

Jessica has a governed character-development workflow, but conversational Jessica
cannot use it as cognitive workspace capability. The workflow is category B today.
The correct integration is not to give chat direct publication access. It is to give
HOME a read-only, target-bound character inspection capability and a separately
governed proposal-preparation capability. Review and publish remain outside the
resident's ordinary reasoning authority.

## Current model-selected tool-use answer

Model-selected bounded tool use does not currently exist in HOME Cognition.

Evidence:

- `HomeCognitionInvocation` has no tool-request/tool-result field;
- `HomeCognitionService.execute()` assembles one `ResidentReasoningPacket`, evaluates HOME policy, binds one cognition request, selects the already-authorized provider/resource, and performs one provider generation;
- `ReasoningAssemblyRequest` and `ResidentReasoningPacket` contain bounded context but no capability catalog or continuation turn;
- `AuthorizedHomeProvider` accepts a callable that returns one `ReasoningResponse`; it is not a tool broker;
- existing `CapabilityRegistry` and `ResourceRegistry` select execution providers/resources, not resident read tools;
- existing Comms5 operations and Jessica workflow endpoints are not exposed as resident cognitive tools;
- speech composition is downstream of the one cognition result.

Therefore the architecture is currently:

```text
preassemble -> one Qwen call -> validate -> speak
```

not:

```text
reason -> select role capability -> retrieve -> reason -> validate -> speak
```

This is the deeper defect behind occupational incompetence.

## Functionality currently outside resident cognition

| Existing capability | Current location | Category | Resident can invoke while reasoning? |
|---|---|---|---|
| CME status | `CMEStatusStore`, `/api/cme/status`, vNext projection | B: separate runtime/operator read | No |
| Active objective/stage status | `ObjectiveStore`, Comms5 `objective_status` | B: separate known-ID control-plane read | No generic query |
| Seed/Comms5 lineage | `Comms5Service.seed_lineage` | B: separate MCP operation | No |
| Recent Steward submissions | `Comms5Service.recent_steward_submissions` | B: separate MCP operation | No |
| Current work-order snapshot | `read_campaign_runner_snapshot` | B: operator projection/helper | No |
| Resource policy/capacity | `ResourcePolicyStore`, `ResourceRegistry`, Comms5 projection | B: control-plane/resource read | No |
| Engineering proposal formation | `DirectGraceFormation`, Comms5, `EngineeringIntentStore` | B: governed workflow | No generic HOME selection; execution remains separately gated |
| Codex execution | Runner/Relay/Codex adapter | B: execution workflow | No, intentionally |
| Character current/proposals/reviews | `CharacterStore`, `CharacterDesignerWorkflow` | B: governed character workflow | No |
| Jessica workflow inspection | `/api/jessica/character-development` | B: authenticated Operator route | No |
| Resident registry | `ResidentConversationGateway.residents`, context projection | A/B: preassembled in some Grace packets, not queryable | Only selected bounded material |
| Grace identity/authority | Grace state source and gateway | A: preassembled HOME anchor | Yes, but identity is not occupational capability |
| Procedures/playbooks | docs and workflow metadata | B: documentation/control-plane | No dynamic office-method retrieval |
| Conversation continuity | gateway, `ContinuityStore`, HOME session | A: bounded context/history | Yes, but continuity is not work competence |

The excess of category B explains why automated tests and separate workflows can
succeed while residents still behave like title-aware chatbots.

## Proposed resident-office-capability architecture

### Reuse existing models; do not create a competing authority system

The proposed package should be a derived, versioned workspace projection, not a
new source of truth. It should reuse:

- `ResidentProfile`, durable occupant/office IDs, and `ContextBundle` for identity and context;
- `ContextItem` provenance/classification/budget semantics;
- `resident_implementation_bindings` for implementation/capability binding lineage;
- `CapabilityRegistry` and `ResourceRegistry` for named capability/resource metadata, without conflating them with resident authority;
- Comms5 operation descriptions and existing read methods as adapter handlers;
- `CMEStatusStore` and existing read projections;
- `CharacterStore` and `CharacterDesignerWorkflow` as the character authority;
- `EngineeringIntentStore`, Comms5 formation, Relay, and Runner for governed proposal/execution boundaries;
- `CognitionBindingAdapter`, HOME request/result/session/provenance contracts;
- existing claim grounding and speech validation;
- `OperatorProjection`/vNext projection for derived visibility only.

### Package shape

A resident office capability package should contain:

```text
ResidentOfficeCapabilityPackage
  package_id / package_version
  resident_id / occupant_id / office_id / implementation_id
  role_identity
    title
    purpose
    responsibilities
  domain_knowledge_refs
    bounded ContextItem/source references
  read_capabilities[]
    capability_id/version
    operation/schema
    handler/source
    classification
    freshness bound
    result budget
    evidence requirements
  proposal_capabilities[]
    typed preparation operation
    required authority class
    no-execution policy
  procedures[]
    playbook/reference IDs
    applicability metadata
  authority_boundaries
    read
    advise
    propose
    execute
    required external approvals
  grounding_policy
  privacy/egress policy
  provenance/version/freshness
```

This package is a derived capability contract. PostgreSQL stores, CharacterStore,
Comms5, CME, and workflow stores remain authoritative for their own domains.

### Runtime path

```text
Steward asks novel job-related question
  -> resident session binds resident + office package
    -> HOME cognition receives package catalog, not all data
      -> model emits typed bounded capability request or final reasoning result
        -> resident capability broker validates package, classification, scope, freshness, and authority
          -> named read/proposal handler executes through existing authoritative adapter
            -> typed result returns with source/evidence/correlation
              -> HOME cognition receives result for bounded second reasoning pass
                -> typed claims/authority validation
                  -> natural speech + durable provenance
```

Required safeguards:

- no arbitrary SQL, shell, filesystem, or provider calls;
- package allowlist is authoritative for resident capability selection;
- capability handler owns its schema, limits, classification, and provenance;
- reads do not imply mutation;
- proposal preparation does not imply approval, enqueue, or execution;
- publication and Steward review remain separate workflow transitions;
- tool calls and results carry resident, office, implementation, correlation,
  cognition request/session, capability, source, freshness, and authority metadata;
- maximum tool calls and total budget are bounded;
- stale or unavailable results are explicit unknowns;
- institutional claims are grounded after the second reasoning pass;
- internal cognition envelopes never render directly as speech;
- private character impressions remain structured and out of resident-facing speech.

### Minimum missing contracts

The following are absent and require design approval before implementation:

1. A versioned resident-tool request/result schema and continuation contract.
2. A resident capability broker that binds the request to the office package.
3. A package authority/ownership model: who publishes office capability packages,
   and how package versions become active without becoming character canon.
4. Read-surface schemas for active/ready/blocked/recent work and character evidence.
5. A tool-call budget, timeout, freshness, classification, and retry policy.
6. A result-to-HOME continuation contract that preserves packet digest and
   provenance across multiple reasoning passes.
7. Deterministic claim grounding rules for tool-derived institutional assertions.
8. An operator projection showing selected capability, result source, freshness,
   and failure without exposing protected payloads.
9. Negative-path semantics for unavailable capability, stale result, denied
   authority, malformed tool request, tool timeout, contradictory source, and
   provider failure after a successful read.

These are architecture-level contracts. Adding them implicitly through a
speech-case patch would create an unreviewed second authority/tool system.

## Proposed vertical slices

### Grace slice: current active work

Capability package entry:

```text
operations.current-work.read
```

Expected behavior:

1. HOME identifies a current operational-state question.
2. Model selects the named read capability from the Grace package.
3. Broker validates Grace identity, office, classification, read-only authority,
   freshness, and bounded result size.
4. Adapter reads the existing objective/stage/work-order projection.
5. Result returns active/ready/blocked/recent state with evidence references.
6. HOME reasons over the result and answers naturally.

No work mutation or execution is permitted in this slice.

### Jessica slice: established Grace canon facts

Capability package entry:

```text
character.canon.read
```

Expected behavior:

1. HOME identifies a canon/fact question about a target resident.
2. Model selects `character.canon.read` from Jessica's package.
3. Broker validates target resident, source class, read-only authority, and
   bounded payload policy.
4. Adapter reads `CharacterStore.current()` for the exact durable target ID,
   returning accepted version, identity, role, traits/speech fields, and source evidence.
5. HOME distinguishes established canon from proposal, observation, Steward
   direction, and unknown.
6. Speech is composed only from grounded result; unsupported biography remains unknown.

Proposal preparation can be a later bounded capability. Independent review,
Steward review, and publish remain outside ordinary HOME tool access.

## Why the prototype is not implemented in this tranche

The requested slices cannot be implemented safely as a bounded extension of the
current HOME contracts without choosing the missing tool-request protocol,
package ownership, result continuation semantics, and authoritative read schemas.
Those choices would create a new resident capability architecture and therefore
require a design decision rather than autonomous incremental patching.

Implementing the slices as direct phrase checks, direct endpoint calls selected
by the server, or extra fallback branches would fail the stated success criterion:
it would create another phrase/state machine and would not prove model-selected
role capability.

No prototype code was added in this audit. No new capability, tool, authority,
character state, proposal, workflow, or runtime route was created.

## Generalization test status

The requested Grace and Jessica novel-question tests were not claimed as green.
They are blocked at the missing capability-broker boundary:

- Grace cannot currently select a current-work projection from HOME;
- Jessica cannot currently select a canon inspection operation from HOME;
- paraphrases therefore cannot demonstrate generic model-selected access;
- existing direct Operator/Comms5/workflow calls would test category B endpoints,
  not resident occupational cognition.

This is an architectural blocker, not a runtime failure and not a reason to add
more phrase-specific cases.

## 4090 / model / tool / model proof status

Current live proof establishes:

- HOME Cognition invoked for Grace conversation;
- Qwen model: `qwen3-coder:30b-qwencode-20k`;
- provider: `ollama`;
- HOME service: `HomeCognitionService`;
- local resource class in the existing binding/provenance path: `local:RTX4090`;
- typed cognition request/session/result and correlation provenance;
- deterministic downstream speech/claim validation.

It does not establish model-selected occupational tool use, because no resident
capability request was emitted and no tool-result continuation exists.

## No phrase-specific state machine

No phrase-specific state machine, additional conversational case, Grace/Jessica
character tuning, character publication, or capability-specific speech patch was
added in this tranche.

The prior bounded speech-recovery changes remain unchanged. This audit does not
extend them.

## Recommended design decision for Steward review

Approve or reject the following architecture before implementation:

> Riverview resident occupational competence is represented by a derived,
> versioned Resident Office Capability Package bound to durable resident,
> occupant, office, implementation, classification, and authority identities.
> HOME Cognition may select only package-allowlisted named capabilities through
> a bounded broker. Read/proposal handlers reuse existing authoritative
> projections and workflows. Tool results return to HOME for a bounded second
> reasoning pass. Claims and speech are validated afterward. Capability does
> not imply authority; proposal preparation does not imply approval; execution,
> character publication, independent review, Steward review, and acceptance
> remain separate governed transitions.

If approved, the first implementation should be two read-only vertical slices:

- Grace: `operations.current-work.read`;
- Jessica: `character.canon.read`.

The first implementation should include paraphrase tests, tool denial/staleness
negative tests, result provenance, bounded continuation, and live model/tool/model
proof. It should not publish Grace v2, change character canon, involve Jessica in
character authoring, or add direct execution authority to either resident.

## Boundary

Technical outcome: architecture audit and evidence-backed design proposal complete.  
Prototype outcome: not implemented; blocked by missing design-level contracts.  
Runtime outcome: existing managed runtime remains healthy; no lifecycle work opened.  
Institutional acceptance: not claimed.  
Steward decision required: approve the resident-office-capability package/tool-broker design.
