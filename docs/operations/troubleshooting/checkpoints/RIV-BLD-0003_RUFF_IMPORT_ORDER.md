<!-- Version: 0.1.0 -->
# RIV-BLD-0003: Ruff Rejects Diagnostic Import Order

Status: Validated from the third initial-foundation publication attempt on 2026-08-14.

## Detection

Ruff reports `I001` for the import block in `src/riverview/diagnostics/models.py` after `Mapping` has been moved to `collections.abc`.

## Cause

The bounded `RIV-BLD-0002` repair placed the new import after other standard-library imports rather than in Ruff's deterministic sorted order.

## Distinguishing probe

Run `python -m ruff check src tests`. This checkpoint applies when `I001` identifies the diagnostic model import block and no unrelated file.

## Smallest safe repair

Move `from collections.abc import Mapping` to the beginning of the standard-library import group immediately after the future import separator.

## Verification

1. Run Ruff against `src` and `tests`.
2. Run pytest.
3. Compile `src`.

## Escalation

Escalate if another file or another formatting rule remains after the exact reorder.
