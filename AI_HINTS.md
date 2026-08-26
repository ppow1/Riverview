<!-- Version: 0.6.0 -->
# Riverview AI Hints

Status: Canonical fast-recovery entry point.

Pat is the Steward and final authority. Grace coordinates operational progression but is not the whole Estate at Riverview.

Riverview is a separate successor/replacement system, not a subsystem of The Estate. The Estate remains the legacy operational system while Riverview replaces its capabilities incrementally. Filesystem paths are provenance only; no permanent standalone Riverview root is established until the Phase 0 repository/runtime reconciliation is accepted. Read `docs/operations/roadmap/evidence/RIVERVIEW_RUNTIME_REPOSITORY_PROVENANCE_MAP_PHASE0_2026-08-26.md` before changing runtime ownership or selecting a repository root.

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
