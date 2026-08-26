# Hermes / Riverview Integration — Tranche 2 Steward Checkpoint

Status: TECHNICALLY INCOMPLETE; BLOCKED AT PROVIDER STRUCTURED-OUTPUT BOUNDARY
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

Tranche 2 is not technically complete and is not institutionally accepted.
The system must stop at the current provider/Steward boundary until the
structured-output blocker is resolved through an authorized bounded continuation.
