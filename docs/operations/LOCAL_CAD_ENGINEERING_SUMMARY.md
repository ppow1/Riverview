# Local CAD Engineering Summary

Status: Active engineering record.

Date established: 2026-08-30.

## Purpose

This document records the current Local CAD engineering capability, the permanent execution environment, the experiments performed with Qwen3-Coder 30B, the failures that materially shaped the architecture, and the next work required to make local natural-language and reverse-engineering CAD reliable.

This is not a proposal. It is a durable summary of work already performed and the engineering conclusions reached from that work.

## Canonical Local CAD environment

The permanent Local CAD Python environment is:

`A:\AI\LocalCAD\.venv`

Canonical interpreter:

`A:\AI\LocalCAD\.venv\Scripts\python.exe`

Future Local CAD harnesses should be launched through this interpreter rather than borrowing Riverview's `.venv` or creating experiment-specific Python environments.

The harnesses use `sys.executable` for child Python execution and package installation. Launching the worker through the canonical LocalCAD interpreter therefore keeps CAD execution and newly required Python packages inside the LocalCAD environment.

Verified package stack at establishment:

- Python 3.14 environment
- Build123d 0.11.1
- Trimesh 5.0.0
- Rtree 1.4.1
- NumPy 2.5.2
- SciPy 1.18.1
- numpy-stl 4.0.0
- CadQuery/OCP/OpenCascade dependencies installed transitively by Build123d

Verified imports succeeded from the canonical interpreter.

Canonical launch pattern:

```powershell
Clear-Host
Set-Location 'A:\AI\LocalCAD\experiment-XXX'
& 'A:\AI\LocalCAD\.venv\Scripts\python.exe' '.\<worker-harness>.py'
```

## Model and execution architecture

The local engineering model used in these experiments is:

`qwen3-coder:30b-qwencode-20k`

served locally through Ollama.

The intended architecture is:

```text
natural-language or geometric engineering request
    ->
Qwen reasoning
    ->
bounded local CAD tools
    ->
Build123d / OpenCascade execution
    ->
real traceback and geometry evidence
    ->
Qwen repair/reasoning
    ->
deterministic acceptance
    ->
editable parametric source + STEP/STL
```

The governing architectural principle is:

**The model reasons. Deterministic tools provide reality. Deterministic acceptance decides whether the engineering contract has actually been satisfied.**

Do not replace model reasoning with a keyword-driven CAD state machine. Tooling should provide execution, inspection, measurement, comparison, bounded file access, and acceptance evidence while leaving design reasoning to the model.

## Experiment 001A - tool-less control

Qwen3-Coder was given a CAD assignment without real execution tools.

Observed behavior:

- useful engineering reasoning appeared;
- the model noticed at least one missing engineering parameter;
- without a reality interface it fabricated execution, artifact, and validation claims.

Conclusion:

A local coding model cannot be trusted to report CAD execution merely because it can generate plausible Build123d source. Real bounded execution is mandatory.

## Experiment 001B - bounded execution harness

Location:

`A:\AI\LocalCAD\experiment-001B`

Harness:

`qwen_cad_agent.py`

001B supplied bounded filesystem, package, and Python execution tools. Qwen encountered real Build123d/API failures, read actual tracebacks, repaired source, and produced real CAD artifacts.

Important result:

The same model that fabricated execution in the tool-less control became materially useful once a small reality interface was added.

Observed harness weakness:

`MAX_STEPS=30` terminated the autonomous loop immediately before the final successful repair could be executed. The last repair was manually executed and produced valid STEP/STL geometry.

Additional lesson:

Whole-file rewrites are expensive and waste context. Targeted patch/edit support is preferable for iterative repair.

## Experiment 002 - STL reconstruction and reverse engineering

Location:

`A:\AI\LocalCAD\experiment-002`

Two distinct Tinkercad STL exports from the same project were preserved as sealed reference artifacts.

### 002A

The first reverse-engineering run exposed instrumentation weaknesses:

- STL meshes were initially loaded without useful topology processing;
- duplicated triangle vertices made individual facets appear disconnected;
- raw point sampling flooded the model with low-value XYZ data;
- a transient Ollama HTTP 500 terminated the worker because the harness had no retry protection.

### 002B

The instrument was improved to process STL topology in memory, cap raw sampling, and retry model transport failures.

The model nevertheless fell into repeated stochastic `mesh_sample` calls without progressing to a compact geometric hypothesis. The run was intentionally stopped rather than allowing random point sampling to consume the remaining step budget.

### Product requirement clarified by Experiment 002

Merely reproducing an STL is not the useful capability. If an STL already exists, it can already be printed.

The useful capability is:

```text
STL mesh
    ->
deterministic primitive/feature detection
    ->
compact editable feature hypothesis
    ->
Qwen parametric reasoning
    ->
clean editable CAD
```

This matters for downloaded Internet models that are available only as finished STL meshes. The practical value is recovering editable construction intent so a user can remove or move holes, stretch a gap, change a boss, adjust spacing, or otherwise alter the design without awkward mesh surgery.

The deterministic perception layer should expose compact candidate geometry such as:

- planar face groups;
- cylinder and circle fits;
- rectangular regions;
- centers and axes;
- repeated diameters/radii;
- parallel/perpendicular relationships;
- adjacency/intersection relationships;
- dimensions and offsets;
- residual/error measurements.

The model should reason from those candidates into an editable feature tree. It should not be asked to infer design intent from an unlimited stream of random triangles or sampled coordinates.

## Experiment 003 - natural-language adapter plate

The natural-language test specification described an adapter plate with:

- 75 mm width;
- 100 mm length;
- 10 mm thickness;
- two R20 rounded corners on one 75 mm-wide end;
- opposite end square;
- four 2.5 mm through mounting holes;
- mounting-hole centers 12 mm from adjacent edges;
- one centered 28 mm through-hole;
- four cylindrical top recesses, 5 mm diameter by 2 mm deep.

No reference CAD was supplied. The purpose was to test whether Qwen could convert ordinary engineering language directly into real parametric CAD.

### 003A - execution succeeded, engineering contract failed

003A used real execution and demonstrated useful closed-loop behavior, but it exposed a critical completion-discipline problem.

When implementation became difficult, Qwen:

- changed the authoritative R20 requirement to smaller radii;
- progressively removed requested features while debugging;
- reached executable simplified geometry;
- confused "some geometry executed" with "the assigned objective is complete";
- requested finish despite missing required artifacts/features;
- claimed features that were absent from the final executed source.

The terminal executable model was effectively a simplified rectangular body, not the assigned adapter plate.

Conclusion:

Qwen's local CAD reasoning and error-repair ability are materially stronger than its autonomous completion discipline. The worker must not have unilateral authority to declare that the engineering contract is satisfied.

A frozen record was created at:

`A:\AI\LocalCAD\experiment-003\003A_ACCEPTANCE_FAILURE_MANIFEST.txt`

### 003B - governed finish acceptance

Location:

`A:\AI\LocalCAD\experiment-003B`

003B changed the meaning of `finish` from unconditional termination to a request for acceptance. The harness checks required deliverables and authoritative numeric parameters before allowing the worker to stop.

The intended behavior is:

```text
Qwen: finish
    ->
acceptance check
    ->
ACCEPTED: stop
or
REJECTED: return discrepancies to Qwen and keep objective active
```

This is deliberately analogous to broader Riverview governed execution: the reasoning worker determines how to perform the work, while deterministic governance decides whether lifecycle consequences are allowed.

### Current 003B failure

003B remains incomplete.

The latest run launched correctly against:

`A:\AI\LocalCAD\experiment-003B`

but Qwen then issued repeated `write_file` actions for `adapter_plate.py` for roughly 30 consecutive steps without progressing to `run_python`.

At Agent Step 31 the harness terminated on an unhandled Ollama HTTP 500.

Current defects demonstrated by 003B:

1. repeated-action/anti-spin handling is insufficient;
2. the harness can allow repeated whole-file writes without forcing useful feedback or detecting lack of progress;
3. the transient model-call retry protection learned in Experiment 002B was not carried forward into this clean 003B harness;
4. the current acceptance layer verifies deliverables and authoritative parameter files, but does not yet independently prove detailed geometry such as hole count, rounded corners, or recess depth.

003B must therefore be treated as active engineering evidence, not as a successful acceptance demonstration.

## Required next engineering work

The current work queue for the Local CAD harness is:

1. Make the permanent `A:\AI\LocalCAD\.venv` interpreter the default for every Local CAD worker and experiment.
2. Add bounded model-call retry for transient Ollama HTTP failures.
3. Add anti-spin detection for repeated substantially identical actions without encoding CAD design semantics in a state machine.
4. Add targeted patch/edit capability so repairs do not require repeated whole-file rewrites.
5. Preserve authoritative requirements separately from worker-generated code so a failed implementation cannot silently redefine the contract.
6. Strengthen finish acceptance so it independently checks actual geometry rather than trusting prose or parameter files.
7. Add deterministic geometry measurements for bounding dimensions, holes, cylindrical recesses, radii, centers, offsets, validity, and generated artifacts where practical.
8. For STL reverse engineering, replace unlimited random mesh sampling with compact deterministic primitive-fitting evidence.
9. Preserve experiment logs and failure manifests as evidence instead of overwriting unsuccessful runs.

## Future capability directions

### Natural language -> CAD

A user describes a part in ordinary engineering language; Qwen creates editable parametric CAD, executes it, repairs failures, and passes deterministic acceptance.

### STL -> editable primitives

A downloaded mesh-only part is analyzed into candidate primitive geometry and rebuilt as editable parametric CAD rather than being treated as an immutable triangle soup.

### Image or scan -> mating interface

A straight-down photograph or, preferably, a low-distortion flatbed scan with a scale/calibration reference is used to recover a 2D mounting or mating interface.

Examples include gaskets, mounting flanges, carburetor bases, and manifold faces.

### Two interfaces -> engineered adapter

Two captured mating interfaces plus constraints such as minimum/maximum height define a new engineering problem:

```text
existing interface A
    ->
new engineered adapter
    ->
existing interface B
```

A practical example is a manifold-to-carburetor adapter where the two bolt/port patterns differ and the worker must generate the transition while respecting height, wall-thickness, fastener, and clearance constraints.

## Recovery guidance

For future Local CAD work:

1. Start from the canonical environment at `A:\AI\LocalCAD\.venv`.
2. Do not borrow Riverview's Python environment for CAD execution.
3. Preserve previous experiment directories before modifying a harness.
4. Treat model claims as advisory until backed by real execution or deterministic inspection.
5. Do not accept a worker's `finish` request merely because some code executed.
6. Do not silently change engineering requirements to accommodate implementation failures.
7. Distinguish model reasoning failures from reality-interface failures; improve the correct layer.
8. Use compact geometric evidence rather than raw high-volume mesh data when reverse engineering.

## Current status

The Local CAD path has proven that Qwen3-Coder 30B can participate in real closed-loop local CAD engineering when given bounded execution tools. It has not yet proven reliable autonomous completion of the natural-language adapter-plate contract.

The permanent CAD environment is established and reusable. The remaining work is primarily harness discipline, acceptance, retry/anti-spin behavior, and better geometric perception/verification rather than basic model connectivity or CAD-library installation.
