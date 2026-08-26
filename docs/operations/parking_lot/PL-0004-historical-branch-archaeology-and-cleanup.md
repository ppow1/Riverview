# PL-0004 — Historical Branch Archaeology and Cleanup

Status: CAPTURED
Classification: Riverview Internal
Category: Repository Hygiene / Development Workflow
Priority: High
Originator: Steward
Date Captured: 2026-08-26

## Idea

Perform a deliberate archaeology and cleanup pass over the historical remote branches remaining in `ppow1/Riverview` so old Codex branches cannot be mistaken for current development authority and potentially useful branch-only work is not lost.

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

`main` is the current development authority. Presence of any branch above is not authorization to use it.

## Why It Is Parked

The inventory exposed a recurring operational hazard: a coding worker can discover an old branch, or find itself in an old checkout, and incorrectly treat that branch as the active development line. This already caused Grace work to continue on `codex/c484-operator-persistent-service` after development was intended to be on `main`, requiring reconciliation back to main.

The immediate priority is to finish the current Grace/Campaign Runner stopping checkpoint and move to Hermes work. A full branch-by-branch archaeology would interrupt that work, so this cleanup is intentionally deferred rather than forgotten.

## Promotion Condition

Promote after the current Grace/Campaign Runner temporary stopping checkpoint is complete and Hermes priority work no longer requires immediate attention, or sooner if a historical branch again causes a checkout, publication, merge, validation, or development-authority error.

## Explicit Non-Action

Do not begin branch archaeology merely because this item exists.

Do not delete branches merely because they appear old.

Do not resume development from any listed branch to discover what it contains.

Do not treat a branch name, local checkout, old report, or prior Codex usage as authority.

Until this item is intentionally promoted, normal Riverview development authority is `main` unless a future work package explicitly authorizes another branch.

## Future Cleanup Scope

When promoted, perform a bounded read-only inventory first and classify every non-main Riverview branch. For each branch:

1. Compare it against current `origin/main`.
2. Identify commits/files already represented on main, superseded, duplicated, or genuinely branch-only.
3. Recover any useful branch-only implementation, documentation, evidence, or institutional knowledge through an explicit reviewed package.
4. Verify recovered material on main before changing or removing the historical reference.
5. Classify the branch as safe to delete, retain for forensic history, or investigate further.
6. Remove or otherwise retire branches that no longer provide useful recovery value after preservation is proven.
7. Verify local worktrees, scripts, and automation do not still point at retired branches.
8. Confirm branch-authority guidance prevents historical-branch discovery from becoming implicit authorization.

Special attention should be given to:

- `codex/c484-operator-persistent-service` — old Grace development line that diverged from `main` and had to be reconciled.
- `codex/rv-0083-*` — old doorbell-related lines that should not be reused merely because they remain visible.

## Related Evidence

- Current Riverview remote inventory observed 31 non-main branches plus `main` on 2026-08-26.
- Current accepted Grace/Campaign Runner implementation is on `ppow1/Riverview/main`.
- `AI_HINTS.md` explicitly directs substantial parked ideas to `docs/operations/parking_lot/PL-####-slug.md` and states that parking does not authorize implementation.
