"""Canonical policy vocabulary for governed engineering formation."""

from pathlib import Path

READ_ONLY_POLICY = "read_only"
BOUNDED_WRITE_POLICY = "bounded_write"
ENGINEERING_CAPABILITY = "codex.engineering.v1"
ENGINEERING_ACTION = "codex.engineering.v1"
ENGINEERING_POLICIES = frozenset({READ_ONLY_POLICY, BOUNDED_WRITE_POLICY})


def validate_engineering_policy(value: str) -> str:
    if value not in ENGINEERING_POLICIES:
        raise ValueError("RIV-CAP-0004: unsupported Codex engineering write policy.")
    return value


def validate_allowed_paths(paths: tuple[str, ...] | list[str]) -> None:
    if not paths or any(
        not isinstance(path, str)
        or not path.strip()
        or Path(path).is_absolute()
        or path.startswith(("/", "\\"))
        or ".." in path.replace("\\", "/").split("/")
        or path.replace("\\", "/").startswith(".git/")
        for path in paths
    ):
        raise ValueError("RIV-CAP-0002: allowed paths must remain relative and outside Git metadata.")
