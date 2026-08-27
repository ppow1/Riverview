# Riverview Clean-State Contract

Use this reference when deciding whether a Riverview lane is safe to continue, publish, reconcile, or retire.

## Canonical state

Canonical local root: `A:\Riverview\standalone`.
Canonical published authority: `ppow1/Riverview` `main` / `origin/main`.
Canonical orientation: current `AI_HINTS.md` from canonical main.

## Status semantics

- CLEAN: local HEAD equals fetched origin/main and no tracked/untracked working-tree changes exist.
- DIRTY: uncommitted/staged/untracked changes exist, with no commit divergence required.
- AHEAD: local commits exist that origin/main does not yet contain.
- BEHIND: origin/main contains commits not in local HEAD.
- DIVERGED: both sides contain unique commits.
- UNKNOWN/ERROR: authority or provenance cannot be established safely.

## Automatic non-destructive actions

Fetch, inspect, compare, test, diagnose, preserve evidence, and create bounded isolation when governance permits.

## Explicit stop actions

Deletion, force push/history rewrite, destructive reset/clean, authority changes, promotion, and ambiguous dirty-material resolution require explicit Steward confirmation unless already explicitly authorized in the current bounded maintenance request.

## Anti-sprawl rule

A temporary branch/worktree must have a named purpose, base SHA, owner/lane, and intended retirement condition. Once integrated and verified, retire it promptly instead of retaining it as a parallel development authority.
