# RIV-MIG-0001 — Estate capability inventory boundary

## SYMPTOM

An Estate capability is assumed to exist, be equivalent, or be retired without authoritative evidence.

## BOUNDARY

RV-017.1 inventory before parity or migration work.

## SAFE DIAGNOSTIC

Record capability, state, provenance, classification, and explicit unknowns from source, runtime, and service probes.

## EXPECTED HEALTHY RESULT

The inventory separates active, active-but-unintegrated, unknown, deprecated, and intentionally absent capabilities.

## KNOWN FAILURE / REPAIR

Unverified claims fail closed. Re-probe the bounded source and preserve the prior inventory; do not infer parity.

## VERIFY

Compare each inventory item with its source reference and confirm unknowns remain explicit.

## DO NOT

Do not modify Estate, perform migration, or treat an inventory row as permission to execute or retire a capability.

## EVIDENCE

Evidence: `docs/operations/roadmap/evidence/RV-017.1_ESTATE_CAPABILITY_INVENTORY.json`.
