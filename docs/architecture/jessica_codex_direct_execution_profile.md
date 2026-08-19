# Jessica Localization — Direct Codex Execution Profile

Status: Planning architecture — not authorization for execution  
Date: 2026-08-19  
Applies to: Jessica / Chief Character Architect Local Residency campaign  
Roadmap: `docs/architecture/riverview_resident_localization_master_roadmap.md`  
Base campaign spec: `docs/architecture/jessica_localization_campaign_execution_spec.md`  
Work packages: `docs/work_packages/resident_localization_tranche_0_A_work_packages.md`

## 1. Purpose

This profile defines how the Jessica localization campaign may be executed directly through Codex CLI while Grace's autonomous engineering workflow is still being repaired.

This is not an abandonment of Grace. Grace remains the intended autonomous campaign manager for substantial future Riverview engineering work. This profile exists because Jessica's localization should not be blocked on unrelated Grace permission / workload issues when Codex is already capable of performing the required high-reasoning repository work directly.

## 2. Precedence

For a work package explicitly dispatched under the `direct_codex` execution profile, this document overrides conflicting Grace-specific execution clauses in:

- `docs/architecture/jessica_localization_campaign_execution_spec.md`;
- `docs/architecture/jessica_localization_campaign_manifest.yaml`;
- `docs/work_packages/resident_localization_tranche_0_A_work_packages.md`.

It does not alter the resident-localization architectural invariants, Steward authority boundaries, provenance requirements, cookbook requirements, or package acceptance criteria.

## 3. Grace prerequisite removed for direct Codex execution

The requirement `grace_autonomous_engineering_accepted` applies to **Grace-managed autonomous execution**, not to direct Codex execution.

Under this profile, Tranche 0 and Tranche A may be dispatched to Codex CLI before Grace autonomy is repaired, provided the Steward explicitly authorizes the direct Codex campaign / tranche.

The campaign remains tranche- and dependency-driven:

`Tranche 0 -> Tranche 0 Gate -> Tranche A discovery -> JCA-005 synthesis -> Archaeology Gate`

Do not stream later tranches merely because earlier roadmap entries exist. Progressive elaboration remains required.

## 4. Codex is the escalated reasoning lane for this profile

When Codex CLI is the execution provider, remove requirements that Codex reach out to another provider for "higher reasoning" merely to satisfy the Grace reasoning-escalation policy.

Codex is already the high-reasoning repository-grounded execution / analysis lane for this profile.

Therefore, for `direct_codex` execution:

- no ChatGPT escalation is required for ordinary ambiguity, architecture analysis, source classification, synthesis, or self-checking;
- no separate external reasoning request is required solely because the base Grace specification marked a point as "mandatory reasoning escalation";
- Codex should inspect the authoritative repository evidence, state uncertainty explicitly, challenge assumptions when evidence warrants it, and stop at genuine Steward authority boundaries;
- if Codex lacks required evidence or encounters a canonical conflict that cannot be resolved from authoritative sources, it must stop and report the issue rather than invent an answer.

## 5. Double-checking and review under Codex

Removing external reasoning escalation does **not** remove validation or critical review.

Where the base campaign requested an independent / consequential double-check, the Codex profile uses one of these mechanisms as appropriate:

1. **separate Codex review pass / fresh Codex context** over the same bounded evidence;
2. **repository-grounded validation** against source artifacts, tests, manifests, schemas, or acceptance criteria;
3. **explicit adversarial self-review section** in the completion evidence when a separate session would add little value;
4. **Steward review** when the matter is identity-, authority-, scope-, or canon-sensitive.

A second Codex pass is preferred over asking the same execution context to simply affirm its own conclusion when meaningful independence is useful.

## 6. Work-package reasoning-policy override

For direct Codex execution, interpret every `Reasoning policy` section in RC-000 through RC-002 and JCA-001 through JCA-005 as follows:

> Codex performs the required reasoning directly from repository / authoritative evidence. It may perform a separate Codex review pass when useful. It must preserve uncertainty and source provenance. It must stop for the Steward when a canonical identity fact, institutional authority boundary, material scope change, or unresolved high-impact contradiction requires human judgment. No external higher-reasoning escalation is required merely because the package is running in Codex.

Specific override for WP-JCA-004:

The phrase **"Mandatory independent reasoning review before final acceptance"** becomes:

> **Mandatory critical review before final acceptance.** For direct Codex execution, perform a distinct review pass, preferably in a fresh Codex context, over consequential / representative disposition decisions. No external reasoning provider is required.

Specific override for WP-JCA-005:

JCA-005 must consume the JCA-004 critical-review evidence. Additional external reasoning is not required unless the Steward explicitly requests it.

## 7. Orchestration model while Grace is bypassed

Direct Codex execution temporarily shifts campaign orchestration away from Grace.

Preferred mechanism:

- submit **Tranche 0 as one bounded Codex campaign** containing RC-000, RC-001, and RC-002 with explicit parallel-safe guidance and a final reconciliation gate;
- review / accept Tranche 0 evidence;
- submit **Tranche A as one bounded Codex campaign** where JCA-001, JCA-002, and JCA-003 may be investigated in parallel, JCA-004 consumes their evidence for final classification, and JCA-005 performs final synthesis;
- stop at the Archaeology Gate before writing or dispatching Tranche B implementation work.

The atomic evidence unit remains the individual work package even when several packages are submitted in one Codex campaign.

## 8. Human workload objective

The direct Codex path should avoid recreating the Estate-era problem where the Steward manually shepherds every small task.

Where Codex CLI supports a bounded multi-step session / campaign, prefer a tranche-level handoff with explicit dependencies and stop conditions over eight separate copy/paste submissions.

The desired temporary flow is:

`Steward / orchestration chat -> Codex Tranche 0 -> evidence / gate -> Codex Tranche A -> evidence / Archaeology Gate`

not:

`Steward -> WP1 -> check -> WP2 -> check -> WP3 -> ...`

## 9. Authority boundaries retained

Codex may not:

- redefine Jessica's canonical identity;
- invent missing history;
- grant institutional authority;
- silently rewrite Steward-established facts;
- expand the campaign into unrelated resident migrations;
- promote uncertain Estate evidence to canon without support;
- import Estate governance ceremony by default;
- bypass the Archaeology Gate;
- authorize later tranche execution merely because it has drafted later work.

## 10. Cookbook obligations retained

Any code, schema, runtime, adapter, retrieval, or operational infrastructure change still requires the corresponding first-pass Riverview cookbook update before acceptance.

Tranche 0 and Tranche A are primarily analysis / archaeology work, so cookbook changes are required only where the work discovers or changes operational understanding that future builders need to avoid rediscovery.

## 11. Campaign handoff artifact

Before direct execution begins, create one Codex-ready handoff that:

- names the exact repository: `ppow1/Riverview`;
- references the Estate source repository: `ppow1/theestate`;
- references the roadmap, base campaign spec, this direct-Codex profile, and the tranche work-package file;
- explicitly states that this direct-Codex profile overrides Grace-specific reasoning-escalation and Grace-autonomy prerequisites;
- defines exact tranche stop points;
- requires package-by-package evidence and commits;
- preserves progressive elaboration;
- stops at the Archaeology Gate for review before Tranche B.

## 12. Current decision

The architecture now supports two execution profiles:

- **Grace-managed autonomous profile** — event-driven, notification-backed, with Grace able to request external escalated reasoning and double-checks as needed;
- **Direct Codex profile** — Codex performs the high-reasoning work directly, uses Codex-native critical review / fresh-context review where useful, and does not depend on Grace autonomy being repaired first.

Both profiles consume the same resident-localization roadmap and preserve the same institutional / provenance / authority boundaries.
