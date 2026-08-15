# RIV-NOT-0001 — Exactly-once bounded notification

## SYMPTOM

A genuine Steward checkpoint or critical failure is not represented, is duplicated, or contains sensitive/unbounded payload.

## BOUNDARY

Notification record creation/delivery before an external notification adapter.

## SAFE DIAGNOSTIC

Inspect `steward_notifications` by idempotency key, checkpoint, state, and evidence references.

## EXPECTED HEALTHY RESULT

One bounded summary/reference notification exists per logical event; retries return the same identity.

## KNOWN FAILURE / REPAIR

Unknown type, missing checkpoint/evidence, oversized summary, or duplicate delivery fails closed. Repair the typed record or retry the same idempotency key.

## VERIFY

Emit twice and mark delivery once; verify one row and one delivery transition.

## DO NOT

Do not include secrets, protected payloads, arbitrary conversation text, or generic execution commands.

## EVIDENCE

Source: `src/riverview/notifications.py`; Cookbook entry: `RIV-NOT-0001`.
