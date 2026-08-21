<!-- Version: 1.0.0 | Date: 2026-08-21 | Status: READY -->
# RB-0001 — Operator Model Override

## Ready Bench identity

- ID: RB-0001
- Category: Operator / Resident Runtime / Diagnostics
- Priority: High-value diagnostic and qualification capability
- Originator: Steward
- Date committed: 2026-08-21
- Status: READY
- Current blocking condition: Deliberately not active while C485 Jessica interactive-residency repair remains the current execution path.

## Steward intent

Riverview will provide an explicit Steward-authorized way to temporarily run an existing resident through a different available model implementation without changing that resident's identity or default accepted implementation binding.

The immediate use case is human comparison and diagnostics in the Riverview Operator: the Steward can remain in the same Jessica conversation, temporarily select another model, observe the behavioral difference, and then return to Jessica's normal implementation.

This is committed future work, not an open-ended research idea.

## Core architectural rule

The resolution order is:

`resident identity -> accepted/default implementation binding -> optional authorized conversation override -> provider/runtime/model`

The override changes execution only.

It MUST NOT mutate:

- resident identity;
- office or role;
- accepted canon;
- resident continuity;
- default implementation binding;
- provider qualification evidence;
- authority state.

A conversation can therefore say "use model X for subsequent turns" without making model X part of the resident's identity.

## User interaction

The preferred Operator interaction is an explicit command rather than natural-language keyword matching.

Initial command surface:

- `/model <model-id>` — apply a temporary model override to the current resident conversation.
- `/model default` — clear the override and return to the resident's accepted/default implementation binding.
- `/model status` — show the current effective execution binding and whether it is default or overridden.

Natural phrases such as "switch brains" MUST NOT silently change runtime state.

The UI should visibly indicate an active override, for example:

`Jessica — temporary model override: <model-id>`

and when cleared:

`Jessica — active binding: qwen3:32b`

Exact wording is implementation detail; visible state is required.

## Initial scope

Version 1 is conversation-scoped only.

A conversation-level override remains active for subsequent turns in that one Operator conversation until:

- `/model default` is issued;
- the conversation is archived/closed if the existing lifecycle contract treats that as terminal; or
- the override is explicitly invalidated because the target implementation becomes unavailable or unauthorized.

Version 1 does NOT implement resident-wide persistent model reassignment.

Turn-scoped override may be added later if useful, but is not required for first acceptance.

## Authorization

The override is a Steward/operator diagnostic control.

The first implementation must use existing Operator authentication and authorization boundaries. It must not expose an unauthenticated endpoint that lets arbitrary callers choose resident implementations.

If Riverview later introduces finer-grained operator roles, the override permission may be separated explicitly.

## Candidate model eligibility

The override must not accept arbitrary text and blindly dispatch it.

The target model must be discoverable through an approved local implementation/provider inventory or an explicitly permitted test implementation catalog.

At minimum, validation must establish:

- target model exists;
- target provider/runtime is available;
- model can be reached through an existing approved provider adapter;
- requested override does not silently invoke a cloud/external provider unless separately authorized;
- resource failure is reported honestly rather than falling back to another model.

A model need not be Jessica-qualified in order to be used for an explicitly marked diagnostic comparison, but the Operator must distinguish `qualified/default` from `temporary test override`.

## Failure behavior

The override must fail closed.

Examples:

- unknown model -> reject override;
- provider unavailable -> reject or report unavailable;
- model load fails -> retain/restore prior effective binding and report failure;
- GPU/resource exhaustion -> report exact failure; no silent fallback;
- resident has no default binding -> override may be permitted only if existing resident runtime contracts allow a test implementation, otherwise reject;
- stale conversation override references unavailable implementation -> surface stale state and require explicit clear/change.

No failure may mutate resident identity or accepted binding.

## Persistence semantics

Conversation-level override state must persist with the Operator conversation if the conversation itself is durable, so a restart does not silently change the model mid-conversation.

Persistence must record the override as conversation/runtime metadata, not resident canon.

At minimum preserve:

- conversation ID;
- resident ID;
- override model/implementation reference;
- provider/runtime reference as appropriate;
- who/what authorized the override;
- activation timestamp;
- cleared/invalidated timestamp where applicable;
- reason/source (`operator_model_override` or equivalent).

## Restart semantics

After Operator restart:

- the same conversation still resolves to the same resident;
- an active conversation override remains visible and effective if still valid;
- `/model default` returns execution to the accepted resident binding;
- a different conversation for the same resident remains on its own default/override state and is unaffected.

## Resource-awareness boundary

RB-0001 is not the Autonomic Resident Layer and does not implement general cognitive-resource scheduling.

The override may expose or preflight basic feasibility information such as model availability and expected local device constraints, but it must not become a GPU scheduler, fairness engine, or multi-resident arbitration system.

PL-0001 remains separate.

## Runtime boundary

RB-0001 must use the existing provider-neutral resident/runtime architecture and current Operator persistent-service ownership.

It must not require promotion of PL-0002 Alternative Local AI Inference Runtime Paths.

If a requested model requires an unsupported inference runtime, the command should report that limitation rather than installing a new runtime automatically.

## Diagnostics / Cookbook obligations

Every executable seam created or changed must prepare its first-pass diagnostics/Cookbook treatment under the existing Riverview engineering rules.

Expected diagnostic seams include:

- command parsing;
- authorization;
- model/implementation lookup;
- conversation override persistence;
- effective binding resolution;
- provider availability;
- model load failure;
- stale override;
- restart restoration;
- clear/default restoration;
- UI state projection.

Reuse current RIV-UI-*, RIV-RES-*, and RIV-REASON-* checkpoints when they own the seam; create a new checkpoint only for a genuinely distinct failure family.

## Execution roadmap

### WP-OMO-001 — Contract and state model

Define the resident-general `OperatorModelOverride` contract and conversation-scoped lifecycle. Reuse existing conversation persistence and resident implementation contracts. Specify authorization, activation, clear, stale, and invalid states.

Acceptance:

- model override cannot mutate resident identity/default binding;
- conversation-scoped state is unambiguous;
- default effective-binding resolution remains unchanged when no override exists.

### WP-OMO-002 — Operator command/API surface

Implement explicit `/model` command handling and the smallest API/service contract needed by the existing Operator UI.

Acceptance:

- `/model <id>` activates only a valid authorized target;
- `/model default` clears it;
- `/model status` reports effective state;
- ordinary natural-language conversation cannot accidentally activate an override.

### WP-OMO-003 — Effective binding resolution and provider dispatch

Integrate the temporary override into the resident execution path after resident identity/default binding resolution and before provider invocation.

Acceptance:

- resident ID remains unchanged;
- target provider/model is explicit in response metadata;
- no silent generic/default fallback on override failure;
- clearing override immediately restores default binding.

### WP-OMO-004 — Persistence, restart, and UI visibility

Persist conversation override metadata using the existing Operator projection/state mechanism and display the active override visibly.

Acceptance:

- override survives Operator restart for that conversation;
- same resident in a different conversation remains unaffected;
- state is visibly marked as temporary;
- clearing survives restart as cleared/default.

### WP-OMO-005 — Live comparison acceptance and diagnostics

Run a bounded real Operator comparison using Jessica or another accepted resident with at least two locally available model implementations.

Acceptance:

- default resident conversation works;
- override activates;
- real response uses requested model;
- resident identity remains exact;
- conversation continuity remains intact;
- `/model default` restores default qwen3:32b (for Jessica, if still current at execution time);
- Operator restart preserves correct override state;
- failure test for unavailable model is fail-closed;
- Cookbook/diagnostic evidence is complete.

## Dependencies

Required before activation:

- persistent Operator service ownership must remain healthy (C484 or successor);
- resident implementation-binding and provider-neutral runtime contracts must remain authoritative;
- at least one alternate local model implementation must be available for live comparison;
- current active resident work should not be interrupted merely to implement this feature.

## Known blockers / resource requirements

No known hardware purchase is required.

The current blocking condition is execution priority/capacity: Jessica's C485 interactive-residency repair is the active path and should not be interrupted by RB-0001 unless the Steward explicitly pulls RB-0001 to active work.

The P100 is not required for RB-0001 first acceptance.

## Prohibited scope

RB-0001 does not authorize:

- resident-wide permanent model rebinding;
- automatic model selection;
- model benchmarking campaigns;
- new model downloads merely to populate the selector;
- provider/runtime architecture replacement;
- PL-0002 activation;
- PL-0001 Autonomic Resident Layer implementation;
- GPU scheduling/resource arbitration;
- changes to resident canon;
- model name becoming resident identity;
- unauthenticated model switching;
- silent fallback after override failure.

## Final acceptance criteria

RB-0001 is complete when the Steward can use the real Riverview Operator to:

1. talk to an accepted resident on its default implementation;
2. issue an explicit model override command for the current conversation;
3. visibly see that the override is active;
4. receive a real response from the selected alternate model;
5. continue the same resident/conversation without identity reset;
6. restart Operator and retain valid override state;
7. clear the override explicitly;
8. receive subsequent responses from the resident's default accepted binding;
9. prove that another conversation/resident was unaffected;
10. see an unavailable/invalid override fail closed with useful diagnostics.

## Promotion / activation rule

This item is Steward-committed and fully elaborated for the Ready Bench.

It remains inactive until the Steward or an authorized future Ready-Bench workflow pulls `RB-0001` to Active Work under normal Riverview engineering authority and dependency checks.
