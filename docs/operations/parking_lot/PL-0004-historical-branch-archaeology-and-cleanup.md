# PL-0004 — A: Estate / Riverview Repository Archaeology, Recovery, Consolidation and Cleanup

Status: CAPTURED
Classification: Riverview Internal
Category: Repository Hygiene / Development Workflow
Priority: High
Originator: Steward
Date Captured: 2026-08-26

## Idea

Perform a deliberate A:-scoped archaeology, recovery, consolidation, and eventual cleanup pass over historical Estate/Riverview repositories, remote branches, working trees, and runtime copies so old Codex branches or installed checkouts cannot be mistaken for current development authority and potentially useful work is not lost.

At capture time, the remote branch inventory showed **31 non-main branches plus `main`**. The observed non-main branches were:

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

`origin/main` is the current committed Git baseline. A filesystem development root and runtime owner remain unresolved until the standalone-root reconciliation is accepted. Presence of any branch or checkout above is not authorization to use it.

## Alternate-checkout finding — 2026-08-26

`A:\Riverview\repo` is a separate detached checkout used by the installed runtime, while `A:\theestate\Riverview` is a different current GitHub `main` checkout containing later committed Grace, Hermes, and cognition work. Neither filesystem path is permanently canonical until a reviewed standalone-root reconciliation selects one. The runtime checkout has a dirty spatial/operator worktree and uncommitted/untracked evidence and synchronization artifacts; the current-main checkout has the uncommitted Grace/Jessica initiative. Both must be preserved.

Do not delete, clean, reset, or merge this checkout during ordinary work. Future cleanup should first inventory its dirty files and branch-only commits, then quarantine or recover useful material through an explicit reviewed package.

## Why It Is Parked

The inventory exposed a recurring operational hazard: a coding worker can discover an old branch, or find itself in an old checkout, and incorrectly treat that branch as the active development line. This already caused Grace work to continue on `codex/c484-operator-persistent-service` after development was intended to be on `main`, requiring reconciliation back to main.

The immediate priority is to preserve current Grace/Jessica work while mapping the actual runtime/repository topology. Broad A: archaeology and cleanup is intentionally parked rather than forgotten.

## Promotion Condition

Promote after the current Phase 0 provenance map is reviewed and a standalone-root transition is explicitly authorized, or sooner if a historical branch again causes a checkout, publication, merge, validation, or development-authority error.

## Explicit Non-Action

Do not begin destructive cleanup merely because this item exists.

Do not delete branches or directories merely because they appear old, dirty, detached, duplicated, or branch-derived.

Do not resume development from any listed branch to discover what it contains.

Do not treat a branch name, local checkout, old report, runtime use, or prior Codex usage as authority.

Until a standalone-root transition is intentionally promoted and accepted, preserve all current checkouts and use only the explicitly selected work package target for development.

## Future Cleanup Scope

When promoted, perform a bounded read-only inventory first and classify every Riverview repository/copy, non-main branch, runtime pointer, and dirty artifact under A:. For each repository/copy or branch:

1. Compare it against the verified network `origin/main`.
2. Identify commits/files already represented on main, superseded, duplicated, or genuinely branch-only.
3. Recover useful branch-only implementation, documentation, evidence, or institutional knowledge through an explicit reviewed package.
4. Verify recovered material on the selected standalone root before changing or removing the historical reference.
5. Classify each branch/copy as safe to retire, retain for forensic history, or investigate further.
6. Establish one standalone canonical Riverview root without treating path as institutional authority.
7. Update launchers, scheduled tasks, runtime configuration, and documentation only through an approved transition.
8. Remove or otherwise retire branches/copies only after preservation and rollback evidence is proven.
9. Verify local worktrees, scripts, and automation do not still point at retired branches.
10. Confirm authority guidance prevents historical discovery from becoming implicit authorization.

Special attention should be given to:

- `codex/c484-operator-persistent-service` — old Grace development line that diverged from main and had to be reconciled.
- `codex/rv-0083-*` — old doorbell-related lines that should not be reused merely because they remain visible.
- `A:\EstateRuntime\workspaces\audit\estate-main\*` and other A:-scoped historical Estate variants — never treat age, dirtiness, detachment, or duplication as proof of disposability.

## Related Evidence

- Current Riverview remote inventory observed 31 non-main branches plus `main` on 2026-08-26.
- Phase 0 provenance map: `docs/operations/roadmap/evidence/RIVERVIEW_RUNTIME_REPOSITORY_PROVENANCE_MAP_PHASE0_2026-08-26.md`.
- Current accepted Grace/Campaign Runner implementation is on `ppow1/Riverview/main`; its installed runtime checkout is a separate provenance fact.
- `AI_HINTS.md` explicitly directs substantial parked ideas to `docs/operations/parking_lot/PL-####-slug.md` and states that parking does not authorize implementation.
