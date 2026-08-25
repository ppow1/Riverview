<!--
File: docs/operations/roadmap/evidence/GRC-012-E1-writer-evidence.md
Version: 1.0.0
Date: 2026-08-25
Scope: GRC-003-E1 HOME cognition writer evidence only.
-->

# GRC-012-E1 writer evidence

Status: Implemented and focused-tested in the bounded writer worktree.

## Scope delivered

`riverview.reasoning.home_cognition.HomeCognitionService` composes the accepted
F1/F2/F3/P1/P2 seams for one routine Grace `HOME_COGNITION` turn. The service:

- requires an authoritative, non-stale Grace identity/current-state projection;
- opens an identity-preserving F3 cognition session and verifies request/turn readback;
- assembles the accepted bounded F1 packet and rejects transcript-like or oversized context;
- evaluates P1 before admitting HOME generation and returns without a provider request for a
  deterministic decision;
- creates an exact `HOME_COGNITION` capability/resource request and verifies its F2 request fact;
- records the P1 decision against the canonical F2 request;
- requires a corresponding P2 candidate and an already-authorized provider adapter;
- invokes the authorized provider through the existing provider-neutral `ReasoningRequest` /
  `ReasoningResponse` boundary;
- strictly validates request, correlation, provider, classification, schema, live-generation,
  evidence, and advisory-only authority correspondence;
- records truthful F2 started/completed/unavailable/rejected/timed-out facts and verifies event
  readback before returning;
- records a bounded `cognition.home_generation_observed` River fact containing observed provider,
  resource class, capacity, request/response evidence references, outcome, and measured latency.

The returned cognition result is advisory data only. It cannot dispatch execution or widen Grace's
authority.

## Failure boundary

Focused adversarial tests prove fail-closed behavior for:

- absent, stale, substituted, or classification-mismatched authoritative Grace state;
- unbounded invocation/packet/provider context;
- unavailable, substituted, unauthorized, or timed-out providers;
- F3 session/request mismatch;
- F2 request/result/observation readback loss;
- P2 request, correlation, tier, or policy mismatch;
- provider request, correlation, provider, or classification mismatch;
- malformed or extra-field output;
- missing provider provenance;
- false `live_generation`;
- attempted authority widening;
- invalid completed-result fields.

Provider failures return typed non-success `CognitionResult` values with `live_generation=false` and
matching F2 terminal facts. Once a provider call occurs, its latency/capacity observation remains
durable even if strict output validation rejects the response.

## Real provider request/response evidence

`test_actual_loopback_provider_request_and_response_are_observed` starts a real loopback HTTP
provider boundary and invokes the existing `OllamaReasoningAdapter`. The test observes exactly one
`POST /api/generate`, verifies the configured provider/model identity and bounded E1 prompt, returns
an actual HTTP response, and verifies that E1 records provider request and response evidence plus
latency/capacity observation. This is transport-level provider evidence; it does not claim final
model selection, GPU assignment, or production deployment.

## Deterministic non-generation evidence

`test_deterministic_work_never_calls_provider_or_emits_home_generation_event` drives P1 to
`DETERMINISTIC` and verifies:

- zero provider calls;
- no capability request or cognition result;
- no `cognition.started` or `cognition.completed` HOME event;
- no `cognition.home_generation_observed` event.

## Verification

Focused static verification:

```text
ruff check src/riverview/reasoning/home_cognition.py tests/test_home_cognition.py
All checks passed!

ruff format --check src/riverview/reasoning/home_cognition.py tests/test_home_cognition.py
2 files already formatted
```

Focused E1, accepted-seam, provider-neutral, reservation non-regression, and resident gateway run:

```text
python -m pytest -q \
  tests/test_home_cognition.py \
  tests/test_resident_gateway.py \
  tests/test_cognition_contracts.py \
  tests/test_reasoning_context_assembler.py \
  tests/test_cognition_provenance.py \
  tests/test_cognition_provenance_repair.py \
  tests/test_cognition_session.py \
  tests/test_escalation_policy.py \
  tests/test_cognition_binding.py \
  tests/test_cognition_reservation.py \
  tests/test_provider_neutral_contracts.py

Result: PASS
```

The repository-wide run could not provide a clean environment-level result in the managed writer
sandbox. The default interpreter lacks the declared `mcp` dependency. The repository venv collects
the suite but encounters access denial at the pre-existing global pytest temp root and the protected
PostgreSQL credential path; database-dependent tests consequently fail closed. These are environment
access failures, not failures in the passing E1/cognition/gateway set above.

## Explicit exclusions

This change does not implement E2, E3, E4, E5, I1, I2, P3 behavior, CME mechanics, execution
dispatch, final model selection, GPU assignment, provider reservation, or production deployment.
The existing P3 seam is exercised only as a non-regression test and is not called by E1.

## Changed paths

- `src/riverview/reasoning/home_cognition.py`
- `src/riverview/reasoning/__init__.py`
- `tests/test_home_cognition.py`
- `docs/operations/roadmap/evidence/GRC-012-E1-writer-evidence.md`
