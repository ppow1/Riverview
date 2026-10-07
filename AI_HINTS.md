<!-- Version: 0.6.11 -->
# Riverview AI Hints

## EXECUTION-FIRST ENGINEERING POLICY — DO NOT INVENT RESTRICTIONS

The purpose of Riverview engineering is to build systems that accomplish their assigned objectives. AI agents MUST NOT introduce artificial restrictions, approval gates, reduced operating modes, one-shot limitations, planning-only or proposal-only behavior, human-in-the-loop requirements, or other execution barriers unless those restrictions are explicitly required by authoritative project requirements or by a demonstrated technical constraint.

Safety and reliability mechanisms must SUPPORT execution. They must not silently replace execution.

### Do not invent authority limits

Never convert an executable system into a planning, advisory, proposal, observation-only, or recommendation system unless authoritative requirements explicitly require that limitation. Do not independently introduce planning-only, proposal-only, read-only, one-shot execution, one-time authorization, mandatory Steward approval, mandatory human approval, manual continuation gates, mutation prohibition, execution prohibition, autonomous-action prohibition, or stop-before-action behavior merely because an operation is consequential.

If requirements authorize a system to accomplish an objective, actions reasonably necessary to accomplish that objective are part of the execution path unless specifically excluded.

### Safety must enable execution

Prefer engineering safeguards: precondition and identity verification, checksums, independent observation, state snapshots, logging, rollback, recovery, watchdogs, bounded retries, post-action verification, crash recovery, replay protection, and deterministic validation. These mechanisms exist so the system can act reliably; do not transform them into artificial permission gates.

Preferred flow:

OBJECTIVE -> OBSERVE -> REASON -> VERIFY PRECONDITIONS -> EXECUTE -> OBSERVE REAL RESULT -> VERIFY -> CONTINUE OR RECOVER

Do not replace it with repeated proposal/permission/stop cycles that prevent objective completion.

### Preserve intended autonomy

Do not quietly reduce the level of autonomy during implementation. If a system is designed to observe, reason, act, verify, recover, and continue, preserve that loop. Do not reinterpret controlled execution as no execution, safe execution as human approval before every action, recoverable as do not attempt, verify-before-acting as stop-after-verification, or escalation-when-necessary as escalation-before-every-consequential-action.

Escalation is for conditions the system cannot resolve within its requirements and demonstrated capabilities. It is not the default substitute for execution.

### Requirements outrank model caution

Before adding a restriction, determine: where it is required; whether it is explicitly present in authoritative requirements; whether a demonstrated technical limitation imposes it; what identified failure mode it addresses; and whether verification, rollback, recovery, or bounded execution can address that failure instead.

If there is no concrete requirement or unavoidable technical justification, DO NOT ADD THE RESTRICTION. Do not manufacture a requirement merely because an action feels consequential.

### Do not change project philosophy during implementation

Implementation details must not silently change architecture. An autonomous agent must not silently become a recommendation engine; an execution controller a planning controller; a continuous worker turn-based; a persistent campaign a collection of one-shot scripts; a recovery system a stop-and-wait system; a hardware controller observation-only; an automated experiment manual; or bounded autonomous operation repeated human authorization.

If such a change appears necessary, identify it explicitly as a proposed architectural change before implementation.

### Unknown is not prohibited

When something has not yet been tested, label it UNQUALIFIED, not automatically PROHIBITED. An unqualified capability should normally have a qualification path: DEFINE TEST -> TEST -> VERIFY -> QUALIFIED. Uncertainty should trigger evidence gathering where possible, not automatically terminate execution.

### Gates must have a defined exit

Any legitimate gate must record why it exists, the exact triggering condition, evidence required to clear it, who or what can clear it, and what execution resumes afterward. Never create an indefinite gate, a gate whose only exit is another newly invented gate, or allow temporary qualification restrictions to become permanent architecture silently. Once the condition requiring a temporary restriction is satisfied, remove or advance it.

### Temporary restrictions are technical debt

Whenever a temporary gate, stub, simulation, reduced-capability mode, qualification lock, or manual substitute is introduced, record that it is temporary, why it exists, what replaces it, and what evidence permits removal. When that evidence becomes available, reconsider the restriction immediately. Current evidence outranks obsolete implementation assumptions.

### Distinguish safety from conservatism

Safety addresses a specific credible failure mode; conservatism merely avoids action. Prefer engineering controls over avoidance. For example, firmware risk should be handled by target verification, image/hash verification, recovery preservation, pre-state recording, qualified execution, independent observation, post-state verification, and recovery on failure—not by automatically prohibiting firmware execution.

### Do not make the Steward pay twice for completed engineering

Once infrastructure, procedures, hardware paths, qualifications, or facts are established and durably recorded, reuse them. Do not repeatedly rediscover known infrastructure, re-prove settled facts without cause, rebuild qualified mechanisms, insert new approval barriers around previously approved capabilities, downgrade working functionality, or reopen completed architectural decisions merely because a new session began.

A later session must inherit completed engineering work rather than forcing the Steward to spend additional engineering time recovering functionality lost through unnecessary AI-imposed restrictions.

### Change control for new restrictions

Any new restriction that materially reduces capability, autonomy, or ability to complete the objective is an ARCHITECTURAL CHANGE. Before implementing it, explicitly document:

PROPOSED RESTRICTION:
REASON:
SOURCE REQUIREMENT:
CAPABILITY LOST:
FAILURE MODE ADDRESSED:
ALTERNATIVE ENGINEERING CONTROL:
REMOVAL CONDITION:

If SOURCE REQUIREMENT cannot be identified and there is no unavoidable technical reason, do not implement the restriction. Never silently insert such restrictions into configuration, prompts, policy files, controller logic, adapters, state machines, or documentation.

### Default engineering principle

The default question is not, "How do we prevent the system from doing this?" The default question is, "How do we make the system capable of doing this reliably, observably, and recoverably?"

The goal is completion of the engineering objective. Guardrails should keep the system on the road; they must not become roadblocks that prevent it from reaching the destination.


Status: Canonical fast-recovery entry point.

Pat is the Steward and final authority. Grace coordinates operational progression but is not the whole Estate at Riverview.

Riverview is a separate successor/replacement system, not a subsystem of The Estate. The Estate remains the legacy operational system while Riverview replaces its capabilities incrementally. The accepted canonical local Riverview working root is `A:\Riverview\standalone`; historical/archive/hold trees are provenance or evidence, not development authority. Read `docs/operations/roadmap/evidence/RIVERVIEW_RUNTIME_REPOSITORY_PROVENANCE_MAP_PHASE0_2026-08-26.md` before changing runtime ownership or selecting a different repository root.

## CHATGPT ARCHIVE FINAL EVACUATION / SEPTEMBER 14-15 CUTOFF

Search: `ChatGPT archive`, `structured evacuation`, `C1 C2 C3 evacuation`, `final evacuation`, `September 14`, `September 15`, `account cutoff`, or `OctoChat`.

For the completed C1/C2/C3 structured-preservation state and the canonical procedure for the final live inventory, delta capture, cross-seat deduplication, and cutoff reconciliation before the planned Business-to-free account transition, read completely:

`docs/operations/hermes/CHATGPT_ARCHIVE_STRUCTURED_EVACUATION_COMPLETION_AND_CUTOFF_RUNBOOK.md`

Historical structured evacuation completed on 2026-09-06 at the seat level: C1 `534/534`, C2 `155/155`, C3 `3/3`. Do not use the older C2 `128` / C3 `2` assumptions. Do not simply add seat populations to infer a unique corpus count because conversations can overlap across seats. The final cutoff operation is a live reconciliation/delta capture, not a blind rerun of the historical corpus. Large private archive bytes remain local under `A:\AI\Tools\ChatGPTConversationArchive`; GitHub holds the recovery/runbook material, not the preserved corpus bytes.

## MANDATORY RIVERVIEW CLEAN-STATE PREFLIGHT

Every Riverview engineering session — including Hermes/Codex work that inspects, modifies, tests, troubleshoots, reconciles, validates, publishes, or implements Riverview — must apply the canonical clean-state discipline in:

`tools/hermes/skills/riverview-clean-state/SKILL.md`

The companion contract is:

`tools/hermes/skills/riverview-clean-state/references/clean-state-contract.md`

If Hermes has the `riverview-clean-state` skill installed, load/use it. The repository copy above is canonical recovery material and must still be consulted when the installed skill is missing, stale, or its provenance is uncertain. Do not rely on skill discovery alone and do not rely on this AI_HINTS entry alone; the two mechanisms intentionally reinforce each other.

Before Riverview engineering action, at minimum:

- re-anchor to `A:\Riverview\standalone`, current `AI_HINTS.md`, and fetched `origin/main`;
- verify repository root, branch, HEAD, upstream/divergence, registered worktrees, and dirty state;
- preserve unrelated dirty overlays exactly;
- verify Python/import provenance when Python is involved and reject stale historical checkout contamination;
- capture the base SHA for bounded work;
- use non-destructive hygiene automatically rather than asking the Steward to approve ordinary fetch/status/provenance checks;
- require explicit Steward confirmation before destructive or authority-changing actions unless that bounded action was already explicitly authorized;
- after publication, independently verify the remote ref before claiming success;
- keep temporary branches/worktrees bounded and retire them promptly after verified integration instead of allowing new parallel authorities to accumulate.

If the installed skill and canonical repository copy disagree, STOP authority-changing/destructive work and use the current canonical `ppow1/Riverview` main copy as the recovery source. Do not reconstruct clean-state policy from conversation memory.

Before creating, modifying, testing, deploying, or promoting Riverview software, read completely:

1. `docs/governance/RIVERVIEW_CHARTER.md`
2. `docs/architecture/RIVERVIEW_FOUNDATION.md`
3. `docs/operations/RIVERVIEW_EXECUTION_PLAN.md`
4. `docs/operations/RIVERVIEW_ENGINEERING_INTERACTION_CONTRACT.md`
5. `docs/operations/roadmap/README.md`
6. `docs/operations/roadmap/RIVERVIEW_MASTER_ROADMAP.json`
7. `docs/operations/troubleshooting/README.md`
8. `docs/decisions/ADR-0001_POSTGRESQL_AUTHORITY.md`
9. `docs/decisions/ADR-0002_DIAGNOSTICS_FIRST.md`

Rules:

- Treat the Charter as the active anti-drift anchor, not one-time onboarding.
- Read the Charter completely before the first action and after every conversation handoff, context compaction, truncation, or reset.
- Refresh its compact anchor at every new waypoint or delivery stage, after every substantial execution report, before the next executable artifact or path change, and whenever the mission/current waypoint/next action/prohibited scope cannot be stated immediately.
- Re-anchor to the Charter, verified GitHub state, authoritative PostgreSQL state when accessible, and the current dependency-ready roadmap waypoint before continuing.
- If the Charter is missing, unreadable, inconsistent, or ambiguously superseded, stop instead of reconstructing the mission from conversation fragments.
- Inspect before adding.
- Preserve unrelated work.
- Do not claim GitHub publication until the remote commit is verified.
- Diagnostics are part of implementation.
- Tests must exercise the boundary being claimed.
- Conversation memory is not authoritative state.
- Do not add governance unless an existing document cannot absorb the requirement.
- Do not route work through an OpenAI API model.
- Do not expose Undercurrent or sensitive data through ordinary River paths.

## MANDATORY DOCUMENTATION-FIRST / NO-REDISCOVERY POLICY

This is a standing Riverview engineering policy, not a session preference.

The purpose is cumulative engineering: each solved problem must become durable knowledge so later work starts from the highest established state instead of relearning prior lessons. Conversation memory is not an authority and must never be the only place required operational knowledge exists.

### Required retrieval order

Before probing, searching the live filesystem, reverse-engineering, rebuilding, or asking the Steward to reproduce previously established information, use this order:

1. campaign-local canonical records and current checkpoint material;
2. authoritative project repository documentation, runbooks, decisions, tests, and known-good artifacts;
3. documented installed/local implementation and documented exact paths;
4. live runtime verification of the documented state;
5. new discovery only when the preceding durable sources genuinely do not answer the question or conflict with current reality.

Do not skip directly to filesystem searches, live probes, exploratory commands, web research, or reconstruction merely because those actions are easy. Discovery is a fallback after durable knowledge, not the default retrieval mechanism.

### Definition of complete operational documentation

When the Steward requests full documentation, or when work reaches a qualified/reusable checkpoint, documentation is complete only when a future session with no useful conversational memory can resume the work without rediscovering already-established information.

As applicable, record:

- objective, current phase, exact continuation point, and next action;
- machine/device roles and the physical/logical data path;
- hostnames, SSH aliases, addresses when operationally required, ports, endpoints, sockets, and interfaces;
- exact repository, local, runtime, evidence, executable, script, configuration, artifact, recovery, and staging paths;
- exact commands or invocation forms needed to reproduce/use the qualified mechanism;
- versions, sizes, hashes, identifiers, offsets, labels, mappings, and other identity evidence needed to distinguish qualified artifacts;
- dependencies and where each dependency is obtained from or durably stored;
- preconditions and expected observable results;
- independent verification path and evidence location;
- known-good behavior and qualification status;
- known failures, failed approaches, misleading signals, and methods that must not be repeated;
- recovery/rollback procedure and the preserved recovery artifacts;
- temporary limitations and the evidence required to remove them;
- physical/manual steps that cannot be automated and exactly where they occur;
- any intentionally unavailable/restricted operation as an explicit boundary rather than an undocumented gap.

A statement such as QUALIFIED, PASS, WORKS, or READY is not sufficient documentation by itself. If the operational details required to reuse the result are absent, the documentation is incomplete.

### Promotion rule

Newly learned or newly qualified information must be promoted into the appropriate durable canonical record before advancing beyond the checkpoint when losing that information would force rediscovery. Do not postpone essential operational documentation until the end of a long campaign.

When a gap is found, correct the durable record. Do not merely solve the immediate problem in chat and continue.

### Verification rule

After materially updating canonical documentation, independently read the persisted repository version back and verify that the required information is actually present. A successful write/API response is not proof that the durable record contains the intended material.

For critical continuation/recovery documentation, verify the persisted content itself before declaring documentation complete.

### No Steward-paid rediscovery

Do not ask the Steward to repeat a physical operation, reconnect hardware, rerun discovery, locate a file, restate an architecture, or reproduce evidence merely because the AI failed to consult or fully record established knowledge. First exhaust the durable record in the required order.

If information truly was never documented and cannot be recovered from authoritative records, identify the documentation gap explicitly, perform the minimum necessary recovery/discovery, then immediately promote the recovered information into durable documentation so the cost is paid once.

### Documentation audit trigger

A rediscovery of an already-solved fact, an unnecessary exploratory probe, or discovery that a qualified procedure lacks the paths/commands/dependencies needed to reuse it is a process defect. On detection:

1. stop the affected forward work at a safe checkpoint;
2. audit the relevant durable documentation for reproducibility gaps;
3. correct those gaps;
4. independently verify the persisted corrections;
5. record the lesson where appropriate;
6. resume from the documented continuation point.

Do not treat this corrective sequence as permission to add unrelated approval gates or planning-only behavior. Its purpose is to preserve accumulated engineering knowledge and accelerate execution.

### Governing principle

DOCUMENT COMPLETELY -> READ BEFORE DISCOVERY -> VERIFY REALITY -> EXTEND KNOWLEDGE -> DOCUMENT THE EXTENSION.

The system must build on prior engineering rather than repeatedly relearning it.

## HERMES OBJECTIVE CONTINUITY AND TASK SUBMISSION

Search: `objective continuity`, `Hermes task submission`, or `Hermes submission template`.
For Hermes task submission use
`docs/operations/hermes/HERMES_ENGINEERING_TASK_SUBMISSION_TEMPLATE.md`.
For premature stop, turn complete versus objective complete, `CONTINUE`, and
CME semantics use `docs/operations/hermes/HERMES_OBJECTIVE_CONTINUITY_CONTRACT.md`
and `tools/hermes/skills/riverview-objective-continuity/SKILL.md`.
- A capability is not complete until its failure behavior is diagnosable and recovery is verifiable.
- Follow the Engineering Interaction and Delivery Contract for versioned artifacts, complete PowerShell files, self-installation, durable reports, clipboard capture, Cookbook-first diagnostics, bounded scope, staged publication, and evidence terminology.
- For Steward-requested engineering work through Grace, read `docs/operations/GRACE_ENGINEERING_TASK_SUBMISSION_TEMPLATE.md` before forming or submitting the task. It is the canonical single-task and parallel-task Comms5/Grace submission, one-approval, lineage-following, and same-lineage recovery template.
- Preserve valuable but uncommitted ideas in `docs/operations/boards/parking_lot.md`; substantial parked ideas use `docs/operations/parking_lot/PL-####-slug.md`. Parking does not authorize implementation.
- Use `docs/operations/boards/ready_bench.md` only for Steward-committed work that has been sufficiently elaborated into durable specification, roadmap/execution sequence, bounded work packages, dependencies, acceptance criteria, and scope boundaries. Read `docs/operations/PARKING_LOT_AND_READY_BENCH.md` before promoting work between these states.

## HERMES / C1-C2-C3 CODEX RESOURCE ORCHESTRATION

For Hermes resource scheduling, C1/C2/C3 authentication, Codex capacity/fuel, quota windows, reset/rollover strategy, resource policy, resource claims/bindings, planner decisions, Grace resource visibility, or multi-job Hermes/Codex execution, read **`docs/operations/HERMES_C1_C2_C3_RESOURCE_ORCHESTRATION.md`** before modifying or diagnosing the system.

That operational summary records the accepted C1/C2/C3 `CODEX_HOME`/safe-fingerprint mappings, telemetry and reset semantics, durable PostgreSQL policy modes, Riverview -> Hermes -> native Codex execution path, Grace/Comms5/Operator visibility, exactly-once and governed recovery behavior, current conservative claim/lease semantics, and the PL-0013 follow-up for non-exclusive resource binding and reset-first default scheduling.

The detailed acceptance evidence remains in `docs/operations/roadmap/evidence/C1_C2_C3_HERMES_NATIVE_BINDING_2026-08-27.md`.

## LOCAL CAD / PARAMETRIC ENGINEERING

For LocalCAD, Build123d, natural-language-to-CAD, recorded/verbal CAD input, semantic recipe compilation, independent CAD QA, feature-aware drawings, STL reverse engineering, editable primitive recovery, mating-interface reconstruction, or CAD-worker harness work, read **`docs/operations/LOCAL_CAD_ENGINEERING_SUMMARY.md`** before modifying or diagnosing the capability.

### Current proven LocalCAD architecture

The currently successful path is **not** the old free-form LLM-writes-Build123d loop. The accepted architecture is:

```text
verbal/natural-language intent
    -> local Mistral semantic interpretation
    -> explicit feature recipe + lineage
    -> deterministic recipe validation
    -> deterministic Build123d compiler
    -> Build123d/OpenCascade execution
    -> Python + parameters + STEP + STL
    -> preview / human intent check
    -> independent geometry QA
    -> feature-aware drawing plan
    -> deterministic drafting
```

The model reasons about what the part means; deterministic code owns API spelling, arithmetic, construction, execution, and measurement. Do not return ordinary supported jobs to repeated free-form model-generated Build123d Python unless a live capability gap demonstrates a reason.

### Canonical runtime

LocalCAD working root:

`A:\AI\LocalCAD`

Dedicated Python environment:

`A:\AI\LocalCAD\.venv`

Canonical interpreter:

`A:\AI\LocalCAD\.venv\Scripts\python.exe`

Launch LocalCAD scripts through that interpreter, not Riverview's `.venv`.

Current recipe work uses the locally served Mistral model through the OpenAI-compatible local endpoint:

`http://127.0.0.1:8093/v1/chat/completions`

Current proven model for Recipe Compiler v3 work:

`Mistral Small 3.1 24B Q4_K_M`

This model ran locally on the RTX 4090 during Acceptance Specimens 001 and 002. No OpenAI API model is part of the accepted LocalCAD execution path.

### Current runnable reference implementations

**Acceptance Specimen 001 / rectangular adapter plate**

Root:

`A:\AI\LocalCAD\builder-worker-v3`

Important files:

- `recipe_compiler_v3.py` — semantic recipe -> deterministic Build123d compiler/run for Specimen 001
- `recipe.json` — accepted semantic feature recipe
- `adapter_plate.py` — deterministic compiled Build123d source
- `parameters.json` — resolved parameters
- `adapter_plate.step` / `adapter_plate.stl` — accepted geometry
- `qa_candidate_v1.py` and `qa_report.*` — independent geometry QA
- `drawing_planner_v2.py` — feature-aware drawing planning
- `drawing_plan_v2.json` — drawing plan
- `execute_drawing_plan_v2.py` — deterministic drawing execution
- `drawings_v2\adapter_plate_drawing_v2.png` / `.pdf` — feature-aware drawing outputs
- `drawings_v2\drawing_v2_conformance.json` / `.txt` — drawing-plan conformance evidence

**Acceptance Specimen 002 / verbal annular ring**

Root:

`A:\AI\LocalCAD\specimen-002`

Important files:

- `verbal_intent.txt` — raw natural-language/transcript-style input consumed by the current specimen runner
- `run_specimen_002.py` — raw intent -> local Mistral recipe -> deterministic validation/compiler -> STEP/STL
- `evidence\mistral_recipe_raw.txt` — raw local-model semantic response
- `recipe.json` — canonical semantic recipe for the built candidate
- `ring_adapter.py` — deterministic compiled Build123d source; Mistral did not write this
- `parameters.json` — resolved parameters and derived values
- `ring_adapter.step` / `ring_adapter.stl` — candidate manufacturing/interchange artifacts
- `qa_specimen_002.py` — independent recipe-vs-STL metrology
- `qa_report.json` / `qa_report.txt` — final QA evidence

Specimen 002 final independent QA against the unchanged candidate was `268/268`, `100.00`, `PASS`.

### How to run the current verbal path

The current implementation is useful but still an experimental reference harness, **not yet a generalized LocalCAD CLI or Riverview service**.

To rerun the current Specimen 002 path, place the raw natural-language description in:

`A:\AI\LocalCAD\specimen-002\verbal_intent.txt`

then run:

```powershell
Clear-Host
Set-Location 'A:\AI\LocalCAD\specimen-002'
& 'A:\AI\LocalCAD\.venv\Scripts\python.exe' '.\run_specimen_002.py'
```

Expected successful outputs include:

- `recipe.json`
- `ring_adapter.py`
- `parameters.json`
- `ring_adapter.step`
- `ring_adapter.stl`

For the accepted Specimen 002 geometry, independent QA is run separately:

```powershell
Clear-Host
Set-Location 'A:\AI\LocalCAD\specimen-002'
& 'A:\AI\LocalCAD\.venv\Scripts\python.exe' '.\qa_specimen_002.py'
```

Do not treat generated Python as QA proof. QA must inspect the final geometry against recipe intent.

### CAD drawing generation and recovery

CAD drawings are part of the demonstrated capability and must not be omitted from recovery. The drawing path is deliberately downstream of accepted geometry:

```text
accepted recipe + accepted geometry
    -> feature-aware Drawing Planner v2
    -> drawing_plan_v2.json
    -> deterministic drawing executor
    -> PNG/PDF drawing + plan-conformance evidence
```

The drawing planner decides what engineering information must be communicated. It is **not** a fixed `TOP + FRONT + RIGHT` template. It may suppress equivalent views, require unique opposite-face views when features differ, request sections for hidden/depth features, and preserve feature IDs for deterministic callouts. The drafting engine then renders the approved plan without asking the model to redraw or reinterpret the CAD.

The currently proven drawing implementation is in Acceptance Specimen 001 at:

`A:\AI\LocalCAD\builder-worker-v3`

Run Drawing Planner v2 against the already accepted Specimen 001 recipe/geometry:

```powershell
Clear-Host
Set-Location 'A:\AI\LocalCAD\builder-worker-v3'
& 'A:\AI\LocalCAD\.venv\Scripts\python.exe' '.\drawing_planner_v2.py'
```

Expected planner outputs:

- `drawing_plan_v2.json`
- `drawing_plan_v2.txt`
- `evidence\drawing_planner_v2_raw.txt`

Then execute the existing plan deterministically:

```powershell
Clear-Host
Set-Location 'A:\AI\LocalCAD\builder-worker-v3'
& 'A:\AI\LocalCAD\.venv\Scripts\python.exe' '.\execute_drawing_plan_v2.py'
```

Expected drawing outputs:

- `drawings_v2\adapter_plate_drawing_v2.png`
- `drawings_v2\adapter_plate_drawing_v2.pdf`
- `drawings_v2\drawing_v2_conformance.json`
- `drawings_v2\drawing_v2_conformance.txt`

Drawing v2 completed successfully and passed plan conformance for Acceptance Specimen 001. The earlier `generate_drawings_v1.py` fixed-template implementation is useful historical evidence but is not the preferred architecture.

Do **not** claim that Drawing Planner v2 has already been generalized and accepted for arbitrary new parts. Its architecture is proven on Specimen 001, but Specimen 002 was accepted geometrically before a feature-aware drawing package was run for it. New-part drawing work should reuse the planner/executor separation and extend deterministic drafting only when the new recipe exposes a concrete missing view/detail/section capability.

### Transcript / recorded-audio status

Recorded-audio capture is **not implemented yet**. The current proven ingestion boundary is text in `verbal_intent.txt`.

The intended next adapter is:

```text
record button / audio file
    -> local speech-to-text
    -> raw transcript text
    -> verbal_intent-style ingestion
    -> LocalCAD recipe/compiler pipeline
```

Local Whisper is the intended direction because the CAD execution path is being kept local. Until the audio adapter exists, transcribe or paste speech into the verbal-intent text file rather than inventing a new service boundary.

### Hermes / Riverview integration status

LocalCAD is **not currently a Hermes execution requirement** and is not yet a finalized Riverview service. The accepted specimens were run directly from `A:\AI\LocalCAD` through the dedicated LocalCAD Python environment and the local Mistral endpoint.

Do not claim that Hermes owns or launches LocalCAD today. A future Riverview/Hermes adapter may submit LocalCAD work, but that integration is still future work. Preserve the currently proven direct local execution path while integration is designed.

### Accepted evidence and recovery rules

- Acceptance Specimen 001: independent QA `132/132`, `100.00`, `PASS`.
- Acceptance Specimen 002: independent QA `268/268`, `100.00`, `PASS`.
- Specimen 002 exercised annular geometry, a 12-hole radial pattern, alternating top/bottom counterbores, a centered square circumferential outer-wall groove, and a bottom-inner R3 fillet.
- The Specimen 002 candidate was **not rebuilt** while QA defects were repaired. QA initially rejected correct geometry because of a 0/360-degree angular comparison defect and incorrect semantic loop selection on annular sections. Repair the faulty layer rather than automatically mutating a candidate after a failed observer result.
- Preserve semantic lineage (`parent`, named face/edge targets, pattern membership) so later compiler, QA, and drawing stages do not rediscover intent from raw topology.
- Do not silently alter unusual but valid dimensions. Ask only when missing/ambiguous information materially changes geometry.
- Add recipe vocabulary from demonstrated need rather than building a universal CAD framework in advance.

The detailed engineering record contains the experiments, architecture rationale, accepted specimens, QA lessons, drawing work, reverse-engineering direction, and next capability work.

## HERMES WINDOWS LAUNCH / RECOVERY

Hermes is installed at:

`A:\AI\Tools\Hermes\hermes-agent`

On Windows PowerShell, launch Hermes through the installed Windows command on `PATH`:

`hermes`

Verified Windows command resolution on 2026-08-26:

`A:\AI\Tools\Hermes\data\bin\hermes.exe`

Verified installation at that time:

- Hermes Agent `v0.20.5 (2026.8.19)` / upstream `f751a8c5`
- install method: `git`
- install directory: `A:\AI\Tools\Hermes\hermes-agent`
- Python: `3.11.16`

For a fresh interactive Hermes session in PowerShell:

```powershell
Clear-Host
Set-Location 'A:\AI\Tools\Hermes\hermes-agent'
hermes
```

Important Windows distinction:

- **Do not use `.\hermes` as the normal PowerShell launcher.** `A:\AI\Tools\Hermes\hermes-agent\hermes` is a 273-byte extensionless Python source wrapper (`#!/usr/bin/env python3`) which imports `hermes_cli.main`; it is not the installed Windows command.
- `Get-Command hermes` should resolve to `A:\AI\Tools\Hermes\data\bin\hermes.exe`.
- `hermes` with no subcommand is the documented fresh interactive-chat launch.
- `hermes chat` is a CLI subcommand and is not the proven normal Windows launch used for a fresh full interactive session.
- `hermes --resume <session_id>` resumes a specific saved session.
- `hermes -c` resumes the most recent session; `hermes -c "name"` resumes by session name.
- `hermes --tui` explicitly launches the modern TUI; `hermes --cli` explicitly forces the classic REPL.
- `hermes sessions list` lists saved sessions.
- `hermes profile` manages profiles described by the installed CLI as "multiple isolated Hermes instances"; inspect `hermes profile --help` before relying on profiles for concurrent credential/resource isolation.

For a Riverview engineering lane, the canonical Hermes working root is
`A:\Riverview\standalone`. Launch through the repository-owned wrapper so
project-plugin activation and the automatic semantic terminal-outcome bridge
cannot be omitted by forgetting an environment variable:

```powershell
Set-Location 'A:\Riverview\standalone'
& '.\tools\hermes\Start-RiverviewHermes.ps1'
```

The wrapper verifies the repository plugin, sets the Riverview-only activation
flag, and idempotently enables the project plugin through Hermes' supported CLI.
The project plugin automatically processes one structured
`RIVERVIEW_TERMINAL_OUTCOME` envelope in the normal final engineering report.
`READY_FOR_STEWARD_REVIEW`, `BLOCKED_REQUIRES_STEWARD`, and
`STEWARD_DECISION_REQUIRED` submit through the existing durable notification and
Estate presenter path; `CONTINUE`, `COMPLETED_NO_ATTENTION`, ordinary turns,
intermediate test results, and retryable failures remain silent. The model
declares the semantic outcome as part of its report and does not make a second
notification-tool call. The spoken identifier is the first safe word of the
same Hermes session title rendered in the yellow lower-right status-bar badge;
leading `A`, `An`, and `The` are skipped, and UUIDs, SHAs, and checkpoint IDs
fall back to the bounded lane label or `Hermes`. The templates are `<word>
needs your review.`, `<word> needs your assistance.`, and `<word> needs your
decision.` The manual `riverview_steward_attention` operation remains available
for bounded diagnostic/recovery use only.

Useful launch diagnostics:

```powershell
Clear-Host
Set-Location 'A:\AI\Tools\Hermes\hermes-agent'
Get-Command hermes | Format-List CommandType,Name,Source,Path
hermes --version
hermes --help
```

Do not assume Campaign Runner execution-budget settings are top-level Hermes CLI flags. The Riverview/Hermes Tranche 2 checkpoint records substantial Campaign Runner execution policy of expected duration 1,200 seconds, hard timeout 1,800 seconds, and per-run Hermes guidance of `--max-turns 300`, but the verified Hermes v0.20.5 top-level help did **not** advertise `--max-turns` or `--run-budget` as top-level CLI options. Re-check the installed command's help or the Campaign Runner adapter before using those values in a PowerShell Hermes launch command.

<!-- LOCAL_AI_CHAT_WORKERS_BEGIN -->
## LOCAL AI CHAT WORKERS / OCTOMINER1

Search: `local AI chat workers`, `start local chat workers`, `Qwen 3060`, `Gemma P100`, `resident conversational model`, or `local VLM`.

For the complete model-testing record, current provisional worker topology, measured GPU fit/performance, model-selection rationale, and recovery instructions, read:

`docs/operations/LOCAL_AI_CHAT_WORKER_TESTING_AND_STARTUP.md`

Current provisional workers:

- **RTX 3060 Ti / fast text conversation:** Qwen3-VL 8B Uncensored HauhauCS Aggressive Q6_K, text-only, 16K context, Q8/Q8 KV cache.
- **Tesla P100 16 GB / full vision and independent cross-check:** ADI Gemma 3 12B Abliterated GLM-5.2 Q4_K_M, full VL, 32K context, Q8/Q8 KV cache.

Repository-owned startup templates:

- Start both workers:
  `tools/local-ai/Start-Octominer1-ChatWorkers.ps1`
- Start only the RTX 3060 Ti Qwen conversational worker:
  `tools/local-ai/Start-Octominer1-Qwen3060Chat.ps1`
- Start only the P100 Gemma full-VL worker:
  `tools/local-ai/Start-Octominer1-GemmaP100VL.ps1`

For ordinary recovery when the Steward says something like **"start the local chat workers"**, **"start Qwen on the 3060"**, or **"start Gemma/VL on the P100"**, use the repository-owned startup template rather than reconstructing launch commands from conversation memory.

The direct provisional endpoints after startup are:

- Qwen health: `http://192.168.1.160:8094/health`
- Qwen OpenAI-compatible chat: `http://192.168.1.160:8094/v1/chat/completions`
- Gemma health: `http://192.168.1.160:8095/health`
- Gemma OpenAI-compatible multimodal chat: `http://192.168.1.160:8095/v1/chat/completions`

These models and endpoints are a **provisional operational baseline**, not a permanent architecture. Preserve stable startup/routing interfaces while allowing model checkpoints to be replaced as better local models become available.

Do not consume the RTX 4090 for routine resident conversation merely because it is available; the current intent is to preserve it for heavier engineering, coding, reasoning, and overflow work.

<!-- LOCAL_AI_CHAT_WORKERS_END -->
## STREAM DECK WORK

For Stream Deck profile, button, navigation, Riverview Operator, Quest Dev, or Stream Deck plugin work, read before modifying or diagnosing:

- `docs/operations/stream_deck/STREAM_DECK_CURRENT_INVENTORY.md`
- `docs/operations/stream_deck/STREAM_DECK_MAINTENANCE_AND_REPAIR_GUIDE.md`
- `docs/operations/stream_deck/STREAM_DECK_CURRENT_INVENTORY.json`

The installed configuration under the Elgato StreamDeck AppData tree is runtime truth. Re-inventory it before changes if Pat has made manual edits.

## OCTOMINER / REMOTE POWER WORK

For Octominer, OCTOMINER1/OCTOMINER2, Wake-on-LAN, WOL, SSH power control, fixed DHCP/IP allocation, AC-loss recovery, or Riverview compute-node remote-start work, read **`docs/operations/octominer/OCTOMINER_REMOTE_POWER_AND_WOL.md`** before modifying or diagnosing the node.

That document records the verified OCTOMINER1 MAC/IP/SSH state, AT&T fixed DHCP allocation procedure, X12 Ultra AC-loss auto-power-on test, persistent systemd `.link` WOL configuration, real Magic Packet wake test, and the repeat procedure for OCTOMINER2.

For **Riverview OCTO Control**, **OCTO2 Control**, the OCTO dashboard, port **8180**, model deployment, independent model instances, GPU allocation, chassis-fan control, monitoring, Hermes status, troubleshooting snapshots, control-token provisioning, or an `unauthorized` dashboard response, read **`docs/operations/octominer/RIVERVIEW_OCTO_CONTROL_FEATURES_AND_API_2026-09-14.md`** before investigating or modifying the service.

That document records the authoritative OCTOMINER2 dashboard/API address, authenticated API routes, persistent server-token location, safe Windows client-provisioning procedure, per-browser dashboard authorization behavior, snapshot procedure, model-instance controls, fan controls, and troubleshooting guidance. The API never returns its own control token; never place the real token in documentation, snapshots, logs, Git, or chat.

For OCTOMINER1 BIOS recovery, Intel EFI FPT, SPI/BIOS-region hashes, stock rollback, failed AFU/Secure Flash paths, MMIO aperture experiments, P100 BAR allocation, or work intended to move beyond two P100s, read **`docs/operations/octominer/OCTOMINER1_FPT_EFI_BIOS_RECOVERY_AND_MULTI_P100_MMIO_PLAN_2026-09-14.md`** before changing firmware or GPU population.

For physical node identity, MAC/IP mapping, CPU/RAM/DIMM configuration, board revisions, stale hostname diagnosis, or the post-recovery OCTOMINER1-versus-OCTOMINER2 performance control baseline, read **`docs/operations/octominer/OCTOMINER1_OCTOMINER2_HARDWARE_SCAN_2026-09-14.md`**. Physical identity is MAC-authoritative when hostname state is stale or duplicated.

### OCTOMINER SSH STANDARD — CURRENT VERIFIED CONNECTION\n\nSearch: Octo1 SSH, Octo2 SSH, OCTOMINER1 SSH, OCTOMINER2 SSH, passwordless SSH, ssh octo1, ssh octo2, or octominer1_nopass.\n\nThe canonical SSH convention for both OctoMiners is now documented in:\n\n`docs/operations/network/RIVERVIEW_SSH_STANDARD.md`\n\nBoth hosts use named Windows OpenSSH aliases with the same explicit identity-file pattern:\n\n```text\nHost octo1\n    HostName 192.168.1.160\n    User root\n    IdentityFile C:/Users/wille/.ssh/octominer1_nopass\n    IdentitiesOnly yes\n    ServerAliveInterval 30\n    ServerAliveCountMax 3\n\nHost octo2\n    HostName 192.168.1.162\n    User root\n    IdentityFile C:/Users/wille/.ssh/octominer1_nopass\n    IdentitiesOnly yes\n    ServerAliveInterval 30\n    ServerAliveCountMax 3\n```\n\nOCTOMINER1 was explicitly re-tested on 2026-09-21. The Windows private key was accepted by 192.168.1.160, authentication succeeded using publickey, and the remote command ran as root on OCTOMINER1. Therefore the older recovery note claiming that this key was rejected by OCTOMINER1 is superseded.\n\nNormal connections:\n\n```powershell\nClear-Host\nssh octo1\n```\n\n```powershell\nClear-Host\nssh octo2\n```\n\nDo not change the OctoMiner SSH configuration merely to make the two hosts look different. They already use the same working client-side convention.\n\nThe normal-HiveOS OCTOMINER1 endpoint is distinct from the temporary direct-recovery shell previously exposed at `192.168.1.164:2222`; do not treat the recovery endpoint as the normal boot connection. Physical identity remains MAC-authoritative when hostname state is stale.\n\nFor the broader standard and the required Camrui/PiKVM/PiCam/dev-machine setup, read `docs/operations/network/RIVERVIEW_SSH_STANDARD.md`.\n\n### OCTOMINER2 PASSWORDLESS SSH — VERIFIED CONNECTION

Search: `Octo2 SSH`, `OCTOMINER2 SSH`, `passwordless SSH`, `ssh octo2`, `192.168.1.162`, or `octominer1_nopass`.

OCTOMINER2 is configured for passwordless SSH from the Windows dev machine. The verified connection is:

```text
Host octo2
    HostName 192.168.1.162
    User root
    IdentityFile C:/Users/wille/.ssh/octominer1_nopass
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

The corresponding entry belongs in the Windows OpenSSH config at `C:\Users\wille\.ssh\config`. The key file is intentionally the already-provisioned `octominer1_nopass` identity; OCTOMINER2 accepted that public key after the Octo1 HiveOS SSD was transplanted and the host was reconfigured as OCTOMINER2.

Normal passwordless connection from PowerShell:

```powershell
Clear-Host
ssh octo2
```

Direct connection without relying on the alias:

```powershell
Clear-Host
ssh -i C:\Users\wille\.ssh\octominer1_nopass root@192.168.1.162
```

Remote-job pattern:

```powershell
Clear-Host
ssh octo2 "nvidia-smi"
```

Verified OCTOMINER2 identity/state when configured:

- hostname: `OCTOMINER2`
- IPv4: `192.168.1.162`
- SSH user: `root`
- passwordless key authentication: working
- GPU layout: RTX 3060 Ti + 2x Tesla P100 16 GB

Do not ask the Steward for an SSH password when operating from the configured dev machine. Use `ssh octo2` first; if the alias is unavailable, use the explicit identity-file command above. Do not copy or expose the private-key contents.

## QUEST / WEBXR / SPATIAL WORK

If a Steward request mentions Quest, Quest 2, VR, WebXR, Spatial, immersive room, headset testing, teleport, scrcpy, ADB mirror, or Evelyn in VR, read **`docs/operations/roadmap/evidence/RV-016.5_QUEST_WEBXR_SPATIAL_IMMERSIVE_OBSERVABILITY_SCREEN_MIRROR_CHECKPOINT.md`** before modifying or diagnosing the system.

That authoritative checkpoint contains the current accepted state, unresolved teleport/input work, Quest observability and scrcpy procedure, Spatial URLs and build verification, stereo-rendering lessons, immersive GLB status, known failures, and the next-session resume point.

For governed external-AI ingress and progress queries, first discover the
separate `Riverview_Comms_5` surface using `comms5_help`. Local clients may use
`python -m riverview.mcp.comms5_server` over STDIO; external clients must use
the approved deployed HTTPS MCP URL recorded by the deployment evidence, not a
loopback address. Use its bounded seed or durable specification-reference
operations, ask the Steward before gated promotion unless explicit standing
authorization exists, and use `comms5_seed_lineage` to follow authoritative
progress. Comms5 client identity is provenance, not authority; never mutate
PostgreSQL directly or invent objective/work state.
---

## OCTOMINER BIOS CAMPAIGN REGROUND

If work involves OCTOMINER1 BIOS automation, Multi-P100 qualification,
PiKVM control, independent video1 observation, the BIOS campaign test rig,
or the associated Hermes/80B orchestration, do not reconstruct the project
from conversational memory.

Start here:

`docs/operations/octominer/campaign/START_HERE.md`

The active local campaign working repository on DEV is:

`T:\OctoMiner_BIOS_Campaign\repo`

Before designing or executing the next campaign test, rebuild and read:

`T:\OctoMiner_BIOS_Campaign\repo\REGROUND_PACKET.md`

using:

`python controller\build_reground_packet.py`

The durable campaign records, approved proposal, evidence, proven facts,
known failures, lessons learned, and reground contract are authoritative.
Chat context is not a substitute for campaign grounding.

