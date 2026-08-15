# RIV-CTRL-0003 — Control projection and disconnect recovery

## SYMPTOM

A control display differs from the bounded PostgreSQL projection or a device disconnect is treated as an action.

## BOUNDARY

RV-011.3/RV-011.4 device adapters.

## SAFE DIAGNOSTIC

Compare control ID, projection version, state, acknowledged action, and disconnect event.

## EXPECTED HEALTHY RESULT

Display state is a projection only; disconnect produces `offline` recovery state and no action.

## REPAIR / VERIFY

Refresh from the authoritative projection and rerun identity, gesture, and disconnect tests.

## DO NOT

Do not let a display become workflow authority or interpret disconnect as shutdown.

## EVIDENCE

Source: `src/riverview/control/adapters.py`.
