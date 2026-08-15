# RIV-INT-0002 — Repository map and decomposition boundary

## SYMPTOM

A repository map lacks authoritative/ownership seams, or two proposed engineering tasks claim the same mutable path.

## BOUNDARY

RV-012 archaeology and lane decomposition before execution envelopes are formed.

## SAFE DIAGNOSTIC

Validate `RepositoryMap`, `EngineeringTask`, and `reject_path_overlap()`; inspect only bounded structure, paths, and references.

## EXPECTED HEALTHY RESULT

Unknowns remain explicit, ownership is recorded, and non-overlapping tasks can receive separate lanes.

## KNOWN FAILURE / REPAIR

Missing ownership or overlapping paths fails closed. Complete the map or reschedule one task; do not silently merge ownership.

## VERIFY

Run decomposition tests and inspect the resulting envelopes for distinct allowed paths and merge owners.

## DO NOT

Do not treat mapping as permission to rewrite unrelated systems or dispatch from an unaccepted intake.

## EVIDENCE

Source: `src/riverview/intake/engineering.py`; Cookbook entry: `RIV-INT-0002`.
