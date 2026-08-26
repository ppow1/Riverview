# Hermes / Riverview Integration — Tranche 2 Steward Checkpoint

Status: CLOSED; TECHNICALLY AND INSTITUTIONALLY ACCEPTED
Date: 2026-08-26
Authority: Steward-controlled Riverview lifecycle and acceptance
Authoritative checkout: `A:\theestate\Riverview`
Branch: `main`

## Current tranche and scope

Tranche 2 integrates Hermes as a replaceable, bounded execution substrate behind
Riverview Campaign Runner. Scope includes real PostgreSQL lifecycle execution,
writer/independent-validator/repair/revalidator correspondence, dynamic resource
selection, bounded substantial execution, operator projection, Steward attention,
audio delivery, and recovery boundaries. Hermes completion is technical evidence,
not institutional acceptance.

## Acceptance boundary

The required technical lifecycle is:

`writer -> independent validator FAIL -> Campaign Runner repair writer -> independent revalidator PASS`

The final technical PASS remains separate from Steward/institutional acceptance.
No institutional acceptance has been recorded.

## Material implementation changes

- Added dynamic resource registry and Codex capacity/fuel projection.
- Preserved exact candidate, validation basis, evidence, role, seat, attempt,
  lease, fencing, and repair correspondence across lifecycle handoffs.
- Added substantial `campaign.hermes.engineering` execution policy:
  expected duration 1,200 seconds, hard timeout 1,800 seconds, bounded lease
  grace, and per-run Hermes guidance of `--max-turns 300` without changing the
  global 150-turn default.
- Prevented generic relay workers from claiming the internal Hermes lifecycle
  action.
- Added operator-facing Hermes/Campaign Runner projection and bootstrap/recovery
  documentation.
- Added bounded Steward notification classes and migration 0048.
- Added Riverview-to-Estate audio adapter using the existing
  `estate.core.steward_annunciator.WindowsPresenter`.
- Added annunciation capability preflight for Windows `winsound`, PowerShell,
  and System.Speech. No Estate runtime process is falsely required.
- Added atomic lifecycle-triggered Steward attention creation and post-commit
  audio delivery. Notification delivery and acknowledgement remain separate.
- Repaired Hermes API-server request override propagation and Codex Responses
  `response_format`/`text.format` preflight handling.
- Updated PL-0007 and PL-0008 with the future Unified Riverview Resource & Work
  Command Center requirement. No UI work was started.

## Durable live proof evidence

Latest real proof:

- objective: `dfd14e27-b2a8-4b6a-86b4-8b1a2c303700`
- stage: `92ac3724-331e-4783-903d-ac5f84e351c8`
- basis: `7be07ffd-a7db-4193-a9e2-683ed33c0f02`
- writer work order: `47e0607f-3fb0-4adf-82c3-9ef69c59933c`
- writer attempt: `46a50fc6-bd56-41f9-97d5-05ed0f69326c`
- writer: succeeded
- validator work order: `b89c8541-d480-4e0b-8ea8-c1030b0da57b`
- validator attempt: `23aa582a-c4d7-4e41-a981-cf1aac438873`
- validator: failed closed at `RIV-CAM-HERMES-0008` because provider output
  was not structured JSON
- repair writer: not reached in the latest proof
- revalidator: not reached in the latest proof
- latest stage state: `failed / ready`

Earlier genuine lifecycle defects remain preserved as evidence, including
candidate/tree mismatch, incomplete validator output, internal-action claim
boundary failure, and preflight structured-output rejection.

## Steward attention evidence

Lifecycle-triggered blocked notifications were created automatically and
persisted exactly once. The current restart-boundary notification is:

- notification: `bc4cab9d-4ba0-487e-ae2b-8de3fb9b78f5`
- type: `blocked_requires_steward`
- checkpoint: `RIV-HERMES-TRANCHE2-GATEWAY-RESTART-REQUIRED`
- state: `delivered`
- acknowledged: `NULL`

The Steward confirmed hearing the lifecycle-triggered blocked annunciation.
The earlier READY proof was also heard through the same existing presenter path.
Delivered is not acknowledged; acknowledged is not accepted.

## Tests and verification

- Riverview changed-area focused suite: `27 passed`.
- Hermes structured-output/gateway focused suite: `2 passed`.
- Notification/audio gate: `4 passed`.
- Python compilation passed for changed Hermes and Riverview modules.
- Broader direct lifecycle tests remain affected by legitimate shared PostgreSQL
  relay residue/active worker state; no history, lease, or unrelated process was
  removed or altered to manufacture green results.

## Current blocker

The restarted Hermes gateway is healthy on `127.0.0.1:8642`, and the final
Codex Responses preflight correction is loaded. The configured `openai-codex`
provider/model still returns non-JSON validator prose for the strict validator
request. The latest proof therefore cannot truthfully enter repair/revalidation
or claim PASS. No provider result has been fabricated.

Codex C1/C2/C3 remain scheduling/resource identities only. Hermes uses its own
credential store; no proven mapping exists from Campaign Runner seat C3 to an
independently authenticated C3 credential. Credentials and account details are
not recorded here.

## Steward decisions and authorizations

- Steward authorized the default Hermes gateway restart on 2026-08-26.
- Steward confirmed lifecycle-triggered blocked audio was heard.
- Steward has not granted institutional acceptance of Tranche 2.
- Tranche 3 has not started.

## Publication and continuity

This file is the durable human-readable engineering checkpoint intended for
publication through the normal Riverview `main` GitHub path. It contains no
secrets, credentials, raw internal reasoning, transient cache content, or private
resident information.

## Next work

Recommended next bounded work is to resolve the configured provider/model's
structured-output compliance at the verified Codex Responses boundary, then rerun
one fresh PostgreSQL proof through FAIL, repair, revalidation, and PASS. Preserve
all existing evidence and do not replay completed successful stages.

No authoritative Riverview integration plan currently defines a formal Tranche 3
or Tranche 4 name/scope. A future next tranche must be explicitly defined and
Steward-authorized after Tranche 2 technical completion and acceptance review;
this checkpoint does not create one.

## Acceptance state

Tranche 2 is technically complete and institutionally accepted. It is closed.
The next transition belongs to a separately authorized future tranche.

## Final completion addendum — 2026-08-26

The authorized continuation resolved the remaining structured-output and
correspondence defects and completed one fresh real PostgreSQL lifecycle proof.

- objective: `c083f54f-1c42-4124-bd3a-2285d4fc37f1`
- stage: `3b6cd40d-006a-4485-8bc5-f3df41977cc6`
- basis: `8eedf5c1-9df7-46c1-b0a3-c70c2e0c6199`
- writer order/attempt: `c74e61de-8884-4c02-b207-a4d3ea04ba3d` /
  `c3e686dc-d3b2-4554-a794-63a4c54f4b19`
- validator order/attempt: `a6361bd9-1875-4f25-bce1-fc6e569dfbdf` /
  `3fce59cb-23ba-44bb-976e-ee2ad22f2fd0`
- validator result: `970cabea-08f5-4dd2-9157-edbe9454453c`, `FAIL`
- repair order/attempt: `a29fde2d-4225-420d-b86f-bbce0a3dbdce` /
  `a877b02f-0130-429c-854d-1a7e7d386863`
- revalidator order/attempt: `7819f011-0e75-4d43-bbfd-ae1ce16747d1` /
  `50503efd-bc86-4b2b-a126-59f1f90dc1a7`
- revalidator result: `5f201dc6-ab6b-4e98-a4e1-fefca3094d40`, `PASS`
- final stage/objective state: `accepted / completed` technically
- validator and revalidator used the same basis hash:
  `7094adc072456bffbe6d4f72f8e54d7331cd61233c2034693c9d741b7f7a5720`
- writer/validator candidate: `94594552fd84fbdb4162ce2da54c378c0b3a2a17`
- repaired/revalidated candidate: `3234f5b1684d0e869157cbbb238ad689d71eccbc`
- selected resource: dynamic C3 scheduling identity, with Hermes resource
  metadata `resource:hermes-local`; independent credential correspondence to
  C3 remains unproven and is not claimed.

The automatic READY notification was created by the revalidator PASS transition and subsequently acknowledged by the
Steward:

- notification: `4cd5506f-a833-437c-9aa1-5c806917b3fa`
- idempotency key: `runner.steward_attention:ready:5f201dc6-ab6b-4e98-a4e1-fefca3094d40`
- type: `ready_for_steward_review`
- message: `Riverview Hermes is ready for your review.`
- state: `delivered`
- duplicate count: `1`
- `acknowledged_at`: `NULL`
- delivery path: existing Estate `WindowsPresenter` (ding then synchronous
  Windows speech on the default endpoint)

The technical Tranche 2 candidate was ready for Steward review. The Steward
has now explicitly accepted it institutionally. Technical completion,
notification delivery, acknowledgement, and institutional acceptance remain
distinct and are all recorded separately.

The authoritative Riverview roadmap and integration documents do not define a
formal Tranche 3 or Tranche 4 scope. Recommended next work is therefore not
automatically started: the Steward should define and authorize the next bounded
tranche after reviewing this candidate. No Tranche 3 or Tranche 4 is inferred or
created by this report.

## Closure addendum — Steward acceptance

The Steward explicitly accepted Tranche 2 institutionally after reviewing the
successful lifecycle proof. Riverview recorded the decision through its
authoritative objective/event path rather than through documentation alone:

- objective state: `completed`, `acceptance_state=accepted`
- objective closure state: `closed`
- `attention_required`: `false`
- event type: `steward.institutional_acceptance`
- idempotency key:
  `steward.institutional_acceptance:tranche2:5f201dc6-ab6b-4e98-a4e1-fefca3094d40`
- accepted by: `Steward`
- basis: final successful proof, validation result
  `5f201dc6-ab6b-4e98-a4e1-fefca3094d40`
- ready notification acknowledgement: `acknowledged`
- acknowledgement remains distinct from audio delivery and technical PASS.

The Hermes source repository is separate from Riverview and remains on its own
main branch with unpublished working-tree changes in the response-format repair
chain and associated tests. Those changes were loaded and exercised by the
gateway used for this proof, but are not silently represented as part of the
Riverview commit. Their repository/authority boundary remains explicit for a
future separately governed publication decision.

Tranche 2 is closed. No Tranche 3 or Tranche 4 is defined, authorized, or
started.
