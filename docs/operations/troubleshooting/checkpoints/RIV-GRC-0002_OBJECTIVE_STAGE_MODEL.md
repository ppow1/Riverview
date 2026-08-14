<!-- Version: 0.2.2 -->
# RIV-GRC-0002 - Objective or stage cannot progress safely

Component owner: `riverview.grace.objectives`.

Trigger: an objective/stage is missing, a dependency is incomplete, required evidence is absent, a stage transition is invalid, or restart/resume cannot reconstruct authoritative state.

Authoritative inputs:
- `objectives`
- `objective_stages`
- `objective_stage_dependencies`
- River events for the objective aggregate

Outputs:
- persisted readiness and status
- accepted evidence references
- stage final outputs
- objective final output
- River event provenance

Failure classes:
- objective missing
- stage missing
- dependency unsatisfied
- required evidence missing
- invalid stage transition
- restart/resume failure

Bounded distinguishing probes:
1. Run `python -m riverview.grace.objective_acceptance read`.
2. Inspect the three RV-005.2 PostgreSQL tables.
3. Read the objective River aggregate.
4. Compare `required_evidence` with `accepted_evidence`.

Smallest safe repair:
- restore only missing/corrupt objective-stage state from accepted PostgreSQL evidence;
- add only genuine evidence references;
- never fabricate evidence, bypass dependencies, or move workflow authority into JSON files.

Recovery verification:
- objective tests pass;
- seed and read acceptance succeed in separate Python processes;
- final outputs persist;
- River aggregate contains creation, evidence, stage completion, and objective completion events.

Provenance:
- waypoint: RV-005.2
- migration: 0010
- implementation: `src/riverview/grace/objectives.py`
- acceptance: `src/riverview/grace/objective_acceptance.py`

Escalation boundary:
- ambiguous user intent;
- authority changes;
- protected/Undercurrent data;
- requested dependency bypass;
- evidence that cannot be verified.

Validation state: first-pass implementation evidence.
Observed repair evidence:
- Repeated acceptance replay originally reused the fixed key `acceptance.rv0052.restart`.
- A previously completed acceptance objective caused the seed process to fail its first-run readiness assertion.
- Acceptance now accepts an explicit objective key so every replay can create fresh durable evidence while retaining separate-process restart/resume verification.

Recovery verification:
- Generate one fresh acceptance key.
- Run `python -m riverview.grace.objective_acceptance seed <key>`.
- Start a separate process and run `python -m riverview.grace.objective_acceptance read <key>`.
- Repeat with a second fresh key; both runs must succeed independently.
Fifth observed repair evidence:
- The live Python acceptance harness passed syntax-aware validation.
- Repair then failed while trying to locate one exact text anchor in an already partially rewritten, unpublished PowerShell publisher.
- Because the publisher had never been committed or published, the smallest safer repair was to replace that canonical publisher wholesale with a fresh replay-safe version rather than continue brittle text surgery.

Recovery verification:
- Publisher version is 0.2.6.
- Publisher explicitly creates one fresh `acceptance.rv0052.publish.*` key and passes it to both seed and resume processes.
- Publisher retains exact-scope allowlisting, isolated worktree publication, staged whitespace validation, remote race check, exact remote verification, and preservation of unrelated utilities.
- Full local acceptance passes before publication.
Sixth observed repair evidence:
- Broad substring replacement of `KEY="acceptance.rv0052.restart"` can match inside the already-correct identifier `DEFAULT_KEY`.
- Repeated application can therefore produce `DEFAULT_DEFAULT_KEY`, while weaker substring validators still appear to find `DEFAULT_KEY`.
- Ruff exposed the real failure because the CLI referenced `DEFAULT_KEY`, which was no longer actually assigned.

Recovery verification:
- Normalize only a complete line matching `^[A-Z_]*KEY="acceptance.rv0052.restart"$`.
- Parse the resulting Python AST.
- Require exactly one assignment target named `DEFAULT_KEY` with value `acceptance.rv0052.restart`.
- Reject any standalone `KEY` identifier or malformed `DEFAULT_*_KEY` assignment.
- Run two fresh-key cross-process restart/resume cycles.