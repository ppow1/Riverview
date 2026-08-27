# PL-0004 Historical Archive / Workspace Cleanup Report

Status: PRESERVATION / INVENTORY COMPLETE — STOPPED BEFORE DESTRUCTIVE CLEANUP

Date: 2026-08-27

Canonical baseline: `01b658cad1a28eb7fab1cbbf873f881a89caab53`

Canonical published source: `ppow1/Riverview` `main`

Canonical local working root: `A:\Riverview\standalone`

Authority: Steward-authorized PL-0004 preservation/inventory stage.

## Executive result

- `A:\Riverview\standalone` `main`, fetched `origin/main`, and GitHub `main` all matched `01b658cad1a28eb7fab1cbbf873f881a89caab53` before cleanup work.
- No deletion, `git clean`, `reset --hard`, branch deletion, worktree removal, service restart, paused-lane restart, Operator implementation, Ready Bench change, or historical cleanup was performed.
- Private non-authoritative archive created: https://github.com/ppow1/Riverview-Historical-Archive
- Archive main commit: `6e1156af95e47ae7098e859e8c462042c7aac4b4`.
- All 31 actual non-main GitHub branch tips were preserved as Git-native `historical/codex/*` refs. The original branches remain untouched.
- Standalone's pre-existing 36-entry dirty overlay remains a preservation hold and was not staged by this report.

## 1. Local checkout, worktree, and significant-root inventory

The complete machine-readable local inventory is in the archive repository at `inventory/local-checkouts.json`. The bounded inventory is:

| Path | HEAD | State / classification |
|---|---|---|
| `A:\Riverview\standalone` | `01b658c` | ACTIVE / CANONICAL; 36 pre-existing status entries |
| `A:\Riverview\reconciliation-candidate` | `01b658c` | HISTORICAL — GIT ALREADY PRESERVES; clean registered worktree |
| `A:\Riverview\repo` | `99b67d9` | EVIDENCE / PRESERVATION HOLD; dirty independent checkout |
| `A:\Riverview\main-integration` | `de22077` | HISTORICAL / ARCHIVE CANDIDATE; clean independent checkout |
| `A:\Riverview\main-reconcile` | `fb11720` | EVIDENCE / PRESERVATION HOLD; modified/staged material |
| `A:\Riverview\p1repair` | `82b515b` | HISTORICAL / ARCHIVE CANDIDATE; clean independent checkout |
| `A:\Riverview\p3work` | `3251993` | HISTORICAL / ARCHIVE CANDIDATE; clean independent checkout |
| `A:\Riverview\run004c-r1` | `ecf5607` | HISTORICAL / ARCHIVE CANDIDATE; clean independent checkout |
| `A:\Riverview\runtime\publication\rv0052-20260814-154902` | `34b672f` | EVIDENCE / PRESERVATION HOLD; staged publication material |
| `A:\Riverview\runtime\publication\rv0052-20260814-155333` | `34b672f` | EVIDENCE / PRESERVATION HOLD; staged publication material |
| `A:\Riverview\runtime\publication\rv0052-final-20260814-160206` | `34b672f` | EVIDENCE / PRESERVATION HOLD; staged publication material |
| `A:\theestate\Riverview` | `ec9075b` | EVIDENCE / PRESERVATION HOLD; separate Estate/Riverview checkout |
| `A:\Riverview\reference\theestate` | `8d1e243` | UNKNOWN / INVESTIGATE; adjacent reference repository |
| `A:\Riverview\reference\CueMastery` | `9efce59` | UNKNOWN / INVESTIGATE; adjacent reference repository |

Only `standalone` and `reconciliation-candidate` are registered Git worktrees. The remaining paths are independent clones/checkouts or nested publication trees. Significant non-checkout roots include `A:\Riverview\workspaces` (approximately 4.8 GB on the bounded scan), `A:\Riverview\runtime` (approximately 1.8 GB), `backups` (empty), `data` (small), `local` (empty), and `tools` (small). Large roots remain holds; no recursive deletion was attempted.

## 2. Complete remote branch inventory

The complete list of all 31 non-main branches, tips, divergence, unique-commit counts, and patch-equivalence results is committed in `inventory/remote-branches.json` and `ARCHIVE_MANIFEST.md` in the private archive. All remain on `ppow1/Riverview`.

Branches with zero unique commits versus canonical main are classified `GIT HISTORY ALREADY SUFFICIENT`. Branches with unique commits are classified `ARCHIVE` or `ARCHIVE / REVIEW`; age alone was not used as a deletion criterion. No remote branch was deleted.

Archive-preserved non-main branches include the autonomous Grace lane, C463–C484 continuity/Jessica/Operator lanes, Grace orchestration, RV-0045, RV-008, and RV-0083 branches. Grace/Jessica and Hermes/MCP lanes remain paused.

## 3. Contamination and dependency archaeology

### Confirmed Python contamination

- `A:\Riverview\standalone\.venv\Lib\site-packages\_editable_impl_riverview_kernel.pth` contains `A:\Riverview\repo\src`.
- `A:\Riverview\repo\.venv\Lib\site-packages\_editable_impl_riverview_kernel.pth` contains the same stale path.
- Both environments' `direct_url.json` files report editable source `file:///A:/Riverview/repo`.
- This is the proven mechanism by which validation from standalone can import obsolete `repo` source. Neither environment is safe to treat as canonical until separately repaired/rebuilt.

### Runtime, launcher, and service references

- Active `\Riverview Runtime Supervisor` is enabled/running and launches `A:\Riverview\standalone\tools\powershell\runtime\Start-RiverviewRuntimeSupervisor.ps1` with `-RepositoryPath A:\Riverview\standalone`.
- Disabled `\Riverview CME Supervisor`, `\Riverview Comms5 HTTP Service`, and `\Riverview Comms5 Reverse Tunnel` still reference `A:\Riverview\repo`. They are stale-path repair/preservation candidates, not active lanes.
- The bounded Windows service query returned no Riverview-named service.
- The installed Stream Deck plugin and canonical control script still use `A:\Riverview\repo`; this is a live stale-path dependency.
- The current process environment had no Riverview-specific `PYTHONPATH` or `RIVERVIEW_*` override. The primary risk is editable-install metadata plus hard-coded launch paths.
- Virtual environments, caches, dependency downloads, node_modules, generated outputs, credentials, and secrets were not archived.

## 4. Dirty and untracked material

The complete path/status/size/SHA-256 evidence is committed in archive `inventory/dirty-material.json`. No dirty material was staged or deleted.

- Standalone: 36 pre-existing entries, including active implementation/test edits, two migrations, C1/C2/C3 evidence, resource-control additions, and the preserved-runtime directory. Classification: ACTIVE / CANONICAL plus EVIDENCE / PRESERVATION HOLD.
- `repo`: dirty spatial/operator implementation and untracked evidence/scripts. Small evidence files have matching SHA-256 copies in standalone's preserved-runtime directory.
- `main-reconcile`: modified/staged GRC evidence and renamed test; preservation hold.
- Publication trees: staged objective-stage artifacts; preservation hold.
- `A:\theestate\Riverview`: modified governance/source/test files and untracked evidence; separate provenance hold.
- Three spatial reports contain deployment-token fields. They were excluded verbatim from the archive; any future copy must redact values as `[REDACTED]`.
- `evelyn-test.glb` is 5,017,904 bytes and `RV-016.5_SPATIAL_CONTRACT_REFERENCE.png` is 2,892,890 bytes. Both remain local value/size review holds and were not archived.

## 5. GitHub archive and preservation evidence

`ppow1/Riverview-Historical-Archive` is private, default branch `main`, and explicitly non-authoritative. Its README and `ARCHIVE_MANIFEST.md` prominently state `HISTORICAL PRESERVATION ONLY`, identify canonical `ppow1/Riverview main` and `A:\Riverview\standalone`, and prohibit treating the archive as a development starting point without Steward direction.

The archive contains the complete local, remote, and dirty inventories. The 31 non-main branch tips were pushed as Git-native refs under `historical/codex/*` and independently verified with `git ls-remote`. No complete working directory, virtual environment, cache, generated artifact, credential, secret value, GLB, or PNG was uploaded.

## 6. AI_HINTS authority

Canonical copy: `A:\Riverview\standalone\AI_HINTS.md`, published at `ppow1/Riverview/main:AI_HINTS.md`. Local blob, canonical-tree blob, and GitHub API blob all equal:

`00912784685617ea5036ddbffda51b578d1745b4`

Discovered copies:

- `A:\Riverview\standalone\AI_HINTS.md` — canonical.
- `A:\Riverview\reconciliation-candidate\AI_HINTS.md` — historical reference.
- `A:\Riverview\repo\AI_HINTS.md` — stale/evidence hold.
- `A:\Riverview\main-integration\AI_HINTS.md` — historical.
- `A:\Riverview\main-reconcile\AI_HINTS.md` — preservation hold.
- `A:\Riverview\p1repair\AI_HINTS.md` — historical.
- `A:\Riverview\p3work\AI_HINTS.md` — historical.
- `A:\Riverview\run004c-r1\AI_HINTS.md` — historical.
- `A:\Riverview\runtime\publication\rv0052-20260814-154902\AI_HINTS.md` — publication hold.
- `A:\Riverview\runtime\publication\rv0052-20260814-155333\AI_HINTS.md` — publication hold.
- `A:\Riverview\runtime\publication\rv0052-final-20260814-160206\AI_HINTS.md` — publication hold.
- `A:\Riverview\reference\theestate\AI_HINTS.md` and `reference\CueMastery\AI_HINTS.md` — adjacent reference roots, not current authority.
- `A:\theestate\Riverview\AI_HINTS.md` — separate Estate/Riverview provenance hold.

The ordinary development environment is unambiguous only when entered through standalone. Editable installs and stale launch paths remain the practical mechanisms that can expose obsolete guidance/source.

## 7. Stream Deck DIRTY/CLEAN investigation

Installed plugin: `C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\Plugins\com.riverview.operator.sdPlugin`.

- Runtime status is HTTP health at `127.0.0.1:18082/health` plus a live-process count.
- Quest status is ADB/device and scrcpy/process based; Quest Cast is blocked/yellow.
- It does not inspect Git status, staged files, untracked files, branch publication, ahead/behind, or divergence, and cannot identify the responsible repository path.
- Historical trees do not directly contribute to the current indicator, but the stale `repo` working directory can make control actions operate on the wrong source.
- Proposed future semantics: `CLEAN`, `DIRTY — uncommitted`, `AHEAD — committed/unpublished`, `BEHIND`, `DIVERGED`, `ACTIVE WORKTREE DIRTY`, and `ERROR/UNKNOWN`, scoped to canonical standalone and excluding archive/history by default.
- Stream Deck configuration was not modified.

## 8. Proposed cleanup sets — stopped before deletion

| Set | Scope | Classification | Evidence / risk |
|---|---|---|---|
| A — Safe reproducible junk | Allowlisted generated/cache/temp subtrees under workspaces/runtime | REPRODUCIBLE / DISPOSABLE, proposed only | Potentially multi-GB; requires file-level allowlist and regeneration proof |
| B — Clean historical checkouts | `main-integration`, `p1repair`, `p3work`, `run004c-r1` after reference review | HISTORICAL / ARCHIVE CANDIDATE | Git history recorded; verify external references before removal |
| C — Archived historical checkouts | Clean trees whose history is verified in private archive | HISTORICAL / GIT ALREADY PRESERVES | Restore by clone/archive refs; no deletion authorized |
| D — Retired remote branches | Branches classified history-sufficient or archived | DELETE CANDIDATE, proposed only | Archive refs verified; branch deletion still requires explicit authorization |
| E — Dirty historical trees | `repo`, `main-reconcile`, publication trees, Estate/Riverview, standalone overlay | EVIDENCE / PRESERVATION HOLD | Exact status/hash evidence; high risk until semantic review |
| F — Steward decision required | GLB/PNG, private Quest recovery material, large runtime/workspace roots, adjacent reference repos | UNKNOWN / INVESTIGATE | Value/sensitivity/dependency uncertainty; no deletion candidate |

## 9. Reconciliation worktree disposition

`A:\Riverview\reconciliation-candidate` is clean, points to the exact published merge commit, contains no unique committed material beyond published Git history, and was not found in active scheduled-task references. Classification: HISTORICAL — GIT ALREADY PRESERVES. It is an early eventual cleanup candidate but remains intact pending separate Steward authorization.

## 10. Unresolved Steward decisions and proposed next actions

1. Separately authorize repair/rebuild of both editable environments so imports resolve only from standalone; preserve active dirty work and independently verify import provenance.
2. Separately authorize repair of the installed Stream Deck plugin/control-script working directory and future canonical Git-status semantics.
3. Decide whether disabled stale scheduled tasks should be removed or retained as disabled evidence after exporting task definitions.
4. Review GLB/PNG value, sensitivity, and size before archive/deletion decisions.
5. Review workspaces, runtime, publication, and adjacent reference roots with explicit allowlists; never use recursive deletion or `git clean`.
6. Authorize cleanup sets individually. No set is authorized by this report.

## Acceptance / rollback boundary

This tranche is complete only as a preservation-backed inventory and archive-preparation stage. Canonical Git source was changed only by publication of this report. All cleanup sets remain stopped. Recovery is available through canonical commit `01b658cad1a28eb7fab1cbbf873f881a89caab53`, the retained reconciliation worktree, archive commit `6e1156af95e47ae7098e859e8c462042c7aac4b4` and its historical refs, and the local dirty-material SHA manifest.
