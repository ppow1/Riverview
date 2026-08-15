# RIV-SEC-0001 — Closed classification and reference boundary

## SYMPTOM

An unknown or protected artifact is about to enter ordinary River, Comms, or provider storage.

## BOUNDARY

Classification vocabulary and reference-only storage boundary.

## SAFE DIAGNOSTIC

Run `classify_label` and validate `StorageReference`; inspect only identity, hash,
owner, classification, and location reference.

## EXPECTED HEALTHY RESULT

Known classes are deterministic; unknown classes fail closed; large/private payloads
remain outside ordinary source/events.

## KNOWN FAILURE / REPAIR

Unknown labels, invalid hashes, or embedded payloads are rejected. Repair metadata or
retain the data in its authorized classified store; do not copy the payload into GitHub/River.

## VERIFY

Run classification/reference tests and the ordinary River authority audit.

## DO NOT

Do not make an ordinary Comms identity an implicit protected-data capability.

## EVIDENCE

Source: `src/riverview/classification/policy.py`.
