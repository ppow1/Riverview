# RIV-CAP-0001 — Capability registry and deterministic dispatch

SYMPTOM: A bounded engineering task has no selected provider or selection is not
explainable from current capacity.

LIKELY BOUNDARY: Capability registration, measured health, capacity freshness/load,
or provider backoff.

SAFE DIAGNOSTIC: Query `capabilities` joined to `capability_capacity`; compare the
task in `supported_tasks`, `health_status`, `observed_at`, `current_load`, and
`backoff_until`.

EXPECTED HEALTHY RESULT: One enabled healthy measured capability with available
capacity is selected deterministically by current load then name.

KNOWN FAILURE: `RIV-CAP-0001` rejects invalid registration; `RIV-CAP-0002` rejects
missing or overcommitted capacity; no selection is a provider/checkpoint boundary,
not permission to use an unregistered process.

REPAIR: Refresh measured capability evidence or bounded telemetry. Do not substitute a
descriptive provider label for a health probe.

VERIFY: Repeat selection and retain the capability/version, observed capacity, and
correlation in the execution envelope.

The freshness failure/recovery probe was verified on 2026-08-15 by aging the local
Codex telemetry beyond the five-minute bound (selection returned no provider), then
refreshing the measured telemetry (selection returned `codex.engineering.v1`).

DO NOT: route to an OpenAI API model, bypass capacity/backoff, or expose provider
credentials in an envelope or Cookbook entry.

EVIDENCE: `capabilities`, `capability_capacity`, `execution_envelopes`, and the
selection correlation.
