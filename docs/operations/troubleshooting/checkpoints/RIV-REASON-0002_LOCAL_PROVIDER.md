# RIV-REASON-0002 — Local reasoning provider boundary

## SYMPTOM

Ollama is unavailable, times out, returns malformed output, or a caller attempts to route the adapter outside loopback.

## BOUNDARY

The local HTTP reasoning adapter between Grace’s provider-neutral envelope and Ollama.

## SAFE DIAGNOSTIC

Probe only the loopback health/model endpoint; validate the model identity, request bounds,
correlation, classification, and returned `ReasoningResponse`.

## EXPECTED HEALTHY RESULT

One bounded local model invocation returns a typed response with provider and evidence references.

## KNOWN FAILURE / REPAIR

Connection, timeout, invalid JSON, empty response, or non-loopback endpoint fails closed.
Repair the local runtime or model selection; do not bypass the adapter contract.

## VERIFY

Repeat the measured local request and inspect typed response lineage; record provider health/capacity separately.

## DO NOT

Do not send protected payloads, credentials, arbitrary executable instructions, or route through an OpenAI API.

## EVIDENCE

Source: `src/riverview/reasoning/ollama.py`; Cookbook entry: `RIV-REASON-0002`.
