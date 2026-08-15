# RIV-KNW-0001 — Export inventory and provenance boundary

## SYMPTOM

A source export is missing, changes during inventory, lacks a hash, or is about to be copied into ordinary River/source payloads.

## BOUNDARY

RV-009.1 source inventory before normalization and retrieval indexing.

## SAFE DIAGNOSTIC

Hash an existing absolute source file, persist only path/hash/size/classification/provenance, and compare the immutable source on replay.

## EXPECTED HEALTHY RESULT

One immutable source has one idempotent inventory record; originals remain outside GitHub and payload contents are not embedded.

## KNOWN FAILURE / REPAIR

Missing files, hash drift, unknown classification, or duplicate inventory fails closed. Re-inventory the exact source or retain the prior record; do not overwrite history.

## VERIFY

Replay inventory and confirm the same export identity/hash with no duplicate row.

## DO NOT

Do not ingest secrets, protected payloads, or unverified conversation attribution into ordinary River.

## EVIDENCE

Source: `src/riverview/knowledge/inventory.py`; Cookbook entry: `RIV-KNW-0001`.
