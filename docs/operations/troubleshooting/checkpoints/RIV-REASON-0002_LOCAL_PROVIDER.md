# RIV-REASON-0002 — Local reasoning provider boundary

## SYMPTOM

Ollama is unavailable, times out, returns malformed output, emits literal
`<REDACTED>` markers, or a Grace proposal is intermittently malformed.

## BOUNDARY

The local HTTP reasoning adapter between Grace’s provider-neutral envelope and Ollama.

## SAFE DIAGNOSTIC

Probe only the loopback health/model endpoint; validate the model identity, request bounds,
correlation, classification, and returned `ReasoningResponse`. For marker-only Grace output,
compare the raw Ollama `response` field with the persisted/API text hash and marker count.
Run the same prompt through raw `/api/generate` with metadata-only capture, then compare the
model's Modelfile template, stop tokens, temperature, and context settings. Do not print the
prompt, response, hidden reasoning, or credentials.

## EXPECTED HEALTHY RESULT

One bounded local model invocation returns a typed response with provider and evidence references.
The direct-Grace path additionally returns a constrained JSON wrapper, which Riverview
validates before rendering its existing proposal marker. A valid response must yield one
complete bounded proposal or an explicit null proposal; marker-only output is provider failure.

## KNOWN FAILURE / REPAIR

Connection, timeout, invalid JSON, empty response, marker-only output, malformed structured
proposal, or non-loopback endpoint fails closed. If raw Ollama already contains the marker,
the failure is model/template/configuration boundary (not Riverview redaction). If raw output
is valid but typed response differs, repair the adapter. Use Ollama's bounded JSON-schema
format with deterministic low-temperature/capped generation for direct Grace; do not infer a
specification from prose, disable redaction, or switch models without comparative evidence.

## VERIFY

Repeat the measured local request and inspect typed response lineage; record provider health/capacity separately.
For direct Grace, verify repeated identical requests produce valid JSON shape, no marker-only
responses, a parser-valid proposal when appropriate, and no authority before Steward approval.

## DO NOT

Do not send protected payloads, credentials, arbitrary executable instructions, or route through an OpenAI API.

## EVIDENCE

Source: `src/riverview/reasoning/ollama.py`; Cookbook entry: `RIV-REASON-0002`.
