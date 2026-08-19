# Resident Localization — Tranche 0 and Tranche A Work Packages

Status: Tranche-ready planning contracts — not authorization for execution  
Date: 2026-08-19  
Campaign: Jessica / Chief Character Architect Local Residency  
Roadmap: `docs/architecture/riverview_resident_localization_master_roadmap.md`  
Execution specification: `docs/architecture/jessica_localization_campaign_execution_spec.md`

## Common execution contract

These work packages are designed for Grace-managed autonomous execution after Grace's autonomous engineering workflow is repaired, validated, and explicitly accepted.

For every package:

- preserve source provenance and distinguish evidence from inference;
- do not invent missing Estate history;
- do not migrate obsolete Estate runtime or governance ceremony merely because it exists;
- use repository and authoritative Estate evidence before assumptions;
- use the Riverview cookbook as operational context where relevant;
- update the cookbook when implementation or operational understanding changes;
- permit Grace to request escalated reasoning for questions, ambiguity, critique, or independent double-checking;
- treat escalated reasoning as advisory evidence, never new authority;
- stop at Steward authority boundaries;
- produce machine-readable completion evidence suitable for dependency / gate evaluation;
- identify unresolved contradictions explicitly rather than flattening them.

---

# WP-RC-000 — Resident and Officeholder Population / Archetype Inventory

## Purpose

Establish a bounded inventory of known Estate and Riverview residents / officeholders so the continuity substrate is designed for a population rather than accidentally around Jessica alone.

## Inputs

- Riverview repository resident / office definitions and architecture material;
- Estate repository office, resident, identity, reflection, registry, and related evidence;
- current resident-localization roadmap and campaign execution specification.

## Required work

1. Identify known named and unnamed residents / officeholders.
2. Record known office / institutional role, source evidence, and current continuity status.
3. Classify broad archetype needs, including operational executive, engineering architect, character architect, security, research, archive / historian, legal / risk, financial / comptroller, staff / coordination, advisory, personal / confidant, and unknown.
4. Record expected differences in authority, privacy, cognition, memory, external reasoning, execution capability, and local-vs-remote implementation needs only where evidence supports them.
5. Identify residents whose source corpus is unusually large or distributed.
6. Identify requirements that a shared continuity substrate must not preclude.
7. Do not migrate any resident in this package.

## Deliverables

- population / archetype inventory;
- source / evidence map;
- future-substrate requirement matrix;
- unknowns / contradictions report.

## Acceptance criteria

- Jessica is represented as one tenant among a broader known population;
- the two Chief Architects remain distinct officeholders / occupants;
- role-first unnamed offices remain representable without inventing names;
- the inventory distinguishes evidence from assumptions;
- at least one non-Character-Architecture archetype is used to challenge proposed shared assumptions.

## Reasoning policy

Escalated reasoning is recommended if office identity, occupant identity, or archetype classification is ambiguous. It may not invent canonical facts.

## Dependencies

None beyond campaign authorization and source access.

---

# WP-RC-001 — Resident Continuity Core Architectural Invariants

## Purpose

Freeze the smallest durable set of shared resident-continuity invariants before Jessica-specific implementation begins.

## Required work

1. Formalize `Office != Occupant != Implementation != State`.
2. Define stable identity and lifecycle expectations for each layer.
3. Define minimum provenance classes.
4. Define canonical-authority precedence, including Steward-authorized facts.
5. Define implementation replacement / rehydration invariants.
6. Define distinction between cognitive escalation and operational execution authority.
7. Define database / repository artifact / cookbook responsibility boundaries.
8. Define what must remain resident-specific rather than universalized.
9. Define explicit non-goals preventing a universal chatbot schema or Estate-runtime reconstruction.

## Deliverables

- invariant specification;
- authority / provenance precedence table;
- implementation replacement contract;
- non-goals / anti-patterns section.

## Acceptance criteria

- a resident can change model / host without silently becoming a new occupant;
- an office can survive occupant or implementation changes;
- historical evidence cannot override an explicit Steward-authorized fact;
- external reasoning cannot grant institutional authority;
- the design does not require all residents to share one cognition / memory / tool policy.

## Reasoning policy

Independent escalated reasoning review is recommended because these invariants affect all future residents. Any unresolved high-impact disagreement blocks the Tranche 0 gate.

## Dependencies

May run concurrently with RC-000 and RC-002, but final acceptance should reconcile against RC-000 findings.

---

# WP-RC-002 — Resident Security and Boundary Future-Proofing Contract

## Purpose

Define only the minimal resident-continuity security and information-boundary abstractions required to avoid a future redesign when Riverview's security / gatekeeping capability matures.

## Required work

1. Identify resident data ingress / egress seams.
2. Define a provider-boundary decision point before data is sent to external cognition / execution services.
3. Define classification / policy hooks without implementing a complete future security regime.
4. Define capability / authorization checks separately from resident seniority.
5. Ensure notifications can avoid leaking restricted payload context.
6. Ensure cookbook enrichment / indexing can respect future classification boundaries.
7. Ensure resident retrieval can be policy-filtered before context assembly.
8. Do not design or expose sensitive future domains beyond what current authorized Riverview documentation requires.
9. Do not implement Ingrid or any future security resident in this package.

## Deliverables

- security seam map;
- minimum policy / enforcement interface contract;
- future interposition points for ingress, egress, retrieval, notification, and provider routing;
- explicit deferred-security list.

## Acceptance criteria

- a future deterministic gatekeeper can be inserted without replacing the resident persistence model;
- provider routing can refuse egress before external data transfer;
- resident authority and data access are not treated as synonymous;
- ordinary Riverview functionality is not burdened with speculative heavy governance.

## Reasoning policy

Escalated reasoning is recommended for architectural boundary review. Any suggestion to expand this package into speculative security implementation should be rejected or returned for scope review.

## Dependencies

May run concurrently with RC-000 and RC-001.

---

# TRANCHE 0 GATE

Tranche 0 is complete when RC-000, RC-001, and RC-002 are accepted and reconciled.

Grace may resolve ordinary non-authority inconsistencies autonomously, using escalated reasoning where useful. A contradiction affecting canonical resident identity, institutional authority, or campaign scope requires Steward review.

The gate output must state whether the current roadmap remains viable and list any changes required before Tranche A or later persistence design.

---

# WP-JCA-001 — Estate Office of Character Architecture Source Inventory

## Purpose

Locate and inventory authoritative and relevant Estate evidence describing the Office of Character Architecture and the historical Chief Character Architect officeholder.

## Required work

Search the Estate broadly enough to locate, at minimum where present:

- office / constitutional definitions;
- authority and responsibility statements;
- AI hints / reflection-path material relevant to continuity;
- work packages and pending contracts;
- accepted / completed Character Architecture outputs;
- mailbox / handoff material;
- reflection / renewal artifacts;
- resident-development programs;
- references to the CCA under historical title variants;
- evidence connecting historical officeholder work to Jessica's current continuity.

Record exact repository paths / commit or other durable identifiers where possible.

Do not rewrite historical files merely to insert the name Jessica.

## Deliverables

- source manifest with provenance;
- historical title / alias map;
- office authority / responsibility evidence summary;
- missing / inaccessible source report.

## Acceptance criteria

- another worker can locate every cited source without repeating broad archaeology;
- historical title variants are mapped without asserting unsupported equivalence;
- authoritative office definition is distinguishable from later commentary;
- missing evidence is explicit.

## Reasoning policy

Grace may escalate questions about conflicting office definitions or historical title equivalence. Escalated reasoning must cite supplied evidence and may not manufacture continuity.

## Dependencies

Tranche 0 gate accepted.

---

# WP-JCA-002 — Jessica Officeholder Continuity Evidence Inventory

## Purpose

Identify evidence that belongs to the continuity of the Chief Character Architect officeholder herself rather than merely to the office or its produced artifacts.

## Required work

Inventory, where evidenced:

- reflection / renewal records;
- professional reasoning patterns;
- collaboration style;
- stated strengths / weaknesses;
- lessons learned;
- relationship / institutional interaction evidence;
- self-description or officeholder perspective;
- implementation transitions / passdowns;
- continuity claims and their provenance;
- historical attempts to name or characterize the officeholder;
- evidence that should remain historical rather than become present canon.

Preserve the Steward-established current name Jessica separately from historical evidence.

## Deliverables

- continuity evidence manifest;
- evidence classification by authority / confidence;
- contradictions / supersessions report;
- candidate continuity facts requiring later acceptance rather than automatic import.

## Acceptance criteria

- officeholder evidence is separated from generic office doctrine;
- current Steward-authorized identity facts are not confused with historical artifacts;
- inference is clearly marked;
- no biography, visual identity, surname, or backstory is invented.

## Reasoning policy

Escalation is recommended for ambiguous reflection interpretation. Canonical self-change remains outside this package.

## Dependencies

Tranche 0 gate accepted.

---

# WP-JCA-003 — Character Architecture Work Product and Method Inventory

## Purpose

Inventory the durable professional work, methods, and demonstrated capabilities produced by the Chief Character Architect / Office of Character Architecture.

## Required work

Locate and classify significant professional corpus including, where present:

- Evelyn character / identity / visual-canon campaigns;
- character bible methods;
- physical / visual canon methodology;
- voice / mannerism / behavior work;
- relationship and cognition design methods;
- resident identity / continuity methods;
- validation / recognizability approaches;
- prompt / reasoning / review techniques;
- work-package series showing professional practice;
- completed outputs versus exploratory drafts;
- methods that remain valuable independently of Estate runtime machinery.

The objective is not to import Evelyn yet. Evelyn's corpus is evidence of Jessica's professional practice and a later major migration subject.

## Deliverables

- professional corpus manifest;
- method / capability taxonomy;
- accepted-vs-exploratory classification;
- candidate professional doctrine recovery list;
- obsolete Estate-runtime dependencies report.

## Acceptance criteria

- durable method is distinguishable from one-off implementation instructions;
- accepted work is distinguishable from drafts / experiments;
- Evelyn's large corpus is bounded sufficiently for later migration planning;
- professional capability can be reconstructed without copying every historical artifact into runtime context.

## Reasoning policy

Grace may use escalated reasoning to identify method patterns across large bodies of work, but conclusions must remain traceable to source evidence.

## Dependencies

Tranche 0 gate accepted.

---

# WP-JCA-004 — Estate Artifact Provenance and Disposition Classification

## Purpose

Define and apply a consistent disposition system to Jessica / Character Architecture evidence so Riverview imports continuity rather than Estate entropy.

## Required work

Using evidence from JCA-001 through JCA-003 as it becomes available, classify artifacts into at least:

- import as identity / continuity evidence;
- import as professional knowledge / doctrine;
- retain as historical evidence only;
- retain as artifact reference rather than structured state;
- superseded;
- duplicate;
- implementation-only;
- governance-only / underlying rule extractable;
- uncertain / contradictory;
- leave behind.

For governance-only material, capture a durable underlying authority / constraint only when necessary; do not preserve ceremony by default.

## Deliverables

- disposition taxonomy;
- artifact classification table;
- rationale for consequential classifications;
- unresolved / conflicting classification queue;
- proposed import boundaries.

## Acceptance criteria

- provenance is preserved;
- uncertain material remains uncertain;
- no bulk-import assumption exists;
- obsolete runtime machinery is not treated as identity;
- governance ceremony is not migrated merely because it existed;
- classification can be consumed by JCA-005 and later migration tooling.

## Reasoning policy

**Mandatory independent reasoning review before final acceptance.**

Grace should form a provisional classification, obtain an independent reasoning review of consequential / representative disposition decisions, reconcile disagreements, and preserve the review evidence. Historical evidence conflicting with a Steward-authorized fact requires Steward review rather than majority reasoning.

## Dependencies

Tranche 0 gate accepted. May begin alongside JCA-001/002/003, but final acceptance depends on their accepted evidence.

---

# WP-JCA-005 — Jessica Recovery Corpus Manifest and Gaps Report

## Purpose

Synthesize the accepted archaeology into the bounded authoritative recovery corpus that downstream identity, persistence, and runtime design will consume.

## Required work

1. Merge accepted manifests from JCA-001 through JCA-004 without erasing provenance.
2. Identify the bounded set of sources / facts / methods eligible for later migration.
3. Identify material retained only as historical evidence.
4. Record unresolved contradictions and unknowns.
5. Record missing or inaccessible evidence.
6. Identify assumptions in roadmap Tranches B onward that are confirmed, weakened, invalidated, or newly required.
7. Recommend specific refinement to downstream roadmap packages without dispatching them.
8. Produce a compact machine-readable manifest in addition to a human-readable report if current repository conventions support it.

## Deliverables

- Jessica recovery corpus manifest;
- gaps / contradictions report;
- downstream roadmap impact report;
- evidence / provenance index;
- recommendation for whether the Archaeology Gate should pass, pass with bounded unknowns, or stop for Steward review.

## Acceptance criteria

- downstream workers can operate from the bounded manifest rather than re-searching the entire Estate;
- every canonical or professional continuity claim remains traceable;
- uncertainty is preserved;
- the report explicitly identifies what should *not* be imported;
- downstream roadmap assumptions are re-evaluated against evidence;
- no later tranche is silently authorized.

## Reasoning policy

JCA-005 must consume the independent review evidence from JCA-004. Grace may request additional escalated reasoning for synthesis, contradiction analysis, or roadmap-impact review.

## Dependencies

JCA-001, JCA-002, JCA-003, and JCA-004 accepted.

---

# TRANCHE A / ARCHAEOLOGY GATE

The Archaeology Gate evaluates whether Riverview possesses a sufficiently bounded and provenance-aware recovery corpus to refine Tranche B.

Possible outcomes:

- **PASS** — evidence is sufficient; Grace may prepare Tranche B for progressive elaboration.
- **PASS_WITH_BOUNDED_UNKNOWNS** — known gaps do not prevent safe downstream design; unknowns remain explicit.
- **STOP_FOR_STEWARD** — a canonical conflict, missing critical evidence, scope change, or unresolved high-impact contradiction requires human judgment.

Passing this gate authorizes only preparation / refinement of the next tranche under the campaign's existing authority. It does not grant authority to alter resident canon or bypass later gates.
