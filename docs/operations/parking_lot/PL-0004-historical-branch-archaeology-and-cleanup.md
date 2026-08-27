# PL-0004 — Historical Branch, Checkout, and Workspace Archive Cleanup

Status: CAPTURED
Classification: Riverview Internal
Category: Repository Hygiene / Development Workflow / Historical Archive
Priority: High
Originator: Steward
Date Captured: 2026-08-26
Last Expanded: 2026-08-27

## Idea

Perform a deliberate archaeology, preservation, archival, and cleanup pass over Riverview's historical Git branches, local checkouts/worktrees, recovery copies, publication trees, validation trees, evidence directories, and other superseded development artifacts.

The objective is not simply to delete old branches. The objective is to establish one obvious canonical working environment, preserve historically or operationally valuable material in a durable GitHub-hosted archive where appropriate, and remove redundant local clutter only after preservation is proven.

This proposal exists because historical branches and multiple local Riverview checkouts have repeatedly created ambiguity about development authority, publication state, validation provenance, and which copy of Riverview an AI worker should trust. The Steward also wants the active development drive to become materially cleaner once the current repository synchronization/reconciliation work has reached a safe stopping point.

## Current Direction

`main` is the development authority unless an explicit governed work package authorizes another branch.

The current standalone Riverview line is being reconciled/synchronized with GitHub separately from this parked cleanup effort. This proposal must not interfere with that work.

`AI_HINTS.md` is critical operational infrastructure used routinely to orient AI workers. Cleanup must leave one clearly authoritative and current AI-hints path on every supported canonical development/runtime surface. Historical copies may be retained only when clearly marked and isolated so they cannot be mistaken for current instructions.

## Historical Remote-Branch Finding

At the original 2026-08-26 capture, the remote inventory showed **31 non-main branches plus `main`**. The observed non-main branches were:

- `codex/autonomous-grace-codex-loop`
- `codex/c463-resident-continuity-foundation`
- `codex/c464-jessica-archaeology-corpus`
- `codex/c465-jessica-continuity-contract`
- `codex/c466-resident-continuity-persistence`
- `codex/c467-resident-continuity-implementation`
- `codex/c468-resident-rehydration-context`
- `codex/c469-resident-rehydration-context-runtime`
- `codex/c470-tranche-d-completion`
- `codex/c471-jessica-professional-recovery`
- `codex/c472-jessica-validation-steward-dossier`
- `codex/c473-provider-timeout-repair`
- `codex/c474-jessica-behavior-remediation`
- `codex/c474-jessica-behavioral-remediation`
- `codex/c475-jessica-model-qualification`
- `codex/c476-ollama-gpu-runtime-repair`
- `codex/c477-jessica-model-discovery`
- `codex/c478-jessica-repeat-validation`
- `codex/c479-jessica-uncensored-32b-comparison`
- `codex/c480-jessica-steward-acceptance`
- `codex/c481-jessica-operator-integration`
- `codex/c482-jessica-operator-restart-repair`
- `codex/c484-operator-persistent-service`
- `codex/grace-orchestration-deploy`
- `codex/rv-008-comms-connection`
- `codex/rv-008-mcp-mailbox`
- `codex/rv-0045-full-loop-mailbox`
- `codex/rv-0083-estate-doorbell-bridge`
- `codex/rv-0083-estate-doorbell-bridge-final`
- `codex/rv-0083-riverview-owned-doorbell`
- `codex/rv-0083-runtime-root-correction`

Presence of any historical branch is not authorization to use it.

## Alternate-Checkout Finding — 2026-08-26

`A:\Riverview\repo` was observed as a separate detached checkout rather than the then-authoritative working copy. It pointed at the same GitHub remote but was detached from older ancestry, contained a dirty spatial/operator worktree, and included uncommitted/untracked Quest/spatial evidence, roadmap, and synchronization artifacts.

Subsequent reconciliation work has exposed additional Riverview checkouts/worktrees and confirmed that checkout proliferation itself is an operational hazard. This proposal therefore expands beyond remote-branch cleanup to include the local workspace topology.

Do not delete, clean, reset, merge, or otherwise normalize any such checkout merely because this parked proposal exists. Each must first be inventoried and classified.

## Why It Is Parked

The environment contains active development and current repository synchronization work. A cleanup pass that deletes branches, worktrees, directories, or evidence while authority is still being synchronized could destroy useful provenance or active work.

The cleanup should begin only after the current canonical Riverview/GitHub state is stable enough to serve as the comparison authority, or sooner only if the Steward explicitly promotes this item because repository clutter is again blocking safe development.

## Promotion Condition

Promote after current Riverview repository synchronization/reconciliation reaches a safe accepted checkpoint and the Steward explicitly authorizes workspace cleanup, or sooner if a historical branch, stale checkout, conflicting `AI_HINTS.md`, or ambiguous dirty state again causes a development-authority, checkout, publication, merge, validation, or recovery error.

## Desired End State

The cleanup should leave:

1. One obvious canonical Riverview source/development location for ordinary work.
2. One authoritative published GitHub lineage for current Riverview development.
3. Canonical `AI_HINTS.md` guidance that is current, consistent, and easy for every AI worker to locate.
4. Only intentionally active local worktrees/checkouts on the primary development drive.
5. Historical material preserved outside the active workspace when it has continuing forensic, institutional, evidentiary, or recovery value.
6. Redundant/superseded local copies removed only after preservation and dependency checks succeed.
7. Stream Deck and other cleanliness/status tooling able to report the state of the canonical working environment rather than remaining permanently `DIRTY` because unrelated historical trees exist elsewhere.
8. A durable manifest describing what was archived, retained locally, deleted, or intentionally left unresolved.

## GitHub Historical Archive Concept

Evaluate creating a separate GitHub archive repository, or another clearly isolated archival namespace if repository governance determines that is preferable, for historical Riverview development material that should be preserved but should no longer clutter the active development drive or current Riverview repository branch list.

The archive is not intended to become a second active Riverview repository. It should be explicitly non-authoritative and historical.

Candidate archive content may include:

- retired branch tips that contain unique historical value;
- superseded reconciliation/publication branches;
- historical recovery checkpoints;
- obsolete worktree/checkouts that contain unique committed history;
- selected evidence/manifests needed to explain major migrations or recoveries;
- preserved snapshots of historically significant pre-Riverview or migration states when ordinary Git history does not already preserve them adequately;
- metadata mapping original local path / branch / commit / purpose to its archived destination.

The cleanup investigation must determine whether Git objects/branches alone are sufficient for a given artifact. Do not copy large working directories into an archive repository when their meaningful state is already fully preserved by Git history.

Large binaries, generated environments, caches, dependencies, model files, temporary validation outputs, and reproducible build products should not be pushed into GitHub merely to empty the drive. Their value, size, licensing, sensitivity, and reproducibility must be evaluated first.

The archive should include a prominent README stating that it is historical, non-authoritative, and must not be used as a development starting point without explicit Steward direction.

## Classification Model

Before any deletion, classify each discovered branch, checkout, worktree, or artifact into one of these categories:

### ACTIVE / CANONICAL
Required for current Riverview development or runtime. Retain in the active workspace.

### ACTIVE / BOUNDED
A currently authorized worktree or temporary execution context with a known owner and purpose. Retain until its work package closes.

### HISTORICAL — GIT ALREADY PRESERVES
No unique working-tree material exists and useful history is already safely represented by reachable Git commits/tags/branches. Local checkout may become removable after dependency verification.

### HISTORICAL — ARCHIVE CANDIDATE
Contains unique historical, forensic, institutional, or recovery value worth preserving outside the active workspace.

### EVIDENCE / PRESERVATION HOLD
Must remain unchanged until an identified acceptance, investigation, or recovery dependency closes.

### REPRODUCIBLE / DISPOSABLE
Caches, virtual environments, generated outputs, temporary validation trees, or other material that can be regenerated and has no required evidentiary value.

### UNKNOWN / INVESTIGATE
Authority, uniqueness, ownership, or dependencies are not sufficiently understood. Do not remove.

## Future Cleanup Scope

When promoted, perform a bounded read-only inventory first.

### Remote branches

For every non-main Riverview branch:

1. Compare it against current authoritative `origin/main`.
2. Identify commits/files already represented on main, superseded, duplicated, or genuinely branch-only.
3. Recover useful branch-only implementation, documentation, evidence, or institutional knowledge through an explicit reviewed package when necessary.
4. Verify recovered material on main before changing/removing the historical reference.
5. Classify the branch as safe to retire, worth retaining temporarily, archive-worthy, or requiring investigation.
6. Verify scripts, worktrees, automation, documentation, and external processes do not still reference the branch.
7. Remove/retire historical branch references only after preservation is proven.

Special attention should be given to:

- `codex/c484-operator-persistent-service` — old Grace development line that previously diverged from `main` and required reconciliation.
- `codex/rv-0083-*` — old doorbell-related lines that must not be reused merely because they remain visible.

### Local checkouts and worktrees

Inventory Riverview-related directories across the development drive rather than assuming every directory named `Riverview` is current.

For each candidate record:

- absolute path;
- repository remote;
- branch/detached state;
- HEAD SHA;
- upstream and divergence;
- dirty/untracked state;
- worktree registration;
- apparent owner/purpose;
- last meaningful activity where determinable;
- unique commits;
- unique uncommitted material;
- external dependencies/references;
- classification and recommended disposition.

### Non-repository workspace clutter

Identify temporary validation directories, backups, recovery trees, exported evidence, obsolete environments, caches, generated artifacts, and other large historical material associated with Riverview development.

Do not equate age with disposability. Determine whether each item is reproducible or evidentiary before removal.

### AI hints and authority anchors

Search canonical and historical Riverview surfaces for `AI_HINTS.md` or equivalent orientation files.

The cleanup must ensure:

- canonical instructions are synchronized with accepted Riverview authority;
- active automation resolves the canonical copy;
- historical copies are clearly isolated/marked or removed with their historical checkout;
- an AI worker cannot reasonably land in an obsolete checkout and mistake stale hints for current authority;
- publication checks verify the canonical hints remotely before claiming completion.

## Stream Deck `DIRTY` / `CLEAN` Follow-On

The Steward's Estate Stream Deck profile currently has a top-left cleanliness indicator that persistently reports `DIRTY` and is operationally irritating because it does not provide a useful clean-state signal.

As part of or immediately following workspace consolidation, inspect what that indicator actually measures.

The desired behavior is not necessarily "every Git tree anywhere on A: is clean." It should report a deliberately defined operational cleanliness boundary, likely centered on the canonical Riverview development tree and any explicitly active bounded worktrees.

Future acceptance should establish:

- exactly which repositories/worktrees contribute to the indicator;
- what `DIRTY`, `CLEAN`, `SYNC`, divergence, unpublished commits, and unresolved work mean;
- whether historical/archive trees are excluded;
- whether a dirty state can be drilled down to the exact responsible path;
- whether the indicator distinguishes uncommitted changes from committed-but-unpublished changes.

Do not modify the Stream Deck profile merely because this proposal records the requirement.

## Safety / Explicit Non-Actions

Parking this proposal does not authorize cleanup.

Until intentionally promoted:

- do not delete branches merely because they appear old;
- do not delete local directories merely because another checkout appears newer;
- do not use `git clean` or broad reset as a cleanup mechanism;
- do not force-push historical refs;
- do not resume development from historical branches to discover their contents;
- do not archive secrets, credentials, private/sensitive data, caches, environments, or large binaries without explicit classification;
- do not treat a branch name, local checkout, old report, or prior Codex usage as authority;
- do not change canonical source/runtime placement as a side effect of cleanup;
- do not allow the archive repository to become a new competing authority.

## Proposed Execution Shape When Promoted

### Phase 1 — Authority freeze and inventory

Establish accepted canonical Riverview/GitHub state and capture manifests of all relevant branches, worktrees, checkouts, and workspace artifacts.

### Phase 2 — Archaeology and classification

Compare every candidate to canonical state and assign one of the classifications above. Identify unique committed and uncommitted value.

### Phase 3 — Preservation plan

Design the GitHub historical archive structure, tags/manifests, retention rules, and handling for non-Git evidence. Obtain Steward approval before destructive action.

### Phase 4 — Preserve/archive

Recover unique valuable material, publish approved historical references/artifacts, and verify remote preservation.

### Phase 5 — Local cleanup

Remove only items proven redundant/disposable and no longer referenced by active tooling. Re-inventory after each bounded cleanup group rather than performing a drive-wide destructive sweep.

### Phase 6 — Authority and cleanliness validation

Verify canonical `AI_HINTS.md`, source/runtime paths, GitHub publication, automation/worktree references, Stream Deck cleanliness semantics, and recovery documentation.

## Acceptance Criteria for a Future Promoted Project

A future cleanup should not be considered complete until:

- canonical Riverview source and GitHub authority are unambiguous;
- every removed local item has a recorded classification and disposition;
- every archive-worthy item has verified durable preservation;
- no active automation or worktree references a removed path/ref;
- canonical `AI_HINTS.md` is verified locally and remotely;
- historical AI hints cannot be mistaken for current authority during normal workflows;
- current development and tests still operate from the intended canonical locations;
- archive documentation explains provenance and non-authoritative status;
- the active development drive has materially less redundant Riverview clutter;
- the Stream Deck cleanliness indicator can reach and accurately represent a meaningful `CLEAN` state, either as part of this project or through a bounded follow-on accepted by the Steward;
- a final manifest provides an audit trail sufficient to undo or understand the cleanup decisions.

## Related Evidence and Context

- Original 2026-08-26 Riverview remote inventory observed 31 non-main branches plus `main`.
- Historical branch/checkouts have already caused development-authority and reconciliation confusion.
- `AI_HINTS.md` is the canonical fast-recovery entry point and directs substantial parked ideas to detailed `PL-####` artifacts.
- Current repository synchronization/reconciliation work is intentionally separate from this parked cleanup proposal.
- The Steward explicitly requested preservation of potentially useful historical material while removing unnecessary local-drive clutter, with a GitHub archive repository as a candidate mechanism.
