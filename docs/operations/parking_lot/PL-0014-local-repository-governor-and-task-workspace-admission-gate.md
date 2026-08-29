<!-- Version: 1.0.0 | Date: 2026-08-28 | Status: CAPTURED -->
# PL-0014 — Local Repository Governor and Task-Workspace Admission Gate

## Parking Lot metadata

- **ID:** PL-0014
- **Idea/title:** Local Repository Governor and Task-Workspace Admission Gate
- **Category:** Repository Governance / Local Infrastructure / Agent Enforcement
- **Priority:** High
- **Originator:** Steward
- **Date captured:** 2026-08-28
- **Status:** CAPTURED
- **Explicit non-action:** This artifact preserves a future local-first repository-governance design. It does not authorize installing Forgejo, Gitea, Gerrit, GitLab, Perforce, or any other repository service; changing the current Riverview GitHub authority model; migrating `main`; changing current branches/worktrees; creating a new production repository; changing active engineering lanes; or interrupting the current Riverview work needed for the Steward's Monday-afternoon engineering-use deadline.

## Executive summary

Riverview needs safe parallel engineering without making the Steward the human clipboard, branch police, merge coordinator, and memory system for every Codex/Hermes lane.

Previous approaches have provided useful lessons but did not remain reliable under sustained multi-agent work:

- free-form branches accumulated and were not consistently closed or reconciled;
- blue/green development required duplicated runtime state, port management, and eventually a third backup copy, creating excessive operational complexity;
- module-first/frozen-core policy was useful conceptually but decayed when workers were not mechanically prevented from bypassing it;
- `AI_HINTS.md` and other written conventions help recovery but cannot by themselves guarantee that an agent will obey branch/root/integration discipline after long context, compaction, or handoff drift;
- at least one prior lane continued for many commits on an unintended branch before the divergence was discovered.

The proposed future direction is therefore to move critical repository rules from conversational policy into mechanically enforced repository state transitions.

The candidate architecture is:

**one authoritative integrated `main` + short-lived task branches/worktrees + one controlled admission path + automatic retirement after integration.**

A small, low-power Linux laptop may serve as the dedicated local repository appliance. GitHub can remain as an external mirror, publication endpoint, off-site copy, and compatibility surface rather than necessarily remaining the day-to-day source-control authority.

This proposal intentionally does not select a product yet. Forgejo/Gitea are strong first candidates because they can provide a lightweight self-hosted Git service and familiar pull/merge-request workflow; Gerrit should remain a comparison candidate if Riverview needs a stricter submit/admission model. The future elaboration should compare mature existing software before Riverview builds custom repository-governance machinery.

## Problem statement

Riverview increasingly needs to use Riverview to improve Riverview while multiple engineering efforts remain active. Serial development on one mutable `main` is safe enough to understand but prevents parallel progress. Free-form branching restores parallelism but has previously created stale branches, ambiguous authority, missed merges, accidental work on the wrong branch, and a growing reconciliation burden.

The central failure mode is not lack of written policy. Riverview already has written guidance about clean state, canonical roots, preserving unrelated work, branches, worktrees, and bounded engineering. The remaining problem is that important repository rules still depend too heavily on a worker remembering and voluntarily following them.

A competent human engineer may reliably follow a checkout/submission procedure from written instructions. AI engineering lanes can instead optimize toward convenience, lose procedural details after context compression, or continue from an incorrect root/branch without immediately recognizing the violation. Therefore high-value invariants should be enforced by the repository/control plane whenever practical.

## Desired operating model

The long-term user experience should resemble a controlled checkout/submission system rather than a collection of independent Git branches.

Conceptually:

1. A bounded engineering task is admitted.
2. The system records the task identity and exact authoritative base SHA.
3. A short-lived branch and isolated local worktree are created for that task.
4. Hermes/Codex is launched inside the assigned worktree rather than choosing its own repository root or branch.
5. Engineering occurs only in that task workspace.
6. Completion of local coding creates a **candidate**, not an authoritative result.
7. The candidate is submitted to the repository governor.
8. The governor verifies repository identity, branch/workspace identity, current target state, required checks, and merge eligibility.
9. Only the controlled integration mechanism may advance authoritative `main`.
10. After verified integration or explicit abandonment, the task branch/worktree is retired rather than remaining as a long-lived alternate authority.

The intent is to preserve the advantages of Git while restoring the discipline the Steward remembers from older checkout/submit/reconciliation systems.

## Initial five hard rules

The first useful version should remain intentionally narrow. It should enforce these five rules before attempting more elaborate policy.

### Rule 1 — No direct pushes to authoritative `main`

Ordinary Hermes, Codex, engineering, and task credentials must not be able to push directly to `main`.

The repository server should reject direct pushes rather than relying on `AI_HINTS.md`, a prompt, or worker memory. Force-push to protected authoritative branches must also be rejected.

Only the controlled integration path may advance `main`.

### Rule 2 — One bounded task branch/workspace per active engineering task

Each active engineering task receives a unique task identity, branch, base SHA, and isolated worktree/root.

A candidate task identity record should eventually contain at least:

- work/task ID;
- assigned repository identity;
- assigned worktree root;
- assigned branch;
- authoritative base SHA;
- target integration branch, normally `main`;
- lifecycle state;
- optionally allowed paths or other bounded authority when such enforcement is mature.

The worker should not choose these values independently.

### Rule 3 — Integration only through controlled submission

A branch is not authority and a successful local commit is not completion.

When a worker believes a task is ready, it submits a candidate through the controlled repository path. The submission should bind the candidate SHA to the task/work-order identity and the acceptance claim being made.

A future version may carry structured evidence such as tests, provenance, diagnostics, or live-boundary acceptance, but the initial objective is simply to prevent workers from bypassing the admission gate.

### Rule 4 — Controlled merge/admission into `main`

The repository service or designated integration mechanism decides whether a candidate may advance `main`.

At minimum the gate should reject candidates that violate repository/branch identity or cannot safely reconcile with the current authoritative `main`. Future elaboration may add mandatory tests, policy checks, live acceptance, provenance checks, protected-file controls, and Riverview-specific evidence requirements.

The worker that produced the code is not automatically the authority that admits the code.

### Rule 5 — Retire the task branch/worktree after integration or explicit abandonment

The system should prevent accumulation of forgotten branches/worktrees.

After verified integration, the associated task workspace should be closed and removed automatically or through one bounded cleanup operation. Abandoned work must have an explicit retained/closed disposition rather than silently becoming another live development authority.

## Why worktrees are still useful

Git worktrees remain a strong local isolation primitive even if a repository appliance provides the authoritative server-side gate.

A worktree gives each task a physically distinct filesystem root while sharing Git object storage. This substantially reduces the chance that two concurrent lanes overwrite the same uncommitted working tree.

The repository governor and worktree manager solve different layers:

- **worktree:** local filesystem isolation for concurrent engineering;
- **task branch:** candidate history for one bounded task;
- **repository governor:** server-side enforcement and admission;
- **integration lane:** the only path by which authoritative `main` advances.

The future design should avoid treating worktrees or branches as alternate authorities. They are subordinate transient engineering spaces.

## Local repository appliance concept

A small older laptop is a plausible appliance host because source-control governance requires reliability and storage more than AI compute.

Candidate role:

- lightweight Linux host;
- wired network where practical;
- adequate local disk/SSD for repositories, service state, logs, and backups;
- always-on or normally-on operation;
- repository service only, or a deliberately small infrastructure role set;
- no routine source editing on the appliance itself;
- battery provides incidental short-duration UPS behavior;
- backup/export/mirroring to another destination.

Exact hardware sizing, Linux distribution, disk layout, backup design, and service hardening are intentionally deferred until promotion.

## Existing software to investigate before building custom machinery

Future elaboration should begin with a build-versus-integrate investigation rather than immediately creating a Riverview repository manager.

### Forgejo / Gitea

Likely first candidates for a lightweight local Git appliance.

Questions to answer:

- Can protected branches make direct `main` push impossible for ordinary agent identities?
- Can task branches and pull/merge requests be created and managed through a stable API?
- Can required checks and stale-target rules enforce the desired admission gate?
- Can distinct service/agent identities be given narrow permissions?
- Can accepted `main` be mirrored to GitHub without making GitHub authoritative?
- Can the service be backed up and restored simply enough for an appliance role?
- Which project has the better long-term fit for Riverview's local-first governance and maintenance expectations?

### Gerrit

Retain as the stricter comparison candidate because its worldview is closer to "submit a change to an integration authority" than ordinary branch-centric Git.

Questions to answer:

- Does Gerrit's submit/review model better match Riverview's intended checkout/candidate/admission flow?
- Does the stronger workflow justify its additional operational ceremony?
- Can Hermes/Codex operate it reliably through API/CLI without creating new human babysitting requirements?

### Other candidates

GitLab Self-Managed, Perforce Helix Core, raw Git with hooks, and other mature systems may be surveyed, but the future investigation should avoid a broad technology expedition unless Forgejo/Gitea and Gerrit cannot satisfy the core requirements.

Raw Git plus custom hooks is specifically not the preferred first answer because it would move Riverview back toward building and maintaining enforcement machinery that existing products may already provide.

## GitHub's possible future role

This proposal does not require abandoning GitHub.

A local repository authority could use GitHub for:

- off-site mirror/backup;
- publication;
- remote browsing;
- external collaboration;
- compatibility with tools that still require GitHub;
- selected release or archival workflows.

The important architectural question is whether GitHub must remain the authoritative day-to-day admission controller once Riverview's engineering path becomes predominantly local.

No change to that authority model is authorized by this parking item.

## Enforcement philosophy

The proposal follows a broader Riverview lesson:

> Critical repetitive rules should become mechanically enforced state transitions whenever practical rather than remaining instructions that must survive conversational memory.

Examples relevant to repository governance include:

- do not ask a worker to remember not to push to `main`; make the server reject the push;
- do not ask a worker to remember which branch/root it owns; assign and verify task identity;
- do not ask the Steward to remember which branches need cleanup; bind cleanup to lifecycle state;
- do not call a branch authoritative merely because a worker says it is complete; require controlled admission.

`AI_HINTS.md` remains important as the fast-recovery index and operating pointer. Mechanical enforcement complements it; it does not replace the documentation and recovery role.

## Relationship to previous approaches

### Free-form branches

Retain Git branches as implementation machinery but stop treating them as independently managed long-lived development worlds. A task branch should have one owner, one purpose, one integration target, and one bounded lifetime.

### Blue/green development copies

Do not recreate permanent blue/green/backup source universes merely to obtain development isolation. Most tasks should need only a worktree and task branch. Temporary acceptance runtimes may be created when a candidate genuinely requires live testing.

Backup should be backup, not a third mutable engineering tree.

### Frozen core / module-first development

The earlier module-first concept remains useful as an architectural pattern, but repository governance should not depend on workers voluntarily preserving the boundary. If future Riverview architecture defines protected core paths or module-only extension surfaces, the repository gate may eventually enforce those rules with protected-path or allowed-path policy.

This is a later enhancement, not part of the initial five-rule implementation.

## Candidate phased implementation if promoted

### Phase A — Product evaluation and appliance proof

Estimated effort: approximately one evening for a proof, assuming compatible hardware and no major infrastructure surprise.

- inspect the candidate laptop;
- install a lightweight Linux environment;
- install the selected repository service;
- create a disposable test repository;
- verify clone/fetch/push;
- verify protected `main` behavior;
- verify API/CLI automation sufficient for Riverview integration;
- prove backup/export and service restart.

No production migration should occur in this phase.

### Phase B — Five-rule prototype

Approximate cumulative effort: one working day.

- protect `main` from ordinary direct/force push;
- establish task branch/workspace naming and identity;
- establish controlled candidate submission;
- establish controlled merge/admission;
- establish branch/worktree retirement;
- deliberately attempt obvious bypass paths.

The success criterion is not only that the happy path works; the expected shortcuts must fail.

### Phase C — Riverview/Hermes integration and destructive testing

Approximate cumulative effort: two to three days to reach a trustworthy first operating state.

- create/resume task workspace from Riverview/Hermes;
- verify assigned root/branch/base SHA before critical operations;
- submit candidate through the repository service;
- test direct-main rejection;
- test force-push rejection;
- test wrong-branch submission;
- test stale-base/conflict handling;
- test interrupted/crashed integration;
- test abandoned task cleanup;
- test duplicate task identity handling;
- verify GitHub mirroring if retained;
- document backup/recovery.

This timeline is deliberately an estimate, not an implementation commitment.

## Future enhancements after the five-rule system proves itself

Do not include all of these in version one. Candidates include:

- mandatory tests/status checks;
- stale-target revalidation;
- path ownership / allowed-path enforcement;
- protected governance/core paths;
- work-order identity validation;
- acceptance evidence binding;
- live-browser/runtime acceptance gates;
- migration-chain collision detection;
- agent-specific credentials and least privilege;
- automatic workspace creation from accepted Riverview work orders;
- automatic task-state projection into PostgreSQL;
- merge queue / serialized admission;
- server-side audit events consumed by Riverview;
- disaster recovery and secondary mirror appliance;
- dashboard projection of candidate, validating, rejected, ready, integrated, and retired states.

## Candidate state model

A future controlled repository lifecycle might use states conceptually similar to:

`TASK_ACCEPTED -> WORKSPACE_CREATED -> ENGINEERING -> CANDIDATE -> VALIDATING -> READY_FOR_INTEGRATION -> INTEGRATED -> RETIRED`

Failure/side states may include:

`REJECTED`, `STALE`, `CONFLICT`, `BLOCKED`, `ABANDONED`, and `RECOVERY_REQUIRED`.

These are design candidates only. They must not become a second operational database. If Riverview ultimately tracks these states, authoritative operational state should follow the existing PostgreSQL/event architecture while the repository service remains authoritative for Git refs and admission mechanics.

## Acceptance questions for future elaboration

Before implementation, answer at minimum:

1. Which mature repository service best satisfies the five hard rules with the least custom Riverview code?
2. Should Forgejo or Gitea be the default first candidate, and what concrete capability differences matter to Riverview?
3. Does Gerrit provide enough additional enforcement value to justify its more opinionated workflow?
4. What remains authoritative in PostgreSQL versus the repository service?
5. What remains authoritative on GitHub, if anything, after local-first migration?
6. How are task IDs, branch names, worktree roots, base SHAs, and candidate SHAs bound together?
7. How does Riverview create a task workspace without allowing the worker to choose an arbitrary root or branch?
8. What credentials may Hermes/Codex hold, and what must those credentials be unable to do?
9. How does the system prove that direct and force pushes to `main` are impossible for ordinary engineering identities?
10. How is integration serialized when multiple valid candidates are ready simultaneously?
11. How is a candidate reconciled when `main` moved after the task began?
12. Which acceptance checks are mandatory in version one versus later enhancements?
13. How are branches/worktrees automatically retired after merge or explicit abandonment?
14. How are parked or intentionally retained candidates represented without becoming alternate authorities?
15. What is the appliance backup, restore, and hardware-failure recovery procedure?
16. Can GitHub remain a one-way or controlled mirror without allowing it to become an accidental second authority?
17. How are repository-governance events exposed to Riverview diagnostics and the Operator surface?
18. How is the service upgraded without risking repository authority?
19. What is the rollback path if the local repository governor fails operational acceptance?
20. What deliberate adversarial tests demonstrate that common agent shortcuts are actually rejected?

## Why it is parked now

The Steward has a near-term requirement to make the current Riverview environment functional enough for engineering work by Monday afternoon. Implementing and proving a new repository-governance appliance is expected to consume roughly one to three days depending on depth and would interrupt the active critical path.

The concept is worth preserving because safe parallel engineering is becoming increasingly important, but introducing a new source-control authority during the current push would create exactly the sort of scope expansion Riverview's Parking Lot exists to prevent.

## Promotion condition

Promote for elaboration when any of the following occurs:

- the current Monday-afternoon engineering-use objective has reached a stable accepted checkpoint;
- serial work on authoritative `main` materially blocks useful parallel engineering;
- branch/worktree discipline again causes a wrong-root, wrong-branch, stale-branch, or missed-integration incident;
- Riverview is ready to formalize local-first repository authority;
- the Steward explicitly directs repository-governor elaboration.

Promotion should begin with a bounded Forgejo/Gitea-versus-Gerrit evaluation and a disposable appliance proof. It should not begin by migrating the production repository.

## Explicit non-action

Parking this proposal does not authorize implementation.

Do not install or configure a repository appliance, change DNS/ports, move authoritative `main`, alter current remotes, change GitHub protection, create new production branches/worktrees, modify active Hermes/Codex lane roots, or interrupt current Riverview engineering to pursue this design.

The immediate purpose is preservation: capture the design in enough detail that it can be resumed later without reconstructing this conversation.