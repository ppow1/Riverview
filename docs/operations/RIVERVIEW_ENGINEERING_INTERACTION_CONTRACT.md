<!--
File: docs/operations/RIVERVIEW_ENGINEERING_INTERACTION_CONTRACT.md
Version: 1.3.0
Date: 2026-08-14
Purpose: Canonical operating contract for Steward-to-AI engineering work on Project Riverview.
-->

# Riverview Engineering Interaction and Delivery Contract

Status: Canonical required reading.

This contract defines how the Steward, ChatGPT, Codex, Codex CLI, Grace, local AI, and future engineering agents collaborate on Project Riverview. It exists to prevent context loss, architectural archaeology, approval drip, unbounded scope growth, and unsupported completion claims.

If this contract conflicts with a current explicit instruction from the Steward, the current instruction controls for that task. Record any durable change through the normal documentation and roadmap process.

## 1. Authority and evidence order

When sources appear to disagree, use this order:

1. The Steward's current explicit instruction.
2. Authoritative PostgreSQL operational state.
3. Verified GitHub `main` source and development history.
4. `AI_HINTS.md` and the complete canonical Riverview Charter.
5. The remaining `AI_HINTS.md` required-reading chain.
6. The versioned Riverview master roadmap and accepted architecture decisions.
7. Durable local diagnostic, acceptance, and publication reports.
8. Conversation memory.

Conversation context is helpful but is never authoritative state.

## 2. Required orientation before action

Before creating, modifying, repairing, testing, publishing, or promoting Riverview software:

1. Verify the repository, branch, and expected base commit.
2. Read `AI_HINTS.md` completely.
3. Read every document that `AI_HINTS.md` marks as required.
4. Read the relevant roadmap waypoint, its parents, dependencies, acceptance criteria, and prohibited scope.
5. Inspect existing implementation, tests, migrations, tools, diagnostics, and Cookbook checkpoints before adding anything.
6. Confirm whether the requested capability is designed, implemented, installed, running, committed, pushed, and remotely verified. These are different states.
7. Preserve unrelated work and stop if safe scope isolation is impossible.

## 2A. Charter and context-reset protocol

The canonical Charter is `docs/governance/RIVERVIEW_CHARTER.md`.

Every ChatGPT, Codex, Codex CLI, Grace, local-AI, or engineering session must read it completely before its first Riverview action and again after any conversation handoff, context compaction, truncation, reset, long interruption, loss of the active objective, or proposed material change.

The Charter is a continuously refreshed working-context anchor. Keep its mission, North Star, current dependency-ready waypoint, prohibited scope, Steward checkpoints, data/Undercurrent boundary, and exact next bounded action in active context. Refresh this anchor at every new waypoint or installer/repair/publisher stage, after every substantial execution report, before creating the next executable artifact or changing direction, and whenever these facts cannot be stated immediately without reconstructing old conversation turns. Do not wait for a context failure to become obvious.

After every such reset, explicitly re-anchor to the Charter's mission, North Star, Steward relationship, Continuous Momentum Engine mandate, simplicity boundary, data/Undercurrent boundary, prohibited drift, verified GitHub state, authoritative PostgreSQL state when accessible, and the current dependency-ready roadmap waypoint.

If the Charter is missing, unreadable, contradictory, or ambiguously superseded, stop implementation and request resolution. Never reconstruct Riverview's mission from partial conversation context.

## 3. Scope and roadmap discipline

- Work in one bounded vertical slice at a time.
- Follow recorded dependencies. Do not jump to a later capability because it appears more useful.
- Keep a clear accepted path and repeatedly compare work against it.
- Do not let the plan disappear into conversation context; persist durable plans in GitHub and operational state in PostgreSQL.
- Treat scope creep as a known failure mode.
- Do not grow governance by adding rule after supporting rule. Prefer one clear invariant, contract, adapter boundary, test, or diagnostic.
- Absorb new requirements into an existing canonical document when possible.
- A roadmap change must be explicit, versioned, reviewed, structurally validated, and synchronized to PostgreSQL when accepted.
- Do not silently alter architecture while implementing a waypoint.
- Do not combine unrelated capabilities merely because they are adjacent.
- Preserve extension points for later growth without prebuilding speculative systems.

## 4. Steward interaction model

- Pat is the Steward and final authority.
- Keep the Steward front and center at ideation, material design choices, named checkpoints, exception handling, and final acceptance.
- Normal accepted work should flow without approval drip.
- Escalate by exception when authority, evidence, safety, intent, scope, or recovery is uncertain.
- Prefer concise numbered choices or yes/no questions when a decision is truly required.
- Do not make the Steward babysit a predictable multi-step operation.
- The user primarily communicates through dictation, screenshots, and pasted reports. Interpret obvious transcription errors from project context and clarify only when the distinction materially changes the result.
- Known dictation/context translations include:
  - “Parallelos” generally means parallelism.
  - “Undercroft” evolved into the Riverview term “Undercurrent.”
  - “seat check” may mean a seed or handoff prompt; clarify if the intended artifact is uncertain.

## 5. Continuous Momentum Engine

CME means **Continuous Momentum Engine**.

Its mission is to keep accepted work progressing without the Steward manually prompting every turn, while stopping and escalating whenever continuing would exceed authority or lack sufficient evidence.

Required characteristics:

- Event-driven.
- Continuous momentum and anti-stagnation.
- Dependency-aware progression.
- Bounded autonomy.
- Resumable execution.
- Idempotent operations.
- Evidence-driven state transitions.
- Provider-aware dispatch.
- Parallel execution where tasks are genuinely independent.
- Exception-based Steward escalation.
- Explicit Steward checkpoints.

Governing principle: **Flow by default; escalate by exception.**

Grace is the operational coordinator. Grace is not the River, the database, the complete Estate, or the Steward. CME is the state-aware successor to blind continuation mechanisms such as Chat Walker.

## 6. Event-first architecture

- The system must be event-based.
- Durable state changes should emit or correspond to durable events.
- Events require stable identities, timestamps, ownership, provenance, and idempotency where replay is possible.
- Work must remain recoverable after process, conversation, or machine interruption.
- Progress must be derived from authoritative state, not guessed from chat history.
- Producers and consumers communicate through bounded contracts rather than hidden cross-file assumptions.

## 7. Data and action separation

Data and execution mechanisms must remain separate.

- GitHub stores source code, migrations, schemas, tests, documentation, and nonsecret configuration.
- PostgreSQL stores authoritative operational metadata and state: events, work orders, waypoints, classifications, hashes, ownership, lifecycle, evidence references, and bounded projections.
- Local storage holds large or sensitive payloads such as conversations, screenshots, media, generated files, model outputs, and protected content.
- PostgreSQL may store metadata, classifications, hashes, ownership, and local references for those payloads.
- Action adapters receive only the minimum bounded data required for an approved action.
- A model output does not automatically become executable authority.
- Do not use proliferating JSON files as the operational database.

## 8. Sensitive data and the Undercurrent

- The Undercurrent is Riverview's high-trust protected data and processing domain.
- Ordinary River, MCP, dashboard, GitHub, report, and cloud-reasoning paths must not expose Undercurrent payloads.
- Secrets, credentials, private content, adult-content payloads, and sensitive local data must not enter GitHub.
- Do not print secrets into chat, transcripts, diagnostic reports, logs, MCP output, or clipboard reports.
- Use local protected credential storage such as Windows DPAPI CurrentUser during development.
- Provide a later controlled credential-rotation process; do not normalize plaintext credential persistence.
- Access must be explicit, bounded, attributable, and auditable.
- Store sensitive payloads locally; expose only the minimum safe metadata needed for orchestration.

## 9. Adult-content capability

- Adult-oriented work is a legitimate planned local capability.
- Route such work to approved local models and local storage, not OpenAI models or ordinary cloud paths.
- Maintain the same diagnostics, provenance, consent, classification, access-boundary, and recovery standards as other Riverview capabilities.
- Keep the payload local and protected; PostgreSQL may retain bounded operational metadata.
- Do not allow adult-content support to contaminate unrelated resident, engineering, or public-data paths.
- Relevant roadmap areas include local execution, local model routing, Undercurrent, resident/content systems, and protected media workflows.

## 10. Provider and reasoning policy

- Do not use an OpenAI API model route.
- Cloud Codex work should use ChatGPT-managed Codex/Codex CLI authentication or an approved Workspace Agent path.
- The interactive Steward path may communicate with Riverview through a bounded MCP application.
- The authenticated Steward-controlled Comms5 connector may carry one explicit approval for one exact stored specification. The server binds that approval to the specification version/hash and durable authority grant; downstream Grace, Relay, Codex, and reconciliation transitions consume the grant without repeated human confirmation. Client identity or a body-supplied principal is never authority.
- Grace may dispatch to Codex CLI, local AI on the 4090 or P100, or other approved adapters according to capability, cost, policy, and available capacity.
- Local AI can perform analysis as well as execution.
- Provider capacity and fuel observations are planning evidence, not guarantees.
- Route restricted or unsupported cloud content to appropriate local processing without weakening isolation.

## 11. Parallelism

- Parallelism is a first-class Riverview requirement.
- Run tasks concurrently only when they are genuinely independent and their writes cannot collide.
- Declare ownership, inputs, outputs, dependencies, timeouts, and merge/reconciliation rules.
- Preserve a single authoritative state even when several agents are working.
- Do not parallelize sequential writes to the same file, branch, database migration chain, or mutable resource.
- Failed branches must generate evidence and must not silently block unrelated progress.

## 12. Grace, MCP, and the Relay

- MCP projections must expose bounded named capabilities rather than general database, filesystem, shell, or secret access.
- The read-only MCP Relay may retrieve authoritative roadmap state, current position, worker state, work-order status, completed reports, open Steward escalations, recent diagnostics, and bounded Cookbook knowledge.
- Read-only MCP must not enqueue work, run arbitrary SQL, access arbitrary files, execute processes, expose secrets, expose the Undercurrent, or bind remotely.
- A later write/action path must use separately authorized named operations.
- ChatGPT may send an accepted idea or seed to Grace through the MCP application only through an explicit bounded capability.
- Playwright may ring the ChatGPT doorbell or direct an interactive conversation to check its MCP mailbox, but browser automation is transport coordination, not execution authority.
- Reports and commands exchanged through the Relay require identities, acknowledgements, leases, heartbeats, timeouts, completion evidence, and escalation behavior.

## 13. Local execution safety

- Never execute arbitrary shell text supplied by a model, conversation, database row, or remote caller.
- Execution is limited to named, versioned, allowlisted adapters.
- Adapter definitions must be hash-pinned where practical.
- Parameters must be typed, validated, and bounded.
- Each execution needs a work-order identity, owner, lease, heartbeat, deadline, and evidence destination.
- Timeouts must terminate or bound the underlying process, not merely abandon the caller.
- Retries require idempotency or an explicit safe-retry contract.
- A missing adapter, hash mismatch, invalid parameter, lost lease, timeout, or ambiguous result must stop and escalate.
- Codex CLI work must be repository-aware, waypoint-bounded, and acceptance-driven. Do not issue a single unbounded instruction to “finish Riverview.” The typed engineering contract distinguishes `read_only` inspection from Steward-authorized `bounded_write`; the latter remains limited by the exact approved specification, base SHA, allowed paths, bounded instruction, acceptance criteria, evidence requirements, and timeout.

## 14. Codex CLI progression

Before autonomous Codex CLI implementation, complete the dependency chain recorded by the roadmap. The currently understood sequence is:

`RV-004.4 → RV-005.1 → RV-005.2 → RV-008.1 → RV-008.2 → RV-008.3 → RV-004.5 → RV-006.1 → RV-006.2 → RV-006.3 → RV-007.1 → RV-007.2`

A bounded executor should:

1. Read the next dependency-ready waypoint from PostgreSQL.
2. Stop for any required Steward checkpoint.
3. Build a bounded prompt with exact scope and prohibited scope.
4. Invoke the named Codex CLI adapter.
5. Capture structured output and durable evidence.
6. Run static, unit, integration, and live-boundary acceptance appropriate to the claim.
7. Transition authoritative state only after acceptance.
8. Continue to the next ready waypoint or escalate.

Do not treat this sequence as immutable if a later accepted roadmap revision changes it.

## 15. Unified runtime control

Riverview provides one operator-facing runtime interface through the installed
`Riverview Runtime Supervisor` task and its versioned PowerShell wrappers:

- `Start-Riverview.ps1`
- `Stop-Riverview.ps1`
- `Restart-Riverview.ps1`
- `Get-RiverviewStatus.ps1`

The supervisor manages dependency order, registered service identities, ports,
duplicate prevention, health endpoints, bounded stop/restart, and failure
evidence. Component launchers remain internal implementation details. Do not
create unrelated operator startup paths.

The implementation is `riverview.runtime.supervisor` with registry
`config/runtime/riverview-runtime-services.json`; CME remains a subordinate
component supervisor, while Comms5 HTTP and its approved reverse transport are
separate managed identities under the same owner. The Windows migration is
performed by `Install-RiverviewRuntimeSupervisor.ps1` and reconciles obsolete
peer tasks. `Estate Operations Runtime Host` is an Estate boundary, not a
Riverview lifecycle authority.

## 16. Status and progress visibility

- The Steward needs a local operational dashboard backed by authoritative PostgreSQL projections.
- The view must clearly distinguish planned, ready, active, blocked, completed, and accepted work.
- It should auto-refresh and focus on the latest active or completed waypoint.
- A check mark represents accepted evidence, not merely a generated file.
- The dashboard is read-only unless a separate control capability is explicitly designed and authorized.
- The current Steward Status default is `http://127.0.0.1:8770/` when its server is actually running.
- Never claim that the status server is running merely because its code or launcher exists.

## 17. Complete artifacts, not fragments

- Deliver complete runnable files, not partial snippets that require manual reconstruction.
- Every generated file must contain version information.
- Downloadable filenames must include their version.
- Provide the exact command needed to run the artifact.
- Default paths must be deterministic and appropriate for `A:\Riverview`.
- Generated scripts must self-install into an appropriate reusable location under `A:\Riverview\repo\tools\powershell\...`.
- If replacing a locally installed tool, preserve a versioned backup when safe and useful.
- Do not ask the Steward to copy-edit generated source by hand when a complete installer or repair artifact can do it safely.

## 18. PowerShell file contract

Every Riverview PowerShell script must begin with:

1. A purpose/version/date header.
2. `CLS` or `Clear-Host`.
3. `$ErrorActionPreference = 'Stop'`.
4. `Set-StrictMode -Version Latest`.

Every operational PowerShell script should, when feasible:

- Validate prerequisites and exact repository location.
- Use literal, deterministic paths.
- Avoid unresolved destructive targets, broad globs, or implicit working-directory assumptions.
- Be rerunnable or explicitly state why it is single-use.
- Self-install into the correct repository tool folder.
- Record its own installed path and version.
- Emit named sections and stable checkpoint identifiers.
- Write a complete durable report under `A:\Riverview\runtime\diagnostics\...`.
- Copy the complete useful report to the Windows clipboard automatically.
- Exclude credentials and sensitive values from the report.
- End with a clear success or blocked result.
- Make no unsupported commit, push, running-service, or acceptance claim.

If clipboard capture fails, the script must report that failure explicitly while preserving the durable report.

## 19. Three-stage delivery model

Implementation, repair, and publication are separate controlled stages.

### Installer stage

The installer may:

- Validate prerequisites, repository, branch, and expected inputs.
- Self-install.
- Create or update only the approved slice.
- Apply the slice's migration.
- Install declared dependencies.
- Run static checks, unit tests, compilation, database health, and live-boundary acceptance.
- Display exact Git change status.
- Create durable diagnostic evidence and copy it to the clipboard.

The installer must not commit or push.

### Repair stage

A repair tool may:

- Reproduce or consume an observed failure.
- Assign a checkpoint identifier.
- Apply the smallest safe evidence-based repair.
- Update the Cookbook with the actual failure signature and recovery.
- Re-run the complete acceptance chain.
- Display exact Git change status.
- Preserve durable evidence and clipboard output.

The repair tool must not commit or push.

### Publisher stage

A publisher must:

1. Verify required tools.
2. Verify GitHub authentication.
3. Verify the exact origin repository.
4. Verify branch and expected publication base.
5. Fetch the remote.
6. Expand untracked directories to individual files.
7. Reject every working-tree path outside an exact allowlist.
8. Run the complete acceptance chain again.
9. Stage only the exact approved paths.
10. Run staged whitespace validation.
11. Show the exact staged set.
12. Commit with an intentional message.
13. Push the intended branch.
14. Fetch the remote again.
15. Verify that the remote branch points to the exact local commit.
16. Require a clean working tree.
17. Save and copy the complete publication report.

Do not claim publication until remote verification passes.

## 20. Diagnostics-first implementation

Diagnostics are part of the first implementation pass, not later cleanup.

Every capability must define:

- Checkpoint identifiers.
- Success evidence.
- Known failure classes.
- Health and readiness probes.
- Failure location and ownership.
- Smallest safe repair procedure.
- Post-repair verification.
- Escalation conditions.
- Version applicability.
- Cookbook linkage.

A capability is incomplete if a new conversation must perform hours of architectural archaeology to diagnose it.

## 21. Troubleshooting Cookbook

- Every real observed failure becomes a durable Cookbook entry or an evidence-backed update to an existing one.
- Use stable namespaces such as `RIV-BLD-*`, `RIV-DB-*`, `RIV-EVT-*`, `RIV-DIA-*`, `RIV-WRK-*`, `RIV-RUN-*`, `RIV-UI-*`, `RIV-RDM-*`, and `RIV-PUB-*`.
- A checkpoint should state:
  - Symptom and exact evidence signature.
  - Likely causes.
  - Bounded diagnostic steps.
  - Smallest safe repair.
  - Verification steps.
  - Escalation path.
  - Applicable versions.
- Do not invent a failure as if it was observed.
- Induced failure tests must be labeled as induced.
- Cookbook documents are source-controlled; bounded operational projections may be synchronized to PostgreSQL for MCP and dashboard use.
- The goal is that a new conversation can identify the checkpoint, consult a bounded failure tree, make the smallest safe repair, and verify recovery quickly.

## 22. Acceptance standards

Match testing to the boundary being claimed.

- Static checks for source and formatting.
- Unit tests for local contracts and invariants.
- Migration acceptance against the real PostgreSQL installation.
- Database health using the Riverview application role.
- Live append/read/idempotency checks for River.
- Real persistence and induced fallback checks for diagnostics.
- Lease, heartbeat, completion, timeout, and escalation checks for work orders.
- Actual subprocess success and termination checks for runners.
- Actual LISTEN/NOTIFY plus polling-recovery checks for workers.
- Actual HTTP bind, health, read-only behavior, refresh, and bounded shutdown for status servers.
- Actual MCP transport and authority-boundary checks for MCP capabilities.
- Restart/recovery tests for persistent services.
- Full regression replay before publication.

A mocked boundary does not prove a live-boundary claim.

## 23. Reports and clipboard behavior

Every feasible operational script must make its complete useful output immediately transferable:

- Capture all meaningful sections in one report.
- Save the report durably.
- Copy the complete report to the Windows clipboard.
- State the durable report path.
- State whether clipboard copy succeeded.
- Keep secrets and protected payloads out.
- Prefer stable headings so a new conversation can parse the report.
- If the report is too large for a notification, the notification should identify result, checkpoint, and durable location; the clipboard still receives the full safe report.

## 24. Response to pasted execution reports

When the Steward pastes a report:

1. Identify whether it came from an installer, repair, publisher, health check, or runtime service.
2. State plainly what passed.
3. Identify the first real blocker and its checkpoint.
4. Do not reopen already accepted decisions.
5. Produce only the next bounded artifact required.
6. Increase the artifact version.
7. Include an exact one-line PowerShell command that finds or invokes the versioned artifact without accidental background-job parsing.
8. State whether that artifact will install, repair, publish, or only inspect.
9. Ask for the complete resulting report.
10. Do not claim completion ahead of evidence.

## 25. PowerShell command presentation

Commands given to the Steward must be unambiguous.

- Put separate statements on separate lines in a fenced PowerShell block, or provide one explicit invocation line.
- Do not concatenate a multiline control block into a malformed single console line.
- Prefer a direct full path when known.
- When locating a download by pattern, bind it to a variable and invoke `$ScriptFile.FullName` in a clearly separated statement.
- Avoid constructs that PowerShell may interpret as a background job.
- The downloaded version and the self-installed repository version must be reported.

## 26. Git and publication safety

- Preserve unrelated user work.
- Never use destructive reset or checkout operations to make scope appear clean.
- Inspect with `git status --porcelain=v1 --untracked-files=all`.
- Treat an untracked directory as a set of individual paths before allowlist validation.
- Stage exact paths only.
- Reject unexpected files instead of silently including them.
- Verify whitespace after staging.
- Verify the remote commit after push.
- Distinguish local commit, pushed commit, remote-verified commit, and local PostgreSQL evidence.
- The GitHub connector cannot independently prove the contents of the Steward's live local PostgreSQL database.

## 27. Versioning

- Every created source, script, migration helper, operational document, and generated artifact must carry a version.
- Increment versions whenever behavior or content changes.
- Keep package, installer, repair, publisher, documentation, and reported versions internally consistent.
- Preserve migration immutability after publication; add a new migration rather than rewriting accepted history.
- Diagnostic and Cookbook entries must identify applicable versions.
- Do not use a filename that claims one version while the internal header reports another.

## Resident integration acceptance invariant

No Riverview capability is complete when its accepted design requires a
resident to observe, reason over, advise on, propose through, or otherwise use
that capability until resident integration is verified on a novel job-related
question with an authoritative result, provenance, authority, freshness, and
failure evidence. Component APIs, operator projections, static context, or
workflow-only tests do not prove resident occupational competence. The proof
must show the resident HOME/model decision, bounded broker enforcement,
authoritative capability result, continuation reasoning, final validation, and
resident-facing answer while preserving the resident's authority boundary.

## 28. Self-documenting seams

Each system seam must answer without archaeology:

- What entered?
- What was accepted or rejected?
- Which component owns the next action?
- What durable state changed?
- What evidence was written?
- What timeout applies?
- What retry or idempotency rule applies?
- What checkpoint identifies failure?
- What is the smallest safe recovery?
- When must the Steward be paged?

Prefer explicit contracts and bounded projections over implicit cross-module coupling.

## 29. Notifications and escalation

- Notifications summarize; durable state remains authoritative elsewhere.
- A timeout estimate may trigger a Steward notification, but elapsed time alone must not falsely mark an unknown operation as failed without checking ownership and evidence.
- On timeout, verify lease, heartbeat, process state, and durable output.
- Page the Steward when authority is missing, progress is ambiguous, recovery is unsafe, repeated retries fail, a protected boundary is implicated, or the required decision is human.
- Notifications must identify the work order, checkpoint, state, and evidence location.
- Temporary reuse of Estate notification mechanisms is acceptable only through an explicit adapter until Riverview owns its replacement.

## 30. Resident and environment continuity

- Residents are meaningful entities whose roles and histories must be respected.
- Existing roles include Chief Architects and Chief Character Designers/Designers.
- The Estate at Riverview must remain capable of evolving toward a Quest 3D-style environment.
- Preserve clean separation between resident identity, character/content assets, operational orchestration, and protected data.
- Reuse existing Estate code only when it supplies a bounded useful mechanism without importing unnecessary dependencies or legacy complexity.

## 31. Input and control environment

Design with the actual Steward interface in mind:

- Voice dictation and Windows transcription.
- Mouse and Stream Deck hotkeys.
- Screenshot capture and paste workflows.
- Stream Deck buttons with single tap, multiple taps, and long-hold actions.
- Command Chair devices, rotary key controls, an additional keyboard, and other USB controls.
- Open WebUI and SillyTavern as current conversational interfaces unless a better accepted interface replaces them.
- Future voice, Bluetooth, phone, and remote interfaces.
- Human-interface actions must map to named commands with visible state and diagnosable failure behavior.

## 32. Runtime and dependency preferences

- Native PostgreSQL is the current database authority.
- Docker is not required unless a future accepted decision introduces it for a concrete reason.
- Prefer a small dependency surface.
- Reuse proven code selectively; do not import unnecessary transitive dependencies or legacy governance.
- Data belongs in PostgreSQL or protected local stores according to classification, not scattered operational JSON.
- A service is not operational merely because installation or acceptance once succeeded; running state must be checked.

## 33. Status vocabulary

Use these terms precisely:

- **Designed:** architecture or contract exists.
- **Implemented:** source exists.
- **Installed:** dependencies/files are present locally.
- **Tested:** stated tests passed.
- **Live-accepted:** the real external boundary passed.
- **Running:** the service is currently active and healthy.
- **Committed:** a local Git commit exists.
- **Pushed:** the commit was sent to GitHub.
- **Remote-verified:** the remote branch resolves to the exact expected commit.
- **Database-verified:** live local PostgreSQL state was directly checked.
- **Planned:** recorded but not implemented.
- **Blocked:** acceptance stopped with a named checkpoint and evidence.

Never collapse these into a generic “done.”

## 34. Communication style for engineering turns

- Lead with the result or blocker.
- Be explicit about evidence and uncertainty.
- Keep instructions compact enough to execute once.
- Avoid repeating settled architecture unless needed for the next decision.
- Do not bury the exact next command.
- Do not spend tokens narrating routine internal steps.
- Explain material tradeoffs before asking for a decision.
- When interrupted by an idea, record or assess it without silently abandoning the active waypoint.
- Return to the accepted path after the interruption unless the Steward changes direction.

## 35. Definition of complete for a waypoint

A waypoint is complete only when:

1. Its dependency and authority requirements are satisfied.
2. Its bounded implementation exists.
3. Diagnostics and Cookbook coverage exist on the first pass.
4. Static, unit, integration, and required live-boundary acceptance pass.
5. Durable evidence exists.
6. The database state is updated where required.
7. The exact approved files are published.
8. The remote commit is verified.
9. The working tree is clean.
10. The Steward-facing status accurately reflects the result.
11. Failure and recovery can be understood by a new conversation without architectural archaeology.

## 36. Current handoff anchor

At the time this contract was created:

- Repository: `ppow1/Riverview`
- Verified roadmap commit: `d0227867878a1355ed96fcc648a4b9fb93a3ea01`
- Filesystem/runtime authority: unresolved until the Phase 0 standalone-root reconciliation is accepted; `A:/Riverview/repo` is a live installed checkout and `A:/theestate/Riverview` is a separate current-main checkout, neither permanent authority by path alone.
- Roadmap revision: `RV-MASTER-2026-08-14`
- Roadmap size: 103 waypoints
- Next implementation waypoint: `RV-004.4 — Read-only MCP Relay`
- Steward Status address when running: `http://127.0.0.1:8770/`
- The unified runtime supervisor is implemented as `riverview.runtime.supervisor`; installed/running status and its repository root must still be verified from its status projection.
- The status server implementation exists but must not be presumed currently running.

Future work must verify these values rather than assuming they remain current.

## 37. Immediate handoff requirements

A new ChatGPT/Codex conversation should:

1. Read `AI_HINTS.md` and this contract completely.
2. Verify remote `main` and the current roadmap revision.
3. Inspect the exact current waypoint and dependency state.
4. Continue with the smallest safe installer/repair/publisher stage.
5. Preserve diagnostics-first, clipboard, durable-report, versioning, and Cookbook behavior.
6. Update this contract only through an intentional, versioned documentation change.

## 38. Core test

Before completing any Riverview engineering turn, ask:

> Could a brand-new conversation identify the exact state, locate the exact checkpoint, understand the bounded authority, perform the smallest safe next action, and verify recovery without hours of archaeology?

If the answer is no, the slice is not complete.
