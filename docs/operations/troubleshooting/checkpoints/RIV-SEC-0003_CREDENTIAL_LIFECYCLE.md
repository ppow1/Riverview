# RIV-SEC-0003 — Credential lifecycle boundary

## SYMPTOM

Credential metadata is missing, expired, revoked, or a secret value appears in an operational record.

## BOUNDARY

RV-013.4 credential lifecycle.

## SAFE DIAGNOSTIC

Inspect owner, classification, reference, fingerprint, status, version, and expiry only.

## EXPECTED HEALTHY RESULT

Only reference/fingerprint metadata persists; expired and revoked credentials fail closed.

## REPAIR / VERIFY

Rotate the reference, revoke the prior record, and verify usability without exposing a secret.

## DO NOT

Do not log, commit, or emit credential values.

## EVIDENCE

Source: `src/riverview/security/credentials.py`.
