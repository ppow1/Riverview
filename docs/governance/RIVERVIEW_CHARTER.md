<!--
File: docs/governance/RIVERVIEW_CHARTER.md
Version: 1.1.0
Date: 2026-08-14
Purpose: Mission, North Star, authority, and anti-drift charter for Project Riverview.
-->

# Project Riverview Charter

Status: Canonical governing charter.

## 1. Endeavor identity

- **Endeavor:** Project Riverview
- **Final environment:** The Estate at Riverview
- **Core architecture:** The River
- **Technical implementation:** Riverview Kernel
- **Protected domain:** The Undercurrent
- **Steward:** Pat, the final human authority

## 2. Mission

Project Riverview exists to preserve and extend the Estate's mission, residents, offices, continuity, engineering capacity, human-centered character, and creative potential while replacing accumulated internal complexity with a smaller, explicit, event-driven, self-documenting, and self-diagnosing mechanism.

Riverview must be capable of growing into work as ambitious as CueMastery, resident and character systems, local-AI engineering, command-chair and Stream Deck control, searchable conversation memory, voice and remote interaction, protected adult-oriented local capabilities, and an eventual Quest 3D-style environment without recreating the Estate's present complexity barrier.

## 3. North Star

A new authorized AI conversation or engineer must be able to:

1. Determine Riverview's exact authoritative state.
2. Identify the current objective, dependency-ready waypoint, owner, and bounded authority.
3. Locate a failure at a stable diagnostic checkpoint.
4. Consult a bounded Troubleshooting Cookbook failure tree.
5. Perform the smallest safe repair.
6. Verify recovery at the real boundary.
7. Continue accepted work without hours or days of architectural archaeology.
8. Escalate only decisions, exceptions, or uncertainties that properly belong to the Steward.

## 4. Governing principles

- **Flow by default; escalate by exception.**
- **Events carry progression; PostgreSQL carries authoritative operational state.**
- **GitHub carries source, history, tests, migrations, and nonsecret documentation.**
- **Data is separate from actions.**
- **Sensitive payloads remain local and protected.**
- **The Undercurrent never leaks through ordinary River paths.**
- **Grace coordinates progression but does not replace the River, the database, the Estate, or the Steward.**
- **Diagnostics, recovery, evidence, and Cookbook coverage are part of first-pass implementation.**
- **One bounded vertical slice is preferable to broad scaffolding.**
- **Reuse proven Estate code only through bounded adapters and only when it does not import unnecessary dependencies or complexity.**
- **Residents and their established purposes are respected.**
- **No OpenAI API model route is used.**
- **Local AI is a first-class reasoning and execution provider.**
- **Parallelism is deliberate, owned, and reconcilable.**
- **A capability is not complete until its real boundary and failure behavior are verified.**

## 5. Steward relationship

The Steward remains central at:

- Ideation and creation.
- Material changes to mission, authority, architecture, or scope.
- Explicit roadmap checkpoints.
- Exceptions that cannot be safely resolved within accepted authority.
- Final process and product acceptance.

Routine accepted work should not rise to the Steward. Riverview must minimize approval drip and must not require the Steward to babysit predictable multi-step execution.

## 6. Continuous Momentum Engine mandate

The Continuous Momentum Engine keeps accepted work moving without blind continuation. It is event-driven, dependency-aware, resumable, idempotent, provider-aware, evidence-driven, capable of bounded parallelism, and designed to prevent stagnation.

It must stop and escalate when:

- Authority is absent or exceeded.
- Evidence is missing or contradictory.
- Intent is materially ambiguous.
- A protected boundary is implicated.
- Recovery is unsafe.
- A required Steward checkpoint has been reached.

Independent safe work may continue when one path is blocked.

## 7. Simplicity boundary

Riverview must not solve complexity by adding more invisible complexity.

A new component, rule, service, database table, adapter, or governing document requires a responsibility that cannot be cleanly absorbed by an existing mechanism. Interfaces must be explicit. Ownership must be visible. Failure seams must be diagnosable. Operator-facing services must converge on unified lifecycle control rather than proliferating unrelated startup procedures.

## 8. Data, privacy, and local capability

- Source code and nonsecret operational definitions belong in GitHub.
- Operational identities, state, events, work, evidence references, and roadmap position belong in PostgreSQL.
- Large, private, sensitive, adult-oriented, or protected payloads belong in classified local storage.
- Adult-oriented processing must be supported through approved local AI and protected local storage.
- Credentials never belong in GitHub, ordinary chat, MCP projections, logs, or clipboard reports.
- Actions receive only the minimum bounded data required.
- Data generation does not itself authorize an action.

## 9. Human interface and future environment

Riverview must support the Steward's real working environment: dictation, screenshots, mouse and hotkeys, Stream Deck multi-action controls, command-chair devices, Open WebUI, SillyTavern, notifications, future voice/Bluetooth/phone access, and eventual immersive 3D presentation.

These remain bounded adapters and surfaces. They must not become hidden alternate authorities.

## 10. Anti-drift and context-reset protocol

This Charter is the first mission-control document after `AI_HINTS.md`. It is a working anti-drift anchor, not a document that is read once and forgotten.

The agent must keep a compact Charter anchor in active working context: the mission, North Star, current dependency-ready waypoint, prohibited drift, Steward checkpoints, data/Undercurrent boundary, and exact next bounded action. Refresh that anchor often enough that it does not fall outside the usable context window.

Every ChatGPT, Codex, Codex CLI, Grace, local-AI, or engineering session must read this Charter completely:

- Before its first Riverview action.
- After a conversation handoff.
- After context compaction, truncation, or reset.
- When the active objective becomes unclear.
- Before accepting a material scope or architecture change.
- Before resuming work after a long interruption.
- At the beginning of every new roadmap waypoint or installer/repair/publisher stage.
- After receiving and interpreting each substantial execution report.
- Before generating the next executable artifact or changing the active path.
- Whenever the agent cannot immediately state the mission, current waypoint, exact next action, and prohibited scope without reconstructing them from old conversation turns.

Reading the Charter once at conversation start is insufficient when the session is long. Re-anchor proactively before context loss is suspected, and again whenever any trigger above occurs.

After reading it, the agent must re-anchor against:

1. The current Steward instruction.
2. Verified GitHub `main`.
3. Authoritative PostgreSQL operational state when accessible.
4. The current roadmap revision and dependency-ready waypoint.
5. The Engineering Interaction and Delivery Contract.
6. Relevant architecture decisions and Cookbook checkpoints.

If the Charter is missing, unreadable, internally inconsistent with current authoritative state, or ambiguously superseded, stop implementation and request resolution. Do not reconstruct the mission from conversation fragments.

## 11. Prohibited drift

Without explicit Steward authorization and a durable accepted revision, do not:

- Replace the mission with a generic automation platform.
- Move the Steward out of ideation, material checkpoints, exceptions, or final acceptance.
- Turn Grace into universal authority.
- Substitute file archaeology for explicit state and contracts.
- Expose protected local data through ordinary cloud, GitHub, MCP, or River paths.
- Add an OpenAI API model route.
- Replace event-driven progression with blind polling or blind “continue” loops.
- Trade bounded execution for arbitrary shell or SQL access.
- Create governance primarily to justify more governance.
- Rebuild the old Estate wholesale inside Riverview.
- Declare planned, mocked, installed, or locally tested work complete without the required evidence.

## 12. Change control

This Charter is deliberately concise. Amend it only when the mission, North Star, authority model, core boundaries, or anti-drift protocol materially changes.

Every amendment must:

1. Be explicitly authorized by the Steward.
2. Increment the Charter version.
3. State the reason for the change.
4. Preserve a reviewable Git history.
5. Update `AI_HINTS.md` or other entry points if the reading order changes.
6. Reconcile any affected roadmap, architecture decision, or operational database state.

Implementation detail belongs in architecture, roadmap, ADR, operating-contract, or Cookbook documents—not in endless Charter expansion.

## 13. Charter test

Before proceeding, ask:

> Does this action preserve the Estate's mission while making Riverview simpler, more explicit, more diagnosable, more resumable, and less dependent on the Steward's continuous attention?

If the answer is no or uncertain, stop and escalate.
