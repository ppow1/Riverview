# RIV-EXE-0010 — When Codex Reports Success but the Artifact Is Missing

Never accept Codex's completion narrative as proof of repository state.

Provider completion != execution completion. Execution completion != objective
completion until independently reconciled.

Codex can be confidently wrong: a model or agent may report an action as
completed even when the external side effect did not persist. This is not an
authoritative claim about intent or behavior; Riverview must independently
reconcile observable repository state.

## Diagnostic sequence

1. Identify the execution, work-order, and objective IDs.
2. Inspect the authoritative repository path directly.
3. Verify `git status` and the authoritative HEAD.
4. Verify the expected artifact exists and satisfies its acceptance condition.
5. Inspect the resulting commit tree.
6. Verify commit reachability from `origin/main` when publication is required.
7. Compare Codex `provider_claimed_*` values with Riverview-generated
   `riverview_verified_*` evidence.
8. Inspect the temporary-worktree changed paths and copy-back result.
9. Find the first divergence between the claim and authoritative evidence.
10. Do not manually create the missing artifact before forensic capture.

Successful bounded repository work must independently verify repository
identity, approved base, exact path scope, required artifact/content, commit
tree, publication when required, and the expected post-execution working tree.
Any mismatch fails reconciliation closed and leaves the historical record
auditable. A correction is append-only; it does not rewrite the original
execution or reconciliation record.
