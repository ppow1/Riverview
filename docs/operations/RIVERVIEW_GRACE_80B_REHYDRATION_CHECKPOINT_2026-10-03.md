# Riverview / Grace 80B Rehydration Checkpoint
**Date:** 2026-10-03
**Scope:** Executive engineering checkpoint covering work after the OctoMiner BIOS campaign freeze and the transition of Grace home cognition toward the Qwen3-Next 80B llama.cpp runtime on Octo2.

## Executive Summary

The OctoMiner BIOS campaign was deliberately frozen before this work so its state could be preserved. Octo1 remains the BIOS target. Octo2 is the RTX 4090 machine hosting the currently running Qwen3-Next 80B model.

The Riverview objective was to move Grace's `HOME_COGNITION` implementation away from the previous local Ollama/Qwen3-Coder 30B binding and toward the already-running Qwen3-Next 80B llama.cpp server on Octo2, while preserving Riverview resident identity, policy, classification, structured-output behavior, and unrelated provider routing.

The authoritative resident/database transition succeeded and Riverview was rehydrated. Octo2 llama.cpp is healthy and exposes the expected 80B model. End-to-end live Grace inference is not yet proven. The latest authenticated operator request reached Riverview but was rejected at `RIV-UI-0009` because the bounded request was missing `request_id`. The response reported `provider_calls: []`, so the 80B model was not invoked.

**Authoritative Grace binding transition: successful.**
**Riverview process rehydration: successful.**
**Octo2 80B llama.cpp health/model discovery: successful.**
**Live Grace -> Riverview -> Octo2 80B inference: not yet proven.**

## Machine Roles

### Octo1
Octo1 is the BIOS campaign target only for this phase. It must not be repurposed as Grace's inference host while BIOS work is active. No Octo1, HID, or BIOS action occurred during the Grace transition work.

### Octo2
Established Grace target:

- Host: `Octo2`
- Endpoint: `http://192.168.1.162:8080`
- Provider/runtime: `llama.cpp`
- Device: `RTX 4090`
- Model: `/root/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf`

Live `/v1/models` discovery returned the expected model, approximately 79.67B parameters, with a 65,536 runtime context. `/health` returned `{"status":"ok"}`.

## Original Grace Authoritative Binding

Audit 017B established Grace's pre-transition `HOME_COGNITION` binding:

- Occupant ID: `40f225e2-6f58-55d2-b862-eab7d95700d8`
- Implementation ID: `77fb672c-eb12-5628-aeb6-f5ffa7fbae2e`
- Purpose: `HOME_COGNITION`
- Policy: `grace-home-cognition-policy:v1`
- Key: `grace:implementation:home-cognition:qwen3-coder-30b:ollama-4090`
- Class: `local_ollama`
- Provider: `ollama`
- Model: `qwen3-coder:30b-qwencode-20k`
- Host: `local`
- Device: `RTX 4090`
- Capability profile: `HOME_COGNITION`
- Classification: `internal`
- Configuration: `riverview:home-cognition:ollama`

The expected and actual implementation IDs matched before modification.

## llama.cpp Adapter Investigation and Repair

The existing `src/riverview/reasoning/llama_cpp.py` adapter was loopback-only and rejected endpoints other than `127.0.0.1` or `localhost`. Its legacy path called `/completion`. It therefore could not legitimately route Grace from Riverview to Octo2 over the private LAN.

### Repair 004C

The adapter was repaired rather than bypassed. The revised adapter:

- keeps loopback as the default;
- permits private-LAN IPs only with explicit `allow_private_lan=True`;
- rejects public Internet hosts;
- retains legacy `/completion` behavior;
- adds `/v1/chat/completions`;
- uses `temperature=0` and `stream=False`;
- preserves model selection;
- carries `response_format` through as strict JSON Schema;
- preserves correlation ID and classification;
- returns a Riverview `ReasoningResponse`;
- identifies the provider as `llama-cpp:<model>`.

Compilation and mocked tests passed for loopback behavior, private-LAN opt-in, chat endpoint, model preservation, strict schema preservation, correlation/classification, provider ID, and returned summary. No live model was called.

Backup created:

`A:\Riverview\standalone\src\riverview\reasoning\llama_cpp.py.before-grace-octo2-80b-20261003`

## Transition Preflight

The first 004F preflight failed because the temporary script lacked the Riverview source tree on `PYTHONPATH`:

`ModuleNotFoundError: No module named 'riverview'`

004F-1 corrected this with:

`PYTHONPATH=A:\Riverview\standalone\src`

The real persistence contract was then inspected, including:

- `register_implementation(...)`
- `active_implementation_binding(...)`
- `transition_implementation(...)`

The transition method was confirmed transactional and idempotency-keyed. It validates the predecessor and registered replacement, inserts the successor binding, retires the predecessor, records transition/context-invalidated events, and returns the new binding ID.

## Target Grace Implementation

- Key: `grace:implementation:home-cognition:qwen3-next-80b:llama-cpp-octo2`
- Class: `local_llama_cpp`
- Version: `grace-home-cognition-e1-v1`
- Provider: `llama_cpp`
- Model: `/root/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf`
- Host: `Octo2`
- Device: `RTX 4090`
- Capability: `HOME_COGNITION`
- Classification: `internal`
- Configuration: `http://192.168.1.162:8080`

## Authoritative Transition — Repair 004G

Before:

- Binding: `029ac02f-e826-5c16-af73-c7f8e764f2c4`
- Implementation: `77fb672c-eb12-5628-aeb6-f5ffa7fbae2e`

New implementation:

- Implementation ID: `877b17d1-ae78-4257-a380-edb707fa722c`

New binding:

- Binding ID: `050eb03e-dd5d-5749-92c1-de59ffc917f4`

Transition key:

`grace-home-cognition-qwen3-next-80b-llama-cpp-octo2-20261003`

Authoritative readback showed the new binding active with `HOME_COGNITION`, policy `grace-home-cognition-policy:v1`, provider `llama_cpp`, the 80B GGUF on Octo2/RTX 4090, internal classification, and the Octo2 endpoint configuration. All acceptance checks passed.

This was a real database/binding change. It did not call the model, restart services, touch Octo1, invoke Hermes, perform HID, or perform BIOS actions.

## Runtime Discovery

Repair 004H established the actual running Riverview tree:

- `riverview.runtime.supervisor`
- `riverview.operator.live_service`
- `riverview.autonomy.live_service`
- `riverview.relay.worker`

The operator runtime listened on port `18082`.

Unrelated Hermes and OctoMiner BIOS campaign processes were present and treated as out of scope.

A critical discovery was that live-service source still referenced `OllamaReasoningAdapter`. Therefore the correct database binding alone was not sufficient evidence that runtime requests would use llama.cpp. Actual dispatch still had to be proven.

## Riverview Rehydration

An initial attempt to recycle only the operator did not replace the old process tree. Inspection showed Windows launcher/runtime pairs managed by the supervisor.

Repair 004I-3 therefore performed a controlled Riverview supervisor-tree restart. The old supervisor, operator, autonomy, and relay launcher/runtime processes were terminated, then Riverview was restarted from:

`A:\Riverview\standalone\.venv\Scripts\python.exe -m riverview.runtime.supervisor`

Acceptance:

- old tree process count: `0`
- port 18082 listening: `True`
- old PIDs reused: `False`
- `RIVERVIEW_READY=True`
- Hermes still running: `True`
- BIOS campaign still running: `True`
- `ALL_CHECKS_PASS=True`

Riverview was rehydrated without restarting Hermes or disturbing the BIOS campaign.

## Live Grace Testing

### TEST 004M
The first live request returned `401 Unauthorized`. This established that the operator interface required authentication/session handling. Octo2 remained healthy.

### TEST 004M-2
An authenticated session was created successfully with HTTP 200.

Diagnostic request:

> Grace, identify yourself and briefly state your role in Riverview. This is a diagnostic inference test only. Do not execute any action.

The authenticated request returned `400 Bad Request` with:

```json
{
  "error": "bounded_request_rejected",
  "checkpoint": "RIV-UI-0009",
  "cause_checkpoint": "unavailable",
  "reason": "'request_id'",
  "provider_calls": []
}
```

This is the current end-to-end blocker. Authentication succeeded and the request reached Riverview bounded-request validation, but failed before provider dispatch because `request_id` was absent. The explicit empty provider-call list proves this test invoked neither Ollama nor llama.cpp/80B.

Octo2 remained healthy afterward.

## Current Proven State

1. Grace's authoritative resident identity and `HOME_COGNITION` purpose were preserved.
2. Grace's active implementation binding transitioned from Ollama/Qwen3-Coder 30B to llama.cpp/Qwen3-Next 80B on Octo2.
3. Octo2 llama.cpp is reachable and healthy.
4. The expected 80B GGUF is loaded and exposed.
5. Riverview has a llama.cpp adapter capable of explicitly approved private-LAN routing.
6. The adapter supports OpenAI-compatible chat completion and structured JSON Schema.
7. Riverview supervisor/operator/autonomy/relay were fully restarted and rehydrated.
8. Hermes remained running and was not restarted.
9. The BIOS campaign remained running and was not restarted.
10. Octo1 was not touched.
11. The authenticated live Grace request reaches Riverview but fails bounded validation because `request_id` is missing.
12. Successful live Grace -> Octo2 80B inference is not yet demonstrated.

## Important Non-Claims

Do not state yet that Grace is proven to be actively reasoning through Octo2's 80B model.

The authoritative database binding says that is Grace's selected `HOME_COGNITION` implementation, but runtime dispatch has not completed successfully.

A correct binding, healthy Octo2 server, loaded model, restarted Riverview, and listening operator service are necessary evidence, but not final inference-path proof.

## Immediate Next Engineering Step

Construct a valid authenticated bounded operator request containing `request_id` and every other contract-required field, then observe actual provider dispatch.

The test remains diagnostic-only and prohibits action execution.

Acceptance should include:

- successful operator HTTP response;
- Grace response;
- provider evidence showing `llama_cpp`;
- Octo2 endpoint/model identity;
- preserved correlation/classification/structured-output behavior;
- no Hermes call unless deliberately requested;
- no Octo1/HID/BIOS action.

If the request passes `RIV-UI-0009` but routes to the old Ollama adapter, the next repair belongs in live provider selection/runtime routing, not the resident binding.

## Lessons Learned

### Authoritative state and runtime state are different layers
A correct database binding does not prove the live service rehydrated or dispatch follows that binding.

### Inspect contracts before mutating
Inspecting persistence and transition APIs before the transition prevented blind database manipulation.

### Preserve idempotency and provenance
The transition used Riverview's own transactional/idempotent boundary rather than ad-hoc SQL.

### Rehydrate the actual managed tree
Recycling one apparent Python process was insufficient because the supervisor creates launcher/runtime pairs.

### Listening is not inference readiness
Port 18082 proved the operator existed, not that Grace could complete a bounded request.

### Provider health is not routing proof
Octo2 `/health` and `/v1/models` prove availability, not that Riverview dispatched Grace there.

### Preserve the BIOS campaign boundary
Octo1 remains the BIOS target. Grace inference belongs on Octo2 during this phase.

### Durable evidence must live outside chat
This work generated enough architecture and operational knowledge that leaving it only in conversational context would cause rediscovery and contradictory repairs.

## BIOS Campaign Relationship

The BIOS campaign was frozen before Grace work and remains independently documented.

Relevant cross-project facts:

- Octo1 is the BIOS target.
- Octo2 is the RTX 4090 / 80B inference host.
- BIOS campaign processes survived Riverview rehydration.
- No BIOS or HID action occurred during the Grace transition.
- Grace inference work must not silently consume Octo1 or alter BIOS campaign state.

## Recommended Repository Location

Primary document:

`docs/operations/RIVERVIEW_GRACE_80B_REHYDRATION_CHECKPOINT_2026-10-03.md`

Potential selective cross-feed later:

- `docs/operations/octominer/campaign/PROVEN_FACTS.md`
- `docs/operations/octominer/campaign/LESSONS_LEARNED.md`
- `docs/operations/octominer/campaign/CAMPAIGN_STATE.md`

The master checkpoint should remain intact.

---

**Checkpoint status:** Durable engineering handoff prepared.
**Current stopping point:** authenticated live Grace request is blocked at `RIV-UI-0009` by missing `request_id`; provider dispatch and successful Octo2 80B inference remain to be proven.

## 2026-10-03 Single-Pass Grace Restoration

Grace home cognition is now operational on the Qwen3-Next 80B llama.cpp runtime on Octo2.

Investigation showed that the major latency and normal-chat failure were not caused by VNext, the legacy Operator UI, authentication, Octo2 health, or the Grace implementation binding. Riverview's occupational reasoning path was deliberately performing multiple model passes around a single conversational turn, including scope adjudication, repair, second-pass synthesis, and epistemic repair.

The epistemic machinery had originally been introduced to distinguish deterministic/state-machine behavior from model-generated reasoning. Direct provider-call telemetry now independently identifies the cognition provider, model, resource, phase, timing, and status. Therefore epistemic metadata is no longer allowed to block an otherwise valid normal conversational response.

The legacy multipass/capability machinery remains in source for later reconsideration. Ordinary first-pass answers now return immediately. Capability requests continue into the existing bounded capability path.

### Acceptance Test 004R

A live authenticated Grace request completed successfully with:

- HTTP status: 200
- Provider calls: 1
- Phase: first
- Provider: llama_cpp
- Model: /root/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf
- Resource: RTX 4090
- Provider status: success
- Provider duration: 10451.29 ms
- End-to-end duration: 10794.02 ms
- One-provider-call acceptance: true
- Qwen3-Next 80B acceptance: true
- Overall acceptance: true

Grace responded as Grace from Riverview's Office of Operations. No action was authorized or executed.

The approximately 10.8-second remaining latency is now overwhelmingly provider inference time: approximately 10.45 seconds occurred inside the single 80B provider call, leaving roughly 0.34 seconds of Riverview/API overhead.

### Current Working Architecture

Normal conversational path:

User request -> Riverview -> Grace first-pass cognition -> llama.cpp -> Octo2 Qwen3-Next 80B -> response

The desired one-request / one-inference / one-response behavior is therefore proven.

### Follow-up

Do not reintroduce mandatory epistemic repair into ordinary conversation without reevaluating its current value and latency cost.

Future latency optimization should treat the Qwen3-Next 80B inference runtime separately from Riverview orchestration.

The broader model-selection architecture should also be simplified later so changing a resident's home cognition model does not require coordinated changes across multiple configuration and runtime seams.
