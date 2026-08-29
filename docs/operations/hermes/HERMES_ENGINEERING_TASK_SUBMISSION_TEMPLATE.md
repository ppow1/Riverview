# Hermes Engineering Task Submission Template

Status: Canonical Riverview front door for bounded Hermes work.

Use this template to submit an engineering objective to Hermes. It is distinct
from Hermes objective-continuity enforcement, the Riverview terminal-attention
bridge, and CME progression. Complete the boundary before execution begins;
Hermes must not reconstruct authorization from conversational prose.

## 1. Identity

```yaml
objective_id: "<authoritative ID or null>"
work_order_id: "<authoritative ID or null>"
root_task_id: "<root identity or null>"
correlation_id: "<correlation identity or null>"
task_title: "<short title>"
task_type: "bounded engineering"
hermes_session_id: "<assigned at launch or null>"
```

`task_type` must be one of the existing bounded classes, such as:
`read-only investigation`, `forensic investigation`, `bounded engineering`,
`repair`, `validation`, `reconciliation`, `publication`, `acceptance`, or
another explicitly authorized Riverview class.

## 2. Objective

```text
Exact outcome Hermes is authorized to achieve:

<one concise objective statement>
```

Do not describe a vague aspiration. State the boundary that distinguishes
objective completion from an intermediate result.

## 3. Current known state

```text
Starting state and trusted evidence:

- authoritative repository/root:
- branch and starting SHA:
- runtime/provider/model state:
- current objective/work-order state:
- relevant evidence references:
- known failures or unknowns:
```

Historical reports and conversation memory are context, not current authority.

## 4. Authorized scope

```text
Hermes may:

- inspect:
- modify:
- test:
- reload/restart:
- reconcile:
- publish:
- use external or physical resources:

Explicit authority/lease/fence/capability:

<exact bounded authorization>
```

List only actions already authorized. A technical ability does not expand this
scope.

## 5. Prohibited scope

```text
Hermes must not:

- change:
- delete:
- publish:
- restart/reload:
- access:
- infer or fabricate:
- broaden into:
```

Preserve unrelated dirty work, active lanes, authority, credentials, and
protected data. Do not create a competing database or workflow state.

## 6. Dependencies and ownership

```text
Required prerequisites:

- <dependency, evidence, resource, or authority>

Active-lane ownership/conflicts:

- <owner and protected path/resource>

External boundaries:

- <credential, Steward decision, physical intervention, or service dependency>
```

Ordinary diagnosis, repair, retry, reload through an existing owner, and
provider recovery remain internal work unless a concrete external action is the
sole remaining dependency.

## 7. Acceptance criteria

```text
The objective is complete only when:

1. <objective-level criterion>
2. <independent validation/acceptance criterion>
3. <runtime or publication criterion, if required>
4. <durability/readback criterion, if required>
```

An intermediate implementation, commit, test pass, compilation pass, report,
or coherent synopsis is not `OBJECTIVE_COMPLETE` unless it satisfies the full
criteria above.

## 8. Required evidence

```yaml
evidence_requirements:
  - <durable evidence reference or artifact>
  - <test result and source provenance>
  - <runtime/readback evidence>
  - <acceptance/validation evidence>
```

Preserve exact identifiers, source SHA, provider/model/resource provenance,
request/correlation/run identity, and bounded failure evidence. Do not include
secrets or private chain-of-thought.

## 9. Objective-continuity contract

Bind this task to:

`docs/operations/hermes/HERMES_OBJECTIVE_CONTINUITY_CONTRACT.md`

At every attempted return boundary Hermes emits exactly one structured
`RIVERVIEW_TERMINAL_OUTCOME` marker with `disposition` set to one of:

- `CONTINUE`
- `OBJECTIVE_COMPLETE`
- `READY_FOR_STEWARD_REVIEW`
- `BLOCKED_REQUIRES_STEWARD`
- `STEWARD_DECISION_REQUIRED`
- `RETRYABLE_FAILURE`
- `TERMINAL_FAILURE`

`COMPLETED_NO_ATTENTION` may appear only as the documented compatibility alias.

If executable work remains within the authorized objective and no genuine
hard-stop, authority boundary, blocker, or Steward decision is required, the
disposition is `CONTINUE`.

A normal text response is not objective completion. A commit is not objective
completion. Passing tests are not objective completion unless they constitute
the entire accepted boundary. A useful progress report is not objective
completion.

## 10. Structured remaining work

For `CONTINUE`, the marker must include bounded structured `remaining_work`.
Each item contains:

```yaml
work_id: "<stable bounded identifier>"
description: "<next executable work within this objective>"
executable: true
status: pending | in_progress | blocked | complete
```

Remaining work must not exist only in narrative prose. Preserve the same
objective, work-order, root, correlation, checkpoint, and evidence lineage.

## 11. Hard-stop precedence

Existing Hermes hard boundaries remain authoritative and take precedence over
continuation:

- max iterations or shared iteration budget;
- timeout/deadline;
- context/compression exhaustion;
- provider or runtime failure;
- Codex/subprocess failure;
- user interrupt/cancellation;
- guardrail halt;
- persistence failure;
- interpreter shutdown;
- any other accepted safety/resource boundary.

Do not create an unbounded blind loop. Classify retryable and terminal failures
explicitly.

## 12. CME relationship

Hermes:

- executes the bounded objective;
- continues internally across `CONTINUE` turns;
- reports objective disposition and evidence;
- does not advance authoritative Riverview workflow by assertion alone.

CME:

- consumes the structured disposition;
- verifies root/correlation/work-order correspondence;
- queues bounded continuation for `CONTINUE`;
- validates evidence and acceptance;
- owns authoritative workflow progression under existing Riverview rules.

`OBJECTIVE_COMPLETE` is a claim requiring CME/acceptance validation. It is not
unilateral authority to mutate PostgreSQL, roadmap, or work-order state.

## 13. Steward boundaries

Return `READY_FOR_STEWARD_REVIEW` only when the next step is substantive review.
Return `BLOCKED_REQUIRES_STEWARD` only when a concrete Steward action is needed.
Return `STEWARD_DECISION_REQUIRED` only when an exact policy, authority, scope,
credential, physical, or preference decision is the sole remaining dependency.
Do not escalate predictable intermediate engineering work.

## 14. Completion report

The final report must include:

```text
Objective disposition:

Objective/result summary:

Objective/work-order/root/correlation/checkpoint identities:

Implementation and artifacts:

Commits and publication state:

Tests and source provenance:

Live acceptance/readback:

Evidence references:

Runtime/provider/resource state:

Deferred, blocked, or unknown work:

Acceptance criteria satisfied:

CME/authoritative progression status:
```

Separate technical completion, notification delivery, acknowledgement,
acceptance, and publication. If the objective is not complete, emit `CONTINUE`
or the correct explicit boundary rather than presenting an intermediate report
as completion.
