<!-- Version: 0.1.0 -->
# RIV-BLD-0004: Staged Cookbook Whitespace Rejected

Status: Validated from the fourth initial-foundation publication attempt on 2026-08-14.

## Detection

`git diff --cached --check` reports trailing whitespace in `docs/operations/troubleshooting/README.md` and returns a nonzero exit code.

## Cause

The programmatic insertion of the `RIV-BLD-*` namespace preserved an unwanted whitespace character at the line boundary.

## Distinguishing probe

Run `git diff --cached --check`. This checkpoint applies when the only reported defect is trailing whitespace in the Cookbook index.

## Smallest safe repair

Remove trailing spaces and tabs from the Cookbook index without changing its substantive text, then restage the exact publication paths.

## Verification

1. Rerun `git diff --cached --check`.
2. Confirm the command exits successfully with no output.
3. Continue commit and remote verification gates.

## Escalation

Escalate when whitespace errors affect other files or when normalization would alter substantive content.
