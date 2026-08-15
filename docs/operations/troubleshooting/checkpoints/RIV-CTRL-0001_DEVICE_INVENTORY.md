# RIV-CTRL-0001 — Device and control inventory boundary

## SYMPTOM

A control is present but has no stable identity, capability classification, status, provenance, or known mapping.

## BOUNDARY

RV-011.1 machine-readable device/control discovery.

## SAFE DIAGNOSTIC

Use present-only operating-system device records and retain exact instance IDs, class, friendly name, status, and source. Grouping is allowed only when the raw count and source are retained.

## EXPECTED HEALTHY RESULT

Every discoverable control has bounded identity/capability/status/provenance; physical ownership and legacy mappings remain explicitly unknown until evidenced.

## KNOWN FAILURE / REPAIR

Missing PnP records, duplicate identity, stale status, or inferred mapping fails closed. Re-run present-only discovery and preserve the prior inventory as history.

## VERIFY

Compare raw count/class counts and representative stable IDs against the structured evidence file.

## DO NOT

Do not invent cable labels, action mappings, ownership, or a Stream Deck profile from a device ID alone.

## EVIDENCE

Evidence: `docs/operations/roadmap/evidence/RV-011.1_CONTROL_INVENTORY.json`.
