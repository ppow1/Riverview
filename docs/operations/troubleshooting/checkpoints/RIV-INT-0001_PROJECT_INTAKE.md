# RIV-INT-0001 — Project intake completeness

## SYMPTOM

An intake is incomplete or attempts to become executable work before owner intent and acceptance are complete.

## BOUNDARY

Project intake validation before decomposition or dispatch.

## SAFE DIAGNOSTIC

Call `ProjectIntake.missing_fields()` and `validate()`; inspect no more than bounded
metadata and references.

## EXPECTED HEALTHY RESULT

Missing fields are named exactly and complete intake remains an intent record only.

## KNOWN FAILURE / REPAIR

Missing mission, repository, outcome, acceptance, or classification blocks intake.
Repair the intake record with owner-provided values; never infer a goal.

## VERIFY

Run intake contract tests and confirm no work order or roadmap transition is created.

## DO NOT

Do not dispatch from an intake draft or turn free-form text into a provider/action.

## EVIDENCE

Source: `src/riverview/intake/contract.py`.
