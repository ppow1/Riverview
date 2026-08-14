<!-- Version: 0.1.0 -->
# RIV-BLD-0002: Ruff Rejects Mapping Imported from typing

Status: Validated from the second initial-foundation publication attempt on 2026-08-14.

## Detection

Ruff reports `UP035` in `src/riverview/diagnostics/models.py` and directs that `Mapping` be imported from `collections.abc`.

## Cause

The diagnostic model imported `Mapping` from `typing`. Under the configured Python 3.12 target, Ruff requires the modern runtime collection interface from `collections.abc`.

## Distinguishing probe

Run:

```text
python -m ruff check src tests
```

This failure applies only when `UP035` identifies `Mapping` on the diagnostic model import line.

## Smallest safe repair

Import `Mapping` from `collections.abc` while retaining `Any` from `typing`. Do not run an unrestricted repository-wide automatic rewrite.

## Verification

1. Run Ruff against `src` and `tests`.
2. Run pytest.
3. Compile `src`.

## Escalation

Escalate if Ruff reports another rule, another file, or additional import restructuring after this bounded change.
