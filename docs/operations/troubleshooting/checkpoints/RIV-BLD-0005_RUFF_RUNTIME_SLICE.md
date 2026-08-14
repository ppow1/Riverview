<!-- Version: 0.2.1 -->
# RIV-BLD-0005 — Runtime-slice static acceptance failed

Trigger: Ruff rejects River runtime source or tests before live acceptance.

Observed failure classes:

1. `UP035`: an abstract collection type is imported from `typing` instead of `collections.abc`.
2. `DTZ001`: a test constructs a timezone-naive datetime without explicitly showing that intent.
3. Import sorting: a corrected import is placed outside Ruff's standard-library order.
4. Formatting: an automated or manual repair leaves a source file outside repository formatting rules.

Diagnostic procedure: Run `.venv\Scripts\python.exe -m ruff check src tests` and use the exact rule, file, and line. Do not proceed to database acceptance while Ruff fails.

Smallest repair: Move abstract collection imports to `collections.abc`; construct intentional naive test values from a timezone-aware value and remove the timezone explicitly. Change no runtime behavior unrelated to the reported rule.

Verification: Require Ruff, Pytest, Python compilation, database health, and River event smoke acceptance to all pass in that order.

Applicability: Riverview Kernel v0.2.x River runtime slice.