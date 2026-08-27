<!--
File: docs/operations/roadmap/evidence/GRACE_JESSICA_LIVE_ACCEPTANCE_BASELINE_2026-08-26.md
Version: 1.0.0
Date: 2026-08-26
Purpose: Durable baseline and acceptance-boundary report for Grace cognition and Jessica character development.
-->

# Grace / Jessica live acceptance baseline

Status: BLOCKED_AT_STEWARD_BOUNDARY — NOT READY FOR LIVE ACCEPTANCE
Authority: Steward-controlled Riverview lifecycle and acceptance
Authoritative checkout: `A:\theestate\Riverview`
Branch: `main`
Verified authoritative HEAD and `origin/main`: `ec9075bfec7655fe67e7c4455bfd9c644b2d2d52`

## Scope

This report continues the Grace conversational-reasoning and Jessica
character-development initiative. It preserves the bounded conversation-history
and workflow-contract implementation increment but does not treat those changes,
unit tests, or compilation as behavioral acceptance.

3060 small-brain/big-brain routing, cognition optimization, shared resident
cognition optimization, and escalation optimization are explicitly excluded.

## Actual live path observed

The currently running Operator is a separate installed checkout:

`A:\Riverview\repo`

Its process topology is owned by the installed runtime supervisor and serves
`127.0.0.1:18082`. Operator `/health` reported source SHA
`c29d6256e05bd0c98188a5113346cb3895f8259a`, not the authoritative checkout SHA
above. The alternate checkout is dirty and was not modified.

Observed request path:

`Riverview Operator -> /api/chat -> ResidentConversationGateway.chat -> OllamaReasoningAdapter.complete -> Ollama /api/generate -> qwen3-coder:30b-qwencode-20k -> typed ReasoningResponse -> Operator conversation projection`

Observed provider/model evidence:

- Provider: `ollama:qwen3-coder:30b-qwencode-20k`
- Ollama endpoint: loopback `127.0.0.1:11434`
- Operator response retained request/correlation IDs and operational classification.
- The model returned coherent Operations Director prose for a live Grace prompt.
- Hardware probe: NVIDIA GeForce RTX 4090, 24,564 MiB total; 22,547 MiB used at observation time.

## Cognitive-path assessment

The observed path is genuine local-model generation through a provider-neutral
reasoning envelope, but it is not yet the intended governed Grace cognition path.
It does not invoke `HomeCognitionService`, `HOME_COGNITION`, the resident
reasoning packet assembler, F3 session/request readback, P1 escalation policy,
P2 capability binding, or F2 cognition provenance/latency observation.

Therefore the live response is evidence of a working bounded resident chatbot
path, not evidence that Grace's actual governed cognition has been restored.

## Authoritative-state blocker

PostgreSQL contains the accepted `grace_identities` authority record:

- `grace_id=grace`
- display name `Grace`
- role `operational_coordinator`
- authority version `0.1.0`
- enabled `true`

The resident continuity tables contain Jessica but no Grace occupant/office /
implementation/current-assignment projection suitable for constructing the
non-stale `AuthoritativeGraceState` required by E1. The cognition-specific
service also has no production Operator adapter or live resource-catalog seam
in this checkout.

Creating that canonical Grace cognition state and reconciling the installed
runtime owner to the authoritative checkout are material authority/runtime
changes. They must not be inferred from the existing conversation path or
invented from model output.

## Jessica track

The reusable `CharacterDesignerWorkflow` remains valid and preserves:

- accepted versioned character state;
- proposal/review/publish separation;
- source evidence and rationale;
- prior-version lineage;
- no self-authorized canon mutation.

The live standalone Operator now provides `/jessica` and authenticated
`/api/jessica/character-development` actions for inspect, discuss, propose,
independent review, Steward review, and publish. A real Jessica discussion and
proposal were exercised through Ollama; the proposal retained base version,
source evidence, rationale, and independent-review evidence. Publish without
Steward review was rejected, and no canon was changed.

## Settled runtime verification — 2026-08-26

- Candidate root: `A:\\Riverview\\standalone`.
- Runtime source SHA: `8bda39ea9f84970bcce012485043bf46f4b87d14`.
- GitHub `origin/main`: `cb4a203274fd0d543ae5140cc036190a4625828c`.
- Candidate relation: 13 commits ahead and 1 commit behind by ancestry; the
  upstream launch-hints content is already represented in the candidate tree.
- One scheduled Runtime Supervisor owner and one logical CME/Relay service
  topology are present; Windows venv launcher/child pairs are one service.
- Operator health and runtime status report matching root, branch, Python
  environment, and SHA. PostgreSQL read-only access succeeds.
- Old `A:\\Riverview\\repo` and the preserved artifact subtree remain intact.

## HOME cognition boundary

The accepted `HomeCognitionService` implementation and E1/F1/F2/F3/P1/P2
seams are present and tested, but the live Grace route still uses the direct
provider-neutral gateway. Read-only PostgreSQL inspection found `grace_identities`
but no Grace row in `resident_occupants`, no active Grace occupancy, no Grace
implementation binding, and no current assignment/context bundle. The required
`AuthoritativeGraceState` therefore cannot be constructed without inventing
UUID-backed institutional state or authority. No direct fallback was upgraded
into HOME cognition.

## Supporting verification

- Final bounded candidate regression: `68 passed`.
- Grace live multi-turn Operator probe: real Ollama/Qwen response, six durable
  messages, role/correlation/provider evidence, and a valid non-binding proposal.
- Jessica live Operator workflow probe: inspect/discuss/propose/independent
  review succeeded; publish-before-Steward-review failed closed.
- Candidate runtime settled proof: all managed services `running` after restart.
- `git diff --check`: passed.

## Notification / stop boundary

No READY_FOR_STEWARD_REVIEW claim is made. Runtime ownership is technically
settled. Grace HOME cognition is not proven live because authoritative Grace
state is absent. The remaining Steward action is to establish the authoritative
Grace resident/occupant, office assignment, implementation binding, and
current-assignment/context projection with provenance, or explicitly authorize
a canonical identity-mapping design. After that state exists, wire and live-test
HOME cognition before issuing a READY notification.
