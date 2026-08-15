# RIV-CTRL-0005 — Physical safety and recovery boundary

## SYMPTOM

A disconnect, stuck input, duplicate tap, profile drift, emergency stop, or shutdown gesture could produce an unsafe action.

## BOUNDARY

RV-011.5 physical safety and recovery.

## SAFE DIAGNOSTIC

Classify the event and inspect the explicit confirmation flag; no physical action is required for the probe.

## EXPECTED HEALTHY RESULT

Faults fail safe; destructive events require explicit confirmation and identify `RIV-CTRL-0005`.

## REPAIR / VERIFY

Clear the fault, restore the authoritative projection, and rerun induced disconnect/stuck/shutdown guard tests.

## DO NOT

Do not infer confirmation from a gesture, display, timeout, or conversation text.

## EVIDENCE

Source: `src/riverview/control/adapters.py`; tests: `tests/test_control_adapters.py`.
