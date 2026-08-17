# RIV-COMMS5-0015 — Comms5 lifecycle idempotency

## Symptom

A retry duplicates a seed lifecycle transition, or a reused idempotency key is
accepted for a different payload or relationship.

## Probe

Look up the canonical row or lifecycle event by idempotency key and compare its
operation, seed IDs, actor, reason, classification, and correlation.

## Repair

Return the original canonical result only for an equivalent retry. Reject
conflicting reuse with a bounded idempotency-conflict error. Preserve the
original event and history.

## Verification

Repeat submission, cancellation, supersession, and promotion with the same key
and then deliberately reuse a key with changed intent.
