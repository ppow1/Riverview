<!--
File: docs/operations/GRACE_ENGINEERING_TASK_SUBMISSION_TEMPLATE.md
Version: 1.0.0
Date: 2026-08-20
Purpose: Canonical ChatGPT/Steward template for submitting single or parallel engineering tasks through Grace.
-->

# Grace Engineering Task Submission Template

Status: Canonical operating template.

Pat is the Steward and final authority. Grace is the production engineering orchestrator. This document teaches a fresh ChatGPT conversation how to turn a discussed engineering need into a governed Riverview engineering task, obtain one explicit Steward approval, submit it through Comms5, and follow the same lineage through Grace, Relay, Codex, authoritative reconciliation, recovery, and completion.

Use this document after the normal `AI_HINTS.md` required-reading chain. Do not reconstruct this workflow from conversation memory.

## 1. Core invariant

The normal production path is:

`conversation / engineering intent`
→ `stored specification`
→ `Steward-reviewable draft`
→ `one explicit Pat approval`
→ `seed promotion / durable authority`
→ `Grace engineering intent`
→ `work order`
→ `Relay`
→ `Codex/provider execution`
→ `authoritative repository evidence`
→ `reconciliation`
→ `objective completion`

One exact approved specification should require one Steward approval. Downstream Grace, Relay, execution, publication, and reconciliation consume the durable authority grant. Do not manufacture repeated approval checkpoints for unchanged scope.

## 2. Before submitting engineering work

A fresh conversation must first:

1. Read `AI_HINTS.md` completely and its required-reading chain.
2. Confirm repository identity is `ppow1/Riverview` and authoritative production work belongs on `main` unless Pat explicitly directs otherwise.
3. Determine the current verified `main` SHA. Use that as the specification `expected_base_sha`.
4. Inspect existing implementation, Cookbook guidance, tests, and current authoritative state before inventing new mechanisms.
5. Translate Pat's conversational request into one bounded engineering specification.
6. Preserve unrelated work.
7. Use Cookbook-first diagnostics for a known checkpoint/error before broad archaeology.

## 3. Build the specification

The specification should state the engineering result Pat actually wants, not merely the mechanics of calling Codex.

For a normal bounded write, populate the Comms5 formation contract with:

- `repository_identity`: `ppow1/Riverview`
- `repository_root`: `A:/Riverview/repo`
- `expected_base_sha`: current verified `main` SHA
- `bounded_instruction`: exact implementation task
- `allowed_paths`: exact paths the task may modify
- `acceptance_criteria`: observable conditions that prove completion
- `evidence_requirements`: evidence needed for authoritative reconciliation
- `capability_name`: `codex.engineering.v1`
- `action_type`: `codex.engineering.v1`
- `timeout_seconds`: bounded task-specific timeout, normally 300 unless evidence justifies another value
- `write_policy`: `bounded_write` for an authorized repository mutation; `read_only` only when the task is genuinely inspection-only

Do not let an approved `bounded_write` silently collapse to `read_only`.

### Recommended evidence requirements for a repository write

Use the evidence appropriate to the task. A production repository write commonly requires:

- approved base SHA
- actual changed paths
- authoritative artifact existence/content verification
- resulting commit SHA
- commit-tree verification
- `origin/main` publication verification when publication is required
- reconciliation result

The wording should make commit/publication requirements unambiguous. Prefer phrases such as `resulting commit SHA` and `origin/main publication verification` where those phases are required.

## 4. Store the specification first

Use `comms5_store_specification` before creating the Steward draft.

Never submit a production engineering seed with `specification_id` omitted. A specification-backed draft is required for the governed promotion path.

Record the returned:

- `specification_id`
- version
- content hash
- formation contract

If the Comms5 call times out, retry the same idempotent operation before starting a broad investigation. Do not create duplicate specifications merely because a response was delayed.

## 5. Create the Steward-reviewable draft

Use `comms5_submit_steward_seed` with the exact stored `specification_id`.

The draft text should be a concise human-readable statement of what approval will authorize. The draft call itself does not promote the work or execute engineering.

Record:

- `seed_id`
- `specification_id`
- `correlation_id`
- draft status

If the transport times out, retry using the same stable idempotency key. Query recent submission/status/lineage if needed before creating a replacement.

## 6. Show Pat the draft before requesting approval

Never ask Pat to approve an opaque seed UUID.

Present:

- what will be built or changed
- exact allowed path/scope
- `write_policy`
- approved base SHA
- key acceptance criteria
- required commit/publication/reconciliation behavior
- any material limitations or prohibited scope

Then wait for Pat's explicit approval.

Examples of valid approval language include `I approve`, `I approve both`, or another explicit statement clearly referring to the displayed exact draft(s).

Do not reinterpret a request to merely save or discuss an idea as approval unless Pat explicitly approves the displayed engineering draft.

## 7. Promote once

After explicit approval, use `comms5_confirm_and_promote_seed` for the exact approved seed.

Use one stable promotion idempotency key. Preserve the correlation ID.

Successful promotion should create the canonical objective and durable authority grant. The connector's authenticated Steward transport is the authority signal; client identity is provenance only.

Do not ask for another full approval merely because Grace is now forming, executing, committing, publishing, or reconciling the unchanged task.

## 8. Follow the same lineage through Grace

After promotion, monitor the same seed/objective/correlation rather than creating replacement work.

Useful Comms5 reads include:

- `comms5_seed_status`
- `comms5_seed_lineage`
- `comms5_objective_status`
- `comms5_cme_status`

A healthy engineering progression commonly includes River events such as:

`objective.created`
→ `steward.authority.granted`
→ `steward.seed.promoted`
→ `engineering.intent.bound`
→ `work.order.queued`
→ `execution.result.recorded`
→ `execution.reconciliation.recorded`
→ `work order completed`
→ `objective stage completed`
→ `objective completed`

Do not claim success merely because Codex says it succeeded. Provider completion is not execution completion; objective completion requires authoritative reconciliation.

## 9. Single-task template

Use this structure when translating a conversation into one Grace engineering task:

```text
TITLE:
<short engineering task name>

PURPOSE:
<what Pat wants accomplished and why>

REPOSITORY:
ppow1/Riverview

BASE:
<verified current main SHA>

WRITE POLICY:
bounded_write

BOUNDED INSTRUCTION:
<exact implementation instruction>

ALLOWED PATHS:
- <exact path 1>
- <exact path 2 if genuinely required>

ACCEPTANCE CRITERIA:
- <observable result 1>
- <observable result 2>
- no unrelated tracked changes

EVIDENCE REQUIREMENTS:
- approved base SHA
- actual changed paths
- artifact/content verification
- resulting commit SHA
- origin/main publication verification
- reconciliation result

PROHIBITED SCOPE:
- do not alter <unrelated component>
- do not widen paths or capability

STEWARD REVIEW SUMMARY:
<plain-language description shown to Pat before approval>
```

Then execute the sequence:

`store specification → submit seed → show exact draft → Pat approves → promote → follow lineage to completion`.

## 10. Parallel-task template

Parallelism is a first-class Riverview capability. Use parallel Grace work only when the tasks are genuinely independent and their writes cannot collide.

For two independent tasks A and B:

1. Create a separate stored specification for A.
2. Create a separate stored specification for B.
3. Give each task its own exact allowed paths.
4. Give each its own seed and correlation ID.
5. Show both human-readable drafts to Pat together.
6. Pat may explicitly approve both in one statement.
7. Promote each exact seed under that explicit approval.
8. Monitor each correlation independently.
9. Confirm both lineages can overlap without sharing mutable work state.
10. A failure in A must not silently block B.

### Parallel task A

```text
TASK A TITLE:
<name>

TASK A PURPOSE:
<purpose>

TASK A ALLOWED PATHS:
- <path unique to A>

TASK A ACCEPTANCE:
- <criteria>
```

### Parallel task B

```text
TASK B TITLE:
<name>

TASK B PURPOSE:
<purpose>

TASK B ALLOWED PATHS:
- <path unique to B>

TASK B ACCEPTANCE:
- <criteria>
```

Before promotion, verify A and B do not require sequential writes to the same file, migration chain, branch state, or mutable resource. If they collide, serialize them instead of calling them parallel.

The 2026-08-20 evidence for proven parallel Grace orchestration is preserved at `docs/operations/roadmap/evidence/GRACE_PARALLEL_ENGINEERING_MILESTONE_2026-08-20.md`.

## 11. Recovery without restarting the approval cycle

Preserve the original specification, seed, objective, authority, failed work order, and execution history whenever possible.

### Provider timeout or recoverable execution failure

Do not rewrite a failed work order into success. Use the canonical immutable successor/recovery mechanism when the failure class is eligible.

### Stale base

The reason the original attempt failed and the reason a successor now needs base revalidation are independent facts.

If `main` advanced after approval:

1. Compare the approved base to current `main`.
2. Run the canonical drift assessment.
3. Preserve unchanged instruction, paths, capability, action, policy, criteria, and evidence requirements.
4. Use same-lineage revalidation/successor recovery when eligible.
5. Material drift fails closed unless the governed recovery rule permits a bounded infrastructure-repair revalidation.
6. Do not demand a new full specification approval when unchanged authorized scope can be safely carried forward by the recovery architecture.

The historical failed attempt remains immutable.

## 12. Cookbook-first error handling

When Grace returns a checkpoint code, search `docs/operations/troubleshooting/checkpoints/` first.

Examples demonstrated during production recovery include:

- `RIV-EXE-0003` — bounded provider timeout
- `RIV-EXE-0007` — changed path escaped the envelope
- `RIV-EXE-0008` — approved base mismatch
- `RIV-EXE-0010` — bounded-write/authoritative completion discrepancy; consult the authoritative Codex-completion checkpoint before broad investigation
- `RIV-REC-*` — reconciliation failures; preserve the real checkpoint rather than remapping it to a generic execution error

Follow the Cookbook diagnostic sequence, find the first divergence, repair the demonstrated defect, add regression evidence, publish the repair, and resume the same lineage when safe.

## 13. Comms5 transport flakiness

Observed Comms5 HTTPS/MCP calls may occasionally time out while a retry succeeds.

Until the transport reliability investigation is completed:

- distinguish a network timeout from a Riverview rejection
- retry the same idempotent read/write once or a small bounded number of times before launching a broad investigation
- reuse the same idempotency key for the same transition
- do not create replacement seeds/specifications solely because the response timed out
- if a non-retry-safe server error is returned, stop retrying that mutation and inspect the authoritative state
- never report a timeout as proof that Grace failed

The transport reliability problem is separate from Grace's production engineering capability.

## 14. Completion standard

A normal bounded engineering task is complete only when authoritative evidence proves the required terminal state.

For a repository write requiring publication, verify:

- required artifact/content exists
- actual changed paths stay inside scope
- commit exists
- commit contains the required artifact
- `origin/main` contains the verified commit when publication was required
- reconciliation is accepted
- work order is succeeded
- objective/stage is completed
- no additional Steward attention remains unless explicitly required

Use the River/Operator display for observability, but do not substitute browser state for PostgreSQL/GitHub authority.

## 15. Fresh-chat instruction Pat can use

Pat can point a new ChatGPT conversation at this file with a short instruction such as:

> Read `AI_HINTS.md` and `docs/operations/GRACE_ENGINEERING_TASK_SUBMISSION_TEMPLATE.md`. We are going to discuss an engineering change. When the task is sufficiently defined, turn it into the proper Grace/Comms5 engineering specification, show me the human-readable draft, get my one explicit approval, submit it through Grace, and follow the same lineage through authoritative completion. Use the parallel flow if I give you multiple independent tasks.

A fresh conversation following that instruction should not require Pat to reconstruct the submission mechanics from memory.
