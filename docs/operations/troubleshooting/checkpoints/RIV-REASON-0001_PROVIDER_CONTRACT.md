# RIV-REASON-0001 — Provider-neutral reasoning contract

## SYMPTOM

A reasoning participant is unavailable, emits an unsupported response, exceeds a
bound, or presents a provider-specific contract to Grace.

## BOUNDARY

Provider adapter and typed request/response envelope.

## SAFE DIAGNOSTIC

Validate `ReasoningProvider`, `ReasoningRequest`, and `ReasoningResponse` against
`src/riverview/reasoning/contracts.py`; inspect provider health/capacity separately.

## EXPECTED HEALTHY RESULT

The same bounded envelope is accepted independently of whether the participant is
ChatGPT, Codex, or a future local adapter.

## KNOWN FAILURE / REPAIR

Unknown categories, protected classifications, OpenAI API model routes, oversized
payloads, missing evidence, and arbitrary authority are rejected. Repair the adapter
contract or registration, never the validation boundary.

## VERIFY

Run the reasoning contract tests and provider capability acceptance; confirm no
provider credential or executable instruction is present in the envelope.

## DO NOT

Do not treat provider prose as execution authority or add a provider-specific MCP tool.

## EVIDENCE

Contract version: `riverview-reasoning-v1`; source: `src/riverview/reasoning/contracts.py`.
