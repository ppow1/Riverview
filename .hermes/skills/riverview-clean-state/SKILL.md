---
name: riverview-clean-state
description: Enforce Riverview repository hygiene and canonical-state discipline for every Riverview engineering session. Use whenever Hermes is asked to inspect, modify, test, reconcile, publish, validate, troubleshoot, or implement work in ppow1/Riverview or A:\Riverview. Automatically perform non-destructive preflight and hygiene checks, anchor work to A:\Riverview\standalone and current origin/main, detect stale checkouts/imports/divergence, preserve dirty overlays, and require an explicit stop before destructive filesystem, branch-retirement, force-push, authority-changing, or other irreversible actions.
---

# Riverview Clean State

Apply this skill at the beginning of every Riverview engineering session and again before publication, reconciliation, destructive cleanup, or handoff.

## Canonical anchors

Treat these as the default authority unless current `AI_HINTS.md` or explicit Steward direction says otherwise:

- Canonical local working root: `A:\Riverview\standalone`
- Canonical repository: `ppow1/Riverview`
- Canonical published line: `origin/main`
- `AI_HINTS.md` is the fast-recovery entry point and must be read before engineering action.
- Historical/archive/hold trees are evidence, not development authority.

Never infer authority from a directory name, stale checkout, old branch, detached HEAD, terminal cwd, editable install, or prior conversation memory.

## Session preflight

Before modifying Riverview:

1. Read canonical `AI_HINTS.md` and its required anchors.
2. Verify current cwd/repository root.
3. Verify branch, HEAD, upstream, fetched `origin/main`, divergence, worktree registrations, and dirty state.
4. Verify Python/import provenance when Python is involved. Candidate or canonical source must resolve from the intended root, never an obsolete checkout.
5. Check for obvious stale path contamination when the task touches launchers, scheduled tasks, Stream Deck, services, virtual environments, or test wrappers.
6. Capture the base SHA used for the work.
7. State the intended ownership/scope before editing shared governance or authority files.

Use `scripts/riverview_repo_guard.py` for a repeatable non-destructive preflight when code execution is available.

## Non-destructive hygiene that is automatically allowed

Perform these without asking for additional permission when they are necessary to keep the session grounded:

- `git fetch` / remote refresh.
- read-only status, diff, log, ancestry, worktree, branch, and path inspection.
- compare local HEAD to `origin/main`.
- detect stale editable-install or import provenance.
- create manifests, patches, evidence reports, and preservation bundles.
- create a bounded temporary branch/worktree when explicitly needed for safe isolation and allowed by current governance.
- run tests and diagnostics that do not mutate authority or destroy data.
- update session notes/evidence on an already-authorized branch when that is part of the task.

Do not turn preflight into a long archaeology expedition when the state is already clear. Prefer targeted checks and proceed.

## Dirty-state discipline

Treat dirty work as owned material until proven otherwise.

- Never use `git clean`, `reset --hard`, broad checkout/reset, or blind stash/pop to make a tree look clean.
- Inventory dirty paths before operations that could move or reconcile the tree.
- Preserve unrelated dirty work exactly.
- If a dirty overlay does not overlap the intended delta, do not absorb it into the current task.
- If overlap exists, stop and explain the exact conflicting paths before proceeding with an irreversible resolution.
- Report committed-but-unpublished work separately from uncommitted dirty work.

A useful status model is:

- CLEAN
- DIRTY — uncommitted/staged changes
- AHEAD — committed but unpublished
- BEHIND — remote newer
- DIVERGED — both local-only and remote-only commits
- UNKNOWN/ERROR — provenance cannot be established safely

## Short-lived lane discipline

For bounded Riverview engineering work:

- Anchor the lane to an explicit base SHA.
- Keep scope narrow enough that the lane can be integrated and retired promptly.
- Do not let a temporary branch/worktree silently become a new long-lived authority.
- If the lane accumulates repeated corrective tranches or material divergence, surface that as integration debt rather than continuing indefinitely.
- After successful integration and verification, recommend retiring the temporary branch/worktree promptly.

Modules reduce code coupling; they do not replace source-control integration discipline.

## Hermes engineering Steward-attention boundary

When this repository is the working root for a bounded Hermes engineering lane,
enable the project plugin and expose `riverview_steward_attention`. Use that
single tool only when the lane genuinely stops at a terminal human-attention
boundary: `READY_FOR_STEWARD_REVIEW`, `BLOCKED_REQUIRES_STEWARD`, or
`STEWARD_DECISION_REQUIRED`. Do not call it for progress, intermediate tests,
ordinary failures that will be retried, or a report from which the lane can
continue.

The call must carry the lane, `RIV-*` checkpoint, durable evidence reference,
Hermes session ID, and stable terminal transition ID. Reuse the same transition
ID on a legitimate retry. Riverview owns durable notification state and
idempotency; its existing Estate `WindowsPresenter` adapter owns delivery.
Delivery is not acknowledgement, and acknowledgement is not institutional
acceptance. The spoken summary is short; the full report remains in the Hermes
session/evidence location.

## Publication discipline

Before claiming publication:

1. Fetch/reverify current `origin/main`.
2. Confirm the candidate still includes the intended base and required concurrent changes.
3. Run applicable tests/diagnostics against the actual candidate source.
4. Use a normal fast-forward publication path whenever possible.
5. After push, independently verify the remote ref.
6. Re-anchor the canonical local checkout to the published commit while preserving its dirty overlay.
7. Report local HEAD, remote HEAD, and whether they match.

Never claim GitHub publication merely because a local commit exists.

## Mandatory stop boundaries

STOP and request explicit Steward confirmation before:

- deleting branches, worktrees, directories, files, or scheduled tasks when deletion is not already explicitly authorized;
- force-pushing or rewriting published history;
- `reset --hard`, `git clean`, destructive checkout/reset, or equivalent data-loss operations;
- discarding, overwriting, or rewriting unknown dirty material;
- changing canonical authority, canonical repository root, or `main` ownership semantics;
- promoting Parking Lot work to Ready Bench;
- changing governance/authority policy beyond an already-authorized bounded edit;
- publishing sensitive/secret material;
- replacing or deleting ambiguous evidence/preservation holds.

When the Steward has already explicitly authorized a bounded destructive maintenance operation, do not manufacture extra approval gates. Stop only when the actual tool/runtime requires confirmation or when new ambiguity materially exceeds the authorization.

## Historical/archive boundaries

Treat these as non-authoritative unless current canonical guidance says otherwise:

- `ppow1/Riverview-Historical-Archive`
- `A:\Riverview\historical-holds\...`
- retired/reconciliation/publication/preservation trees
- adjacent Estate/CueMastery reference trees

Do not import, launch, test, or resume development from them merely because they exist.

## Handoff and completion report

At a meaningful completion boundary report, compactly:

- canonical local root;
- local HEAD;
- fetched/published `origin/main` HEAD;
- clean/dirty/ahead/behind/diverged state;
- base SHA used;
- temporary branches/worktrees created and their disposition;
- tests/diagnostics run against which source root;
- publication verification if publication occurred;
- any preservation holds or unrelated dirty overlays intentionally left untouched;
- any destructive/authority-changing action that remains blocked on explicit confirmation.

Do not bury the state in prose. Make the canonical state immediately obvious.

## Recovery rule

If repository authority becomes ambiguous, stop implementation and re-anchor from canonical `AI_HINTS.md`, verified GitHub state, and `A:\Riverview\standalone` before proceeding. Do not reconstruct authority from conversation fragments.
