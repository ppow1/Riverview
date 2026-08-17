<!-- Version: 0.4.0 -->
# Riverview AI Hints

Status: Canonical fast-recovery entry point.

Pat is the Steward and final authority. Grace coordinates operational progression but is not the whole Estate at Riverview.

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

For governed external-AI ingress and progress queries, first discover the
separate `Riverview_Comms_5` surface using `comms5_help`. Local clients may use
`python -m riverview.mcp.comms5_server` over STDIO; external clients must use
the approved deployed HTTPS MCP URL recorded by the deployment evidence, not a
loopback address. Use its bounded seed or durable specification-reference
operations, ask the Steward before gated promotion unless explicit standing
authorization exists, and use `comms5_seed_lineage` to follow authoritative
progress. Comms5 client identity is provenance, not authority; never mutate
PostgreSQL directly or invent objective/work state.
