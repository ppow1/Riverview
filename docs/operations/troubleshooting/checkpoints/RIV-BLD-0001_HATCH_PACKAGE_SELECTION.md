<!-- Version: 0.1.0 -->
# RIV-BLD-0001: Hatch Cannot Select the Riverview Package

Status: Validated from the initial foundation publication attempt on 2026-08-14.

## Detection

Editable installation fails during Hatch metadata generation with a message stating that no directory matches `riverview_kernel` or that Hatch cannot determine which files to ship.

## Cause

The distribution is named `riverview-kernel`, while the import package is `src/riverview`. Hatch's default package-selection heuristic cannot safely infer that mapping.

## Distinguishing probe

Inspect `pyproject.toml` for:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/riverview"]
```

If the table is absent and `src/riverview/__init__.py` exists, this failure class applies. If the table exists with another path, stop rather than replacing it automatically.

## Smallest safe repair

Add the exact wheel package-selection table above. Do not rename the Python package or distribution merely to satisfy inference.

## Verification

1. Run editable development dependency installation.
2. Run `python -m ruff check src tests`.
3. Run `python -m pytest`.
4. Run `python -m compileall -q src`.

## Escalation

Escalate if Hatch still fails after the explicit package declaration, if another build backend is active, or if more than one distributable package is introduced.
