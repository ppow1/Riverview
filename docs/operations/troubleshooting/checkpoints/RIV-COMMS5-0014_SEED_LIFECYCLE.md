# RIV-COMMS5-0014 — Governed seed lifecycle transition

## Symptom

A Comms5 draft cannot be cancelled or superseded truthfully, a cancelled or
superseded draft remains promotable, or lifecycle history is missing from
status/lineage.

## Probe

Inspect the bounded seed row and append-only lifecycle events by seed ID and
idempotency key. Compare the requested transition, current status, replacement
seed, actor, classification, and correlation without reading seed bodies.

## Repair

Use `StewardSeedStore` and migration 0028. Append a lifecycle event, update the
bounded current projection, and emit the corresponding River fact. Never delete
or rewrite the original seed and never cancel or replace an active objective.

## Verification

Create drafts, cancel one, supersede another with a valid replacement, retry
the same transition, and verify status, lineage, history, and promotion guards
at the external Comms5 boundary.

## Do not

Do not promote cancelled/superseded seeds, infer authority from `client_id`,
reuse an idempotency key for a different transition, or expose private seed or
specification content.
