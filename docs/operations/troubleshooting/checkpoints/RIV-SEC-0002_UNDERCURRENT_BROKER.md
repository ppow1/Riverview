# RIV-SEC-0002 — Protected reference broker boundary

## SYMPTOM

An ordinary River, Comms, provider, or worker path requests a protected reference or attempts to treat a reference decision as payload access.

## BOUNDARY

RV-013.3 explicit identity, capability, purpose, classification, and audit decision.

## SAFE DIAGNOSTIC

Inspect only the reference metadata and the typed decision: caller, capability, purpose, classification, reference identity, and decision reason.

## EXPECTED HEALTHY RESULT

Ordinary callers are denied; an explicitly authorized synthetic broker decision may approve a bounded reference operation while the protected payload remains outside River.

## KNOWN FAILURE / REPAIR

Missing identity, capability, purpose, unsupported capability, or non-protected input fails closed. Repair the request envelope; never broaden ordinary River access.

## VERIFY

Run the synthetic denied/approved fixture tests and verify no payload is returned or embedded.

## DO NOT

Do not expose real protected content, credentials, arbitrary file paths, or implicit administrator authority.

## EVIDENCE

Source: `src/riverview/security/broker.py`; tests: `tests/test_undercurrent_broker.py`.
