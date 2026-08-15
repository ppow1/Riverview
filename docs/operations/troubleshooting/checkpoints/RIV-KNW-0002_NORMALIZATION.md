# RIV-KNW-0002 — Conversation normalization boundary

## SYMPTOM

A message-shaped export is empty, malformed, ambiguously attributed, or turns cannot be ordered from source timestamps.

## BOUNDARY

RV-009.2 normalization from an inventoried source export.

## SAFE DIAGNOSTIC

Validate the bounded list, preserve source message IDs/timestamps, and label missing speakers as `unknown`.

## EXPECTED HEALTHY RESULT

Normalized turns retain source order, provenance, classification, and uncertainty without guessing attribution.

## KNOWN FAILURE / REPAIR

Empty exports, unsupported classifications, or malformed timestamps fail closed. Repair the source export or retain the incomplete record for review.

## VERIFY

Compare normalized turn order and source IDs with the immutable export; replay is idempotent.

## DO NOT

Do not infer a speaker, silently reorder messages, or expose protected payloads to ordinary retrieval.

## EVIDENCE

Source: `src/riverview/knowledge/normalize.py`; Cookbook entry: `RIV-KNW-0002`.
