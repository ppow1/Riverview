"""Canonical policy vocabulary for governed engineering formation."""

READ_ONLY_POLICY = "read_only"
BOUNDED_WRITE_POLICY = "bounded_write"
ENGINEERING_CAPABILITY = "codex.engineering.v1"
ENGINEERING_ACTION = "codex.engineering.v1"
ENGINEERING_POLICIES = frozenset({READ_ONLY_POLICY, BOUNDED_WRITE_POLICY})


def validate_engineering_policy(value: str) -> str:
    if value not in ENGINEERING_POLICIES:
        raise ValueError("RIV-CAP-0004: unsupported Codex engineering write policy.")
    return value
