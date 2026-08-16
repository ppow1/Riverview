"""Private-payload-free operational observability projection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_PRIVATE_KEYS = frozenset({"payload", "content", "transcript", "artifact", "secret", "token"})


def project_observability(*, services: tuple[dict[str, Any], ...], providers: tuple[dict[str, Any], ...], diagnostics: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    """Return bounded status metadata without request, transcript, or artifact payloads."""

    def safe(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                key: safe(nested)
                for key, nested in value.items()
                if not (isinstance(key, str) and key.casefold() in _PRIVATE_KEYS)
            }
        if isinstance(value, tuple):
            return tuple(safe(item) for item in value)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [safe(item) for item in value]
        return value

    return {
        "services": tuple(safe(row) for row in services),
        "providers": tuple(safe(row) for row in providers),
        "diagnostics": tuple(safe(row) for row in diagnostics),
        "private_payloads_excluded": True,
    }
