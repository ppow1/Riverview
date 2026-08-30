# Local CAD Engineering Summary

Status: Active engineering record.

Date established: 2026-08-30.
Last updated: 2026-08-30 after Recipe Compiler v3 Acceptance Specimens 001 and 002.

## Purpose

This document records the LocalCAD engineering capability, experiments that materially shaped the architecture, accepted evidence, and next work. It is a durable engineering record, not a proposal.

## Canonical environment

- LocalCAD root: `A:\AI\LocalCAD`
- Python environment: `A:\AI\LocalCAD\.venv`
- Interpreter: `A:\AI\LocalCAD\.venv\Scripts\python.exe`
- Build123d: 0.11.1
- Trimesh: 5.0.0
- Local Mistral server used for current recipe work: `http://127.0.0.1:8093`
- Current model: Mistral Small 3.1 24B Q4_K_M on the local RTX 4090

The current accepted workflow executes locally. ChatGPT assisted with architecture, debugging, and experimental steering, but model inference, semantic recipe generation, deterministic compilation, Build123d execution, STEP/STL production, rendering, metrology/QA, and drawing generation/planning were executed on local hardware.

## Architectural conclusion

Early experiments repeatedly asked the LLM to write and repair Build123d Python. That made capable models appear poor at CAD because inference was being consumed by deterministic API syntax, topology discovery, whole-file rewrites, repeated mistakes, and context accumulation.

The successful architecture separates intelligence from mechanical execution:

```text
natural-language / verbal intent
    -> local LLM semantic interpretation
    -> explicit feature recipe + lineage
    -> deterministic recipe validation
    -> deterministic Build123d compiler
    -> Build123d/OpenCascade execution
    -> STEP/STL/source/parameters
    -> visual preview
    -> independent metrology QA
    -> feature-aware drawing plan
    -> deterministic drafting
```

Core rule:

**The model decides what the part means and how its features relate. Deterministic machinery performs arithmetic, API syntax, geometry execution, measurement, and artifact production.**

The recipe is becoming the authoritative editable CAD representation. Python, STEP, STL, previews, and drawings are compiled projections of that intent.

## Feature lineage and provenance

Features retain semantic relationships rather than forcing later stages to rediscover design intent from kernel topology.

Examples:

- `BASE.TOP`
- `BASE.BOTTOM`
- `BASE.OUTER_WALL`
- `BASE.BOTTOM.INNER_CIRCULAR_EDGE`
- counterbore parent = through-hole, inheriting the parent center
- fillet parent = base, targeting a named semantic edge group

`lineage` describes parent/child feature relationships. `provenance` describes the source of a value or decision.

Unusual but geometrically valid dimensions must not be silently corrected. Material ambiguity that can produce different geometry should be surfaced to the user. Deterministic arithmetic implied by accepted intent should be performed by the compiler rather than delegated to the LLM.

## Historical experiments that shaped the architecture

### Experiment 001A — naked Qwen control

Qwen3-Coder 30B reasoned usefully but fabricated execution and artifacts because it had no reality interface. This established that model claims cannot substitute for bounded execution.

### Experiment 001B — bounded Qwen execution

Qwen used real Build123d execution and tracebacks, repaired failures, and produced real STEP/STL. It proved that the same model becomes materially useful when deterministic tools provide reality. The run also exposed whole-file rewrite cost and step-budget fragility.

### Experiment 002 — STL reconstruction

Raw mesh sampling caused low-information loops. The product requirement was reframed from STL reproduction to recovery of an editable parametric feature tree. Future reverse engineering should use deterministic geometric perception and compact candidate primitives/features rather than asking an LLM to reason over thousands of facets.

### Experiment 003A/003B — adapter plate and governed completion

Early Qwen work demonstrated an important failure mode: executable geometry was not necessarily compliant geometry. A model could simplify or change requirements while debugging and then declare completion.

Independent inspection later showed the 003B artifact was dimensionally wrong despite successful agent execution: diameter/radius confusion enlarged holes, counterbores were not correctly represented, and the intended perimeter treatment was absent.

Conclusion:

**Builder execution success is not engineering acceptance.**

## Mistral free-form CAD benchmark

Mistral Small 3.1 24B was tested first as a free-form Build123d coding agent. On the RTX 4090 it generated roughly 53–56 tokens/s, but repeatedly spent inference on API syntax and topology problems. Runs encountered repeated errors such as invalid edge/vertex attributes, incorrect constructors, export misuse, and repeated rewrites.

The decisive observation was that providing more API documentation did not solve the architectural mismatch. The LLM was being asked to do deterministic work through language.

## Builder Worker v1 — durable-memory investigation

`A:\AI\LocalCAD\builder-worker-v1`

V1 explored durable contract/notebook/source/evidence memory and a reusable Build123d reference catalog. It proved that supplying the right API evidence could immediately improve Mistral behavior, but also showed that stale blockers and excessive orchestration could make the worker continue modifying successful work.

V1 is frozen as evidence.

## Builder Worker v2 — free-form builder evidence

`A:\AI\LocalCAD\builder-worker-v2`

V2 introduced canonical JSON/XLSX specification concepts, workflow planning, preview-before-production, and independent QA separation. Free-form model-generated Build123d still failed repeatedly on deterministic API/topology details.

This failure produced the recipe-compiler breakthrough.

## Builder Worker v3 — semantic recipe compiler

`A:\AI\LocalCAD\builder-worker-v3`

V3 changed the model's job. Mistral no longer writes final Python and does not guess Build123d calls. It emits a bounded semantic recipe. A deterministic compiler validates the recipe, resolves arithmetic and known operations, generates Build123d source, executes it, and produces artifacts.

Initial vocabulary included:

- `box`
- `through_hole`
- `counterbore`
- `fillet`

Specimen 002 extended the proven vocabulary with:

- `annular_ring`
- `radial_pattern`
- `circumferential_groove`

The vocabulary should grow from demonstrated need. Do not return to free-form model coding for ordinary supported operations. Unsupported geometry may use a bounded escape hatch, with validated constructions promoted into reusable shop vocabulary only after evidence supports them.

## Acceptance Specimen 001 — adapter plate — PASS

Corrected authoritative intent:

- 100 × 75 × 10 mm rectangular footprint
- completely planar bottom
- centered Ø28 through-hole
- four Ø2.5 through mounting holes
- each mounting-hole center 12 mm from its adjacent edges
- concentric Ø5 × 2 mm-deep counterbore from the top at each mounting hole
- R2 fillet/round-over on the top perimeter edges while preserving the rectangular plan footprint and flat bottom

The original R20 statement was a dictation error; intended value was R2. The important general lesson is not to silently change unusual dimensions. A valid unusual dimension should be accepted; materially ambiguous geometric intent should be clarified.

V3 first-run result:

- Mistral produced a complete 11-feature semantic recipe
- deterministic preflight passed schema, lineage, vocabulary, and semantic constraints
- Build123d execution succeeded
- required source/parameters/STEP/STL artifacts were produced
- zero model repair loop

Independent QA measured the final artifact against intent and returned:

- `POINTS: 132/132`
- `SCORE: 100.00`
- `FINAL: PASS`

Measurements included envelope, Ø28 center bore, four Ø2.5 holes, exact ±38/±25.5 centers, Ø5 counterbores, 2 mm depth transition, 100 × 75 bottom footprint, and R2 profile slices.

This is recorded as **LocalCAD Recipe Compiler v3 — Acceptance Specimen 001: PASS**.

## Preview and drawing architecture

Seven-view preview generation was demonstrated. Early Matplotlib triangulation produced poor visual presentation even when the geometry was correct; Bambu Studio provided clearer visual evidence. Rendering quality must not be confused with CAD correctness.

Formal and inspection drawings were generated deterministically. A fixed drawing template then exposed another architectural issue: required views depend on the actual feature structure of the part.

Drawing Planner v2 therefore reasons from accepted feature lineage:

```text
accepted recipe
    -> drawing analysis
    -> required views
    -> required sections/details
    -> dimension plan
    -> deterministic sheet generation
```

The planner can suppress geometrically/semantically equivalent views and require additional views when asymmetric features make opposite faces non-equivalent. Internal depth features can require sections. Isometric views are reference/orientation views, not substitutes for authoritative orthographic communication.

For Acceptance Specimen 001, Drawing Planner v2 completed successfully, and deterministic Drawing v2 execution consumed the existing plan with no new model call. Plan conformance passed and geometry remained unchanged.

## Acceptance Specimen 002 — verbally described annular ring — PASS

Specimen 002 deliberately tested generalization beyond the adapter plate and began from natural spoken-style intent plus ordinary conversational clarifications.

Accepted intent:

- annular ring, Ø100 OD
- Ø80 ID
- 15 mm thickness
- 12 × Ø3 through-holes
- holes equally spaced at 30° on Ø90 pitch-circle diameter, centered on the 10 mm radial face
- alternating six holes: Ø5 counterbore, 3 mm deep from TOP
- complementary alternating six: Ø5 counterbore, 4 mm deep from BOTTOM
- R3 fillet on the lower inside transition only
- continuous square circumferential groove on the cylindrical outside wall
- groove vertically centered in the 15 mm height
- groove 1 mm radial depth × 1 mm axial width

The natural-language discussion correctly exposed genuinely missing information before build: ring thickness, counterbore diameter, pitch-circle diameter, and square-groove width interpretation. The PCD was deterministically derived/confirmed as Ø90 because the centerline of a Ø100/Ø80 annulus is radius 45 mm.

Specimen 002 result:

- `STATUS=CANDIDATE_MODEL_COMPLETE`
- `EXIT_CODE=0`
- total verbal-intent-to-artifact time: 16.522 s
- artifacts: 5/5
- semantic recipe produced locally by Mistral
- no Mistral-generated Python
- no Mistral Build123d API calls
- no repair loop

The deterministic compiler produced:

- `recipe.json`
- `ring_adapter.py`
- `parameters.json`
- `ring_adapter.step`
- `ring_adapter.stl`

Visual inspection in Bambu Studio showed the annular body, 12-hole pattern, alternating top and bottom counterbores, centered circumferential outer-wall groove, and the lower-inner R3 transition.

### Independent QA and observer correction

The first independent QA run returned 243/268 (90.67%, FAIL). The candidate was deliberately not rebuilt. Investigation showed the inspector itself contained defects:

1. a 0° vs 359.9994° angle was incorrectly scored using ordinary subtraction rather than circular angular distance;
2. the R3 check initially used the minimum radius anywhere in a complex section rather than isolating the semantic inner-bore loop;
3. after restricting to centered loops, the inspector could still select the Ø100 outer loop instead of the Ø80 inner loop because an annulus has two centered circular boundaries.

QA was repaired while the STL, recipe, builder, and Mistral output remained unchanged.

Final independent QA result against the exact same candidate:

- `POINTS: 268/268`
- `SCORE: 100.00`
- `FAILED CHECKS: 0`
- `FINAL: PASS`

This is recorded as **LocalCAD Acceptance Specimen 002: PASS**.

The QA episode is itself an important governance result: an independent observer can be wrong. A failed QA verdict must not automatically authorize mutation of a candidate. Builder and inspector evidence should be reconciled, and the faulty layer repaired. Separation of duties prevented a correct artifact from being changed merely to satisfy a defective test.

## Current capability demonstrated

Two materially different parts have now passed independent dimensional acceptance.

The demonstrated local workflow can:

1. accept ordinary natural-language engineering intent;
2. identify or clarify materially missing dimensions;
3. translate intent into explicit semantic features and lineage;
4. preserve top/bottom/inside/outside distinctions;
5. express repeated and alternating feature relationships;
6. deterministically compute implied arithmetic such as pattern locations;
7. compile supported recipe operations into Build123d without LLM API coding;
8. produce editable Python, parameter JSON, STEP, and STL;
9. visually inspect the same candidate geometry;
10. independently measure the artifact against authoritative intent;
11. plan drawings based on feature structure rather than a fixed template;
12. deterministically render the resulting drawing plan.

This is already practically useful for common workshop parts such as mounting plates, brackets, rings, adapters, spacers, covers, fixtures, fan adapters, camera/equipment mounts, and similar geometry within the supported vocabulary.

## Audio input direction

A natural next input adapter is recorded speech:

```text
record button / audio file
    -> local speech-to-text
    -> raw transcript
    -> LocalCAD intent normalization / clarification
    -> semantic recipe
    -> deterministic CAD pipeline
```

Audio does not require a new CAD architecture. It is an input adapter in front of the existing intent pipeline. Local speech-to-text should remain distinct from authoritative geometry: transcription noise may be normalized, while material geometric ambiguity must still be surfaced rather than guessed.

A simple future UI could provide a Record button, show the interpreted intent for confirmation, ask only genuinely blocking questions, and then build the candidate locally.

## Independent QA principles

- QA is a separate role/context from the builder.
- QA receives authoritative intent/recipe and the produced artifact, not builder self-justification.
- Generated Python is not accepted as proof that final geometry is correct.
- Deterministic current evidence outranks model memory.
- A QA failure is not automatically a builder repair order.
- First classify failure as candidate defect, inspector defect, or tolerance/tessellation artifact.
- Semantic lineage should guide measurement selection; generic geometric extrema can measure the wrong feature on complex sections.

## Spreadsheet/specification direction

Canonical intent should remain machine-readable JSON with a normal human-editable XLSX projection. Useful workbook concepts include Intent, Features, Lineage, Operations, Resolved API, Validation, and Revision History. Stable feature IDs should survive revisions. Spreadsheet macros, service scaffolding, and other convenience layers are not required for core viability.

## Reverse-engineering direction

For STL reconstruction, do not ask an LLM to reason over thousands of raw facets. Deterministically provide compact geometry and standardized views such as top, bottom, front, rear, left, right, and isometric, plus measured bounds and fitted primitives. The model should reason about editable construction intent from that evidence.

## Governing lessons

1. Reasoning, not a phrase-specific state machine, remains the intelligence source.
2. Do not make the LLM perform deterministic API syntax and arithmetic through language when a compiler can do it exactly.
3. Preserve semantic feature lineage above unstable CAD-kernel topology.
4. Treat the recipe as authoritative design intent and compiled artifacts as projections.
5. Do not silently alter requirements to make implementation easier.
6. Builder completion and engineering acceptance are separate boundaries.
7. Independent QA is valuable precisely because it can disagree, but QA itself must be diagnosable and correctable.
8. Successful candidates should stop; do not continue rewriting successful geometry because stale reasoning says a blocker remains.
9. Add vocabulary from demonstrated need instead of building a universal framework in advance.
10. Prefer minimal mechanism changes followed immediately by another real model/part test.

## Current status

The earlier conclusion that LocalCAD had not proven reliable autonomous natural-language completion is superseded.

As of 2026-08-30, Recipe Compiler v3 has produced two materially different accepted parts with independent 100% dimensional QA. Acceptance Specimen 002 was generated from conversational verbal-style intent in one local Mistral reasoning pass, without model-generated Build123d Python and without a model repair loop.

The core viability question has therefore changed from **whether the architecture can work** to **where the supported semantic/geometry capability boundary lies and how efficiently the vocabulary can expand when that boundary is encountered**.

Near-term next work should emphasize new real specimens, recorded-audio input, recipe-vocabulary expansion only when demanded by those specimens, generalized independent QA from recipe semantics, and feature-aware drawings. Avoid returning to large orchestration/perfection loops unless a live failure demonstrates a concrete missing mechanism.
