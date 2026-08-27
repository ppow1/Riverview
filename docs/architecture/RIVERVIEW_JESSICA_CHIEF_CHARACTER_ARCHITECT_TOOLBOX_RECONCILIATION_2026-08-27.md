# Jessica — Chief Character Architect Toolbox Reconciliation

Date: 2026-08-27
Status: FORENSIC AUDIT / STEWARD REVIEW
Scope: promised vs designed vs built vs resident-available
Implementation in this tranche: none

## Executive finding

Riverview explicitly intended Jessica to be a professional Chief Character
Architect, not a generic role-play chatbot or CRUD record editor. The durable
resident-localization roadmap and work packages assign her a professional corpus
covering character identity, continuity, behavior, relationships, cognition,
voice/mannerism, methods, evidence, validation, character bibles, and visual
canon where evidenced.

The current implementation contains a valid but narrower governed workflow:

```text
CharacterStore
  -> CharacterDesignerWorkflow
    -> /api/jessica/character-development
      -> inspect / propose / independent review / Steward review / publish
```

That workflow is available to an authenticated Operator/Hermes client. It is not
available to conversational Jessica during HOME reasoning. The resident can
state her title but cannot inspect the character corpus, classify canon versus
proposal versus observation, or use the existing workflow as a bounded cognitive
tool.

## Durable promise reconstruction

### Resident-localization roadmap

`docs/architecture/riverview_resident_localization_master_roadmap.md` states:

- Riverview is not building a collection of chatbots;
- Jessica is the first tenant of a reusable resident/officeholder continuity
  substrate;
- Office, Occupant, Implementation, and State are separate;
- Riverview must recover Jessica's institutional continuity, professional
  history, reasoning methods, relationships, accepted work, reflections, and
  durable identity;
- future residents must support different cognition, memory, privacy, authority,
  and execution patterns;
- Tranche E is explicitly for Jessica professional capability recovery;
- Tranche E includes professional doctrine, identity design methods,
  relationship/cognition/behavior/continuity methods, visual canon, and
  character-bible method recovery.

The same roadmap defers surname, biography, backstory, physical identity, visual
canon, expanded personality canon, and personal-history details until supported
by later evidence. That is a boundary against invention, not an absence of
professional responsibility.

### Tranche 0/A work packages

`docs/work_packages/resident_localization_tranche_0_A_work_packages.md` requires:

- an Office of Character Architecture source inventory;
- officeholder continuity evidence separate from office doctrine;
- professional reasoning patterns, collaboration style, lessons, relationships,
  decisions, strengths/weaknesses, and implementation handoffs;
- a professional corpus including Evelyn identity/visual-canon campaigns,
  character-bible methods, physical/visual canon methodology, voice/mannerism/
  behavior work, relationship/cognition methods, identity/continuity methods,
  validation/recognizability, prompt/reasoning/review techniques, and completed
  versus exploratory work;
- explicit classification of missing evidence;
- no invented biography, visual identity, surname, or backstory.

### Jessica residency roadmap

`docs/operations/roadmap/JESSICA_RESIDENCY_ROADMAP_TRANCHE_F_FORWARD.md` requires:

- continuity validation in a fresh session;
- a real Character Architecture assignment, not documentation recitation;
- distinction between canon, historical evidence, provenance, uncertainty,
  supersession, contradiction, and unresolved material;
- self-governance and authority validation;
- an Operator-facing resident home;
- rehydration with correct office, professional capability, authority, relevant
  continuity, and current work;
- later resident-to-system operations involving character, continuity,
  visual/voice systems, reasoning escalation, and other residents.

### Historical commits

Relevant durable history:

- `64ab496` — Complete Riverview resident gateway and character-development parity
- `f9a4f13` — add Jessica character development surface
- `4c68a2b` — enforce Jessica review stages
- `54747e6` — document Jessica residency roadmap from Tranche F forward
- `42cf32d` — add Jessica localization campaign execution spec
- `67329ce` — add resident localization master roadmap
- `7e5e93c` — add direct Codex execution profile for Jessica campaign
- `7fa78a2` — integrate bounded Hermes Campaign Runner

These commits prove the intent was durable and staged. They do not prove that
conversational Jessica was connected to the workflow.

## Jessica toolbox ledger

| Capability | Promised? | Evidence | Designed? | Built? | Bounded interface exists? | Available to conversational Jessica? | Model-selectable? | Authority class | Status | Gap | Recovery effort |
|---|---|---|---|---|---|---|---|---|---|---|
| Stable Jessica identity/title | YES | localization roadmap §§2–3, G–H | YES | YES | gateway and Operator route | YES for identity only | NO | READ | EXISTS + WIRED for identity | Identity is not competence | Low |
| Office purpose/responsibilities | YES | Tranche E; JCA roadmap; work packages | YES | PARTIAL | workflow metadata and documents | PARTIAL static context | NO | ADVISE | PROMISED/DESIGNED + PARTIAL IMPLEMENTATION | No professional doctrine package | Medium |
| Current accepted character | YES | JCA-028; Tranche B–D | YES | YES | `CharacterDesignerWorkflow.inspect`; `/api/jessica/character-development` | NO in HOME | NO | READ | EXISTS + NOT WIRED | No target-bound resident canon read | Medium |
| Character versions/provenance | YES | provenance rules; `CharacterStore` | YES | YES store fields | route returns current/proposals | NO conversationally | NO | READ | EXISTS + NOT WIRED | No bounded version-history reader | Medium |
| Traits and speech | YES | character store and Tranche E | YES | YES storage | current record/route | NO conversationally | NO | READ/ADVISE | EXISTS + NOT WIRED | No cognition projection | Medium |
| Biography/backstory | YES as an investigated/validated domain; not automatic fact | roadmap defers unsupported details; JCA evidence rules | YES boundary | PARTIAL storage only | no dedicated evidence reader | NO | NO | READ/ADVISE | PROMISED/DESIGNED + IMPLEMENTATION MISSING for retrieval | Must return explicit unknown, never invent | High |
| Emotional/personality state | YES bounded and evidence-dependent | roadmap relationship/cognition/behavior methods; current proposals | PARTIAL | PARTIAL proposal fields | no current-state resident reader | NO | NO | ADVISE/PROPOSE | DATA/SERVICE EXISTS + ADAPTER MISSING | Proposal and continuity not cognitive tools | High |
| Behavioral observations | YES | JCA-002/003/028; source-evidence rules | YES | PARTIAL refs/diagnostics | no unified character observation projection | NO | NO | READ/ADVISE | PROMISED/DESIGNED + IMPLEMENTATION MISSING | Need typed evidence-class reader | High |
| Relationship/interpersonal continuity | YES as structured bounded continuity | roadmap §§2, 5.3; JCA-002/003 | YES | PARTIAL continuity primitives | no target-specific professional reader | NO | NO | READ/ADVISE/PROPOSE | PROMISED/DESIGNED + PARTIAL | Must preserve privacy and uncertainty | High |
| Character Architecture methods | YES | Tranche E; WP-JCA-003 | YES | PARTIAL documents/corpus references | no retrieval adapter | NO | NO | READ/ADVISE | PROMISED/DESIGNED + IMPLEMENTATION MISSING | Corpus needs indexed bounded retrieval | High |
| Character proposals | YES | workflow and JCA-009 | YES | YES `CharacterDesignerWorkflow.propose` | route/workflow | NO conversationally | NO | PROPOSE | EXISTS + NOT WIRED | Proposal-preparation tool absent | Medium |
| Independent review | YES | workflow stages; `4c68a2b` | YES | YES `review` | workflow method | Correctly not self-authorized | NO | REVIEW | EXISTS + NOT WIRED | Status may be exposed; review remains separate | Medium |
| Steward review | YES | workflow stages; roadmap JCA-030 | YES | YES `steward_review` | workflow method | Correctly unavailable | NO | REVIEW | EXISTS + NOT WIRED | No missing resident authority | None |
| Publish | YES as final governed transition | `CharacterStore.publish`; roadmap | YES | YES | workflow method | Correctly unavailable | NO | PUBLISH | EXISTS + NOT WIRED by design | Must remain outside ordinary HOME | None |
| Canon/proposal/observation distinction | YES | provenance classes; JCA-028 | YES | PARTIAL statuses/source refs | no typed unified result | NO | NO | READ/ADVISE | DESIGNED + PARTIAL | Need evidence-class result schema | High |
| Target-resident continuity | YES | Office/Occupant/Implementation/State invariant; JCA-002 | YES | PARTIAL IDs/continuity store | character route accepts target alias | NO HOME target binding | NO | READ/PROPOSE | EXISTS + NOT WIRED | Durable target ID must enter cognition workspace | Medium |
| Canon comparison/diff | PARTIAL/likely required by versioned design | versioned store and roadmap evidence | PARTIAL | NO dedicated diff method found | NO | NO | NO | READ/ADVISE | PROMISED/DESIGNED + IMPLEMENTATION MISSING | Add bounded version comparison later |
| Historical/draft material | YES as classified evidence | JCA-001–005; provenance taxonomy | YES | PARTIAL documents/proposals | no bounded corpus projection | NO | NO | READ | PROMISED/DESIGNED + IMPLEMENTATION MISSING | Need source-classed retrieval |
| Unknown/not-established state | YES | roadmap no-invention rules; JCA acceptance | YES | PARTIAL policy only | no canon reader to establish unknowns | NO | NO | ADVISE | DESIGNED + NOT WIRED | Canon read must return explicit absence |
| Visual canon ownership | YES as professional recovery target | Tranche E; WP-JCA-003; WP-JCA-024 | PARTIAL | NO complete current canon found | NO authoritative visual-canon reader | NO | NO | READ/PROPOSE/REVIEW/PUBLISH | PROMISED/DESIGNED + IMPLEMENTATION MISSING | Separate visual-canon design and corpus recovery |
| Reference images/concept art | PARTIAL/future where evidenced | visual-canon roadmap references; no current registry found | AMBIGUOUS | NO complete current implementation found | NO | NO | NO | READ/PROPOSE | AMBIGUOUS | Need source archaeology before design |
| Visual generation | PARTIAL/future | roadmap/parking-lot/Spatial references, no accepted current pipeline | AMBIGUOUS | NO complete Riverview implementation found | NO | NO | NO | PROPOSE/EXECUTE separately | PROMISED/DESIGNED + IMPLEMENTATION MISSING or AMBIGUOUS | Do not assume ComfyUI is connected |
| Visual approval/appearance consistency | PARTIAL/future | visual canon and acceptance intent | PARTIAL | NO complete implementation found | NO | NO | NO | REVIEW/PUBLISH | AMBIGUOUS | Requires later explicit workflow |
| Resident-to-system operations | YES later | Jessica roadmap Tranches I–L | PLANNED | NO | NO | NO | NO | READ/ADVISE/PROPOSE | PROMISED/DESIGNED + IMPLEMENTATION MISSING | Later residency tranche |

## Existing Jessica workflow versus conversational Jessica

### What the workflow can do

`CharacterDesignerWorkflow` currently supports:

- inspect accepted current character;
- create a proposal with source evidence and rationale;
- reject authority/identity replacement fields;
- require independent review;
- require separate Steward review;
- publish only an accepted proposal;
- preserve version and prior-version lineage.

The authenticated `/api/jessica/character-development` route exposes workflow
metadata, target Grace metadata, current character, and proposals.

### What conversational Jessica can do

The current resident conversation path provides identity/role context and one
HOME/model generation, but no call into the workflow or a bounded character-read
adapter. Therefore conversational Jessica cannot use the workflow she is
supposed to embody.

The separation appears accidental/architectural rather than a deliberate
occupational boundary: publication and review should remain separate, but
inspection and discussion are clearly required by JCA-027/028 and should be
resident-available as read capabilities.

### Why acceptance missed it

Workflow acceptance proved:

- record CRUD/lifecycle behavior;
- review-stage separation;
- publish guards;
- source evidence and rationale persistence.

It did not prove:

```text
Jessica asks a novel canon question
 -> selects a bounded canon/evidence read
 -> receives authoritative result
 -> distinguishes canon from unknown/proposal/observation
 -> answers naturally
```

The endpoint was mistaken for resident access, and no acceptance gate required
conversational Jessica to invoke it herself.

## Visual-canon audit

### Explicitly supported by durable intent

The resident-localization roadmap and Tranche E work packages explicitly include:

- visual canon and character-bible method recovery;
- physical/visual canon methodology;
- identity/recognizability validation;
- visual/voice systems in later resident operations;
- Evelyn visual-canon work as evidence of Jessica's professional corpus.

This establishes visual-canon responsibility as a professional recovery target.

### Current implementation found

Current Riverview contains:

- character identity/version/proposal/review/publish storage;
- character workflow metadata;
- visual/spatial project materials and future environment work;
- references to visual/character work in roadmap and work-package documents.

The audit did not find a complete authoritative current visual-canon schema with:

- accepted appearance record;
- reference-image registry;
- image provenance and approval state;
- concept-art version lineage;
- appearance consistency validator;
- resident-connected visual retrieval;
- proven ComfyUI character-generation adapter;
- accepted character-to-Spatial visual embodiment pipeline.

Therefore visual-canon status is `PROMISED/DESIGNED + IMPLEMENTATION MISSING` for
the professional recovery target, with individual historical/concept artifacts
remaining `AMBIGUOUS` until the source inventory is completed.

Jessica would need, at minimum:

1. an authoritative visual-canon record/version model;
2. classified reference-image/artifact metadata;
3. provenance and approval state;
4. bounded visual evidence retrieval;
5. a proposal/review/publish path separate from generation;
6. appearance-consistency validation;
7. explicit local image-generation/provider boundaries if generation is later
   authorized;
8. a resident capability binding so Jessica can inspect and reason over visual
   state rather than merely link to a separate UI.

## Development-context and runtime-context diagnosis

The development requirement was not lost solely in conversation. It is preserved
in the roadmap, work packages, execution specification, character workflow
history, and residency roadmap.

The runtime problem is capability access, not only token budget. Jessica has no
model-selected bounded character retrieval path. Increasing Qwen context length
would not create canon/proposal/observation classification, provenance, target
binding, or review authority.

## Recommended recovery

1. Steward accepts the cross-cutting resident occupational-capability invariant.
2. Define a target-bound, read-only `character.canon.read` capability using
   `CharacterStore` and source-classed evidence results.
3. Bind it to Jessica's resident workspace, not only `/api/jessica/...`.
4. Add bounded proposal preparation later, while retaining independent review,
   Steward review, and publish as separate workflow stages.
5. Recover/index the professional Character Architecture corpus and Cookbook
   references with provenance and classification.
6. Treat visual canon as a separate later design/corpus tranche; do not infer
   images or biography from role-play output.
7. Test Jessica on novel paraphrases involving canon, proposal state, evidence,
   unknowns, and target residents.

## Boundary

- Audit/documentation only.
- No Jessica workflow invocation.
- No character change.
- No canon publication.
- No visual asset generation.
- No resident capability broker.
- No model tool calling.
- No runtime change.
