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

The Grace-owned Jessica workflow contract is exposed in the resident gateway,
but no live Jessica conversation was accepted in this baseline, and the
Operator does not yet provide a dedicated interactive inspect/discuss/propose
character-development control surface. The existing generic proposal/review
workflow is implementation evidence, not live behavioral acceptance.

## Supporting verification

- Targeted Grace/Jessica/operator/cognition tests: `30 passed`.
- Python compilation: passed.
- `git diff --check`: passed.
- System Python without `PYTHONPATH=src`: blocked by package-install environment;
  this is not used as capability evidence.
- Live Operator health: HTTP 200, but alternate-checkout SHA mismatch means it
  is not authoritative evidence for this checkout.

## Notification / stop boundary

This report is a genuine Steward boundary because proceeding requires both:

1. an authoritative Grace cognition-state/runtime adapter decision; and
2. reconciliation of the installed Operator lifecycle owner with the intended
   authoritative checkout without disturbing unrelated alternate-checkout work.

No READY_FOR_STEWARD_REVIEW claim is made. The next safe action is to resolve
that bounded authority/runtime decision, then implement and live-test the E1
cognition adapter and the interactive Jessica character-development path.
