<!-- Version: 0.6.2 -->
# Riverview AI Hints

Status: Canonical fast-recovery entry point.

Pat is the Steward and final authority. Grace coordinates operational progression but is not the whole Estate at Riverview.

Riverview is a separate successor/replacement system, not a subsystem of The Estate. The Estate remains the legacy operational system while Riverview replaces its capabilities incrementally. The accepted canonical local Riverview working root is `A:\Riverview\standalone`; historical/archive/hold trees are provenance or evidence, not development authority. Read `docs/operations/roadmap/evidence/RIVERVIEW_RUNTIME_REPOSITORY_PROVENANCE_MAP_PHASE0_2026-08-26.md` before changing runtime ownership or selecting a different repository root.

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
- A capability is not complete until its failure behavior is diagnosable and recovery is verifiable.
- Follow the Engineering Interaction and Delivery Contract for versioned artifacts, complete PowerShell files, self-installation, durable reports, clipboard capture, Cookbook-first diagnostics, bounded scope, staged publication, and evidence terminology.
- For Steward-requested engineering work through Grace, read `docs/operations/GRACE_ENGINEERING_TASK_SUBMISSION_TEMPLATE.md` before forming or submitting the task. It is the canonical single-task and parallel-task Comms5/Grace submission, one-approval, lineage-following, and same-lineage recovery template.
- Preserve valuable but uncommitted ideas in `docs/operations/boards/parking_lot.md`; substantial parked ideas use `docs/operations/parking_lot/PL-####-slug.md`. Parking does not authorize implementation.
- Use `docs/operations/boards/ready_bench.md` only for Steward-committed work that has been sufficiently elaborated into durable specification, roadmap/execution sequence, bounded work packages, dependencies, acceptance criteria, and scope boundaries. Read `docs/operations/PARKING_LOT_AND_READY_BENCH.md` before promoting work between these states.

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
`A:\Riverview\standalone`. Launch from that root with project plugins explicitly
enabled so the shared `riverview_steward_attention` terminal-boundary tool is
available. This is infrastructure, not a per-handoff reminder:

```powershell
Set-Location 'A:\Riverview\standalone'
$env:HERMES_ENABLE_PROJECT_PLUGINS = '1'
hermes plugins enable riverview-steward-attention
hermes
```

The tool is used only for a genuine terminal `READY_FOR_STEWARD_REVIEW`,
`BLOCKED_REQUIRES_STEWARD`, or `STEWARD_DECISION_REQUIRED` boundary. Ordinary
progress, intermediate test results, and retryable failures remain silent.

Useful launch diagnostics:

```powershell
Clear-Host
Set-Location 'A:\AI\Tools\Hermes\hermes-agent'
Get-Command hermes | Format-List CommandType,Name,Source,Path
hermes --version
hermes --help
```

Do not assume Campaign Runner execution-budget settings are top-level Hermes CLI flags. The Riverview/Hermes Tranche 2 checkpoint records substantial Campaign Runner execution policy of expected duration 1,200 seconds, hard timeout 1,800 seconds, and per-run Hermes guidance of `--max-turns 300`, but the verified Hermes v0.20.5 top-level help did **not** advertise `--max-turns` or `--run-budget` as top-level CLI options. Re-check the installed command's help or the Campaign Runner adapter before using those values in a PowerShell Hermes launch command.

## STREAM DECK WORK

For Stream Deck profile, button, navigation, Riverview Operator, Quest Dev, or Stream Deck plugin work, read before modifying or diagnosing:

- `docs/operations/stream_deck/STREAM_DECK_CURRENT_INVENTORY.md`
- `docs/operations/stream_deck/STREAM_DECK_MAINTENANCE_AND_REPAIR_GUIDE.md`
- `docs/operations/stream_deck/STREAM_DECK_CURRENT_INVENTORY.json`

The installed configuration under the Elgato StreamDeck AppData tree is runtime truth. Re-inventory it before changes if Pat has made manual edits.

## OCTOMINER / REMOTE POWER WORK

For Octominer, OCTOMINER1/OCTOMINER2, Wake-on-LAN, WOL, SSH power control, fixed DHCP/IP allocation, AC-loss recovery, or Riverview compute-node remote-start work, read **`docs/operations/octominer/OCTOMINER_REMOTE_POWER_AND_WOL.md`** before modifying or diagnosing the node.

That document records the verified OCTOMINER1 MAC/IP/SSH state, AT&T fixed DHCP allocation procedure, X12 Ultra AC-loss auto-power-on test, persistent systemd `.link` WOL configuration, real Magic Packet wake test, and the repeat procedure for OCTOMINER2.

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
