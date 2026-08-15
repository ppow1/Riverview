# RIV-KNW-0003 — Classification-first retrieval

## SYMPTOM

A retrieval query is unbounded, uses an unknown classification, or ranks content before access filtering.

## BOUNDARY

RV-009.3 normalized-turn search.

## SAFE DIAGNOSTIC

Run a bounded known-term query and inspect the classification predicate and limit before ranking.

## EXPECTED HEALTHY RESULT

Known operational terms retrieve the expected turn; protected/unknown classifications return no ordinary result.

## KNOWN FAILURE / REPAIR

Invalid classification, empty query, or limit overflow fails closed/clamps. Repair the fixed query path; do not expose a generic search backend.

## VERIFY

Run the benchmark, exclusion, and replay/rebuild tests.

## DO NOT

Do not rank or leak protected results before applying classification filtering.

## EVIDENCE

Source: `src/riverview/knowledge/search.py`; Cookbook entry: `RIV-KNW-0003`.
