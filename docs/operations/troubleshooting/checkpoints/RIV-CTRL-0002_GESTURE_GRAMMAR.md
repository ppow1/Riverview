# RIV-CTRL-0002 — Gesture grammar ambiguity and destructive guard

## SYMPTOM

An input maps to conflicting actions, lacks context, or a destructive action is bound to an unguarded event.

## BOUNDARY

RV-011.2 gesture validation.

## SAFE DIAGNOSTIC

Validate `(control, event, context)` uniqueness and inspect destructive-event class.

## EXPECTED HEALTHY RESULT

Mappings resolve deterministically; destructive actions require guarded hold semantics.

## REPAIR / VERIFY

Reject ambiguous mappings, add explicit context, and rerun grammar tests.

## DO NOT

Do not promote legacy profiles or bind shutdown to a short/double press.

## EVIDENCE

Source: `src/riverview/control/gestures.py`.
