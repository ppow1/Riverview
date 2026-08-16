"""Private-payload-free operational observability projection."""

from __future__ import annotations

from typing import Any


def project_observability(*, services: tuple[dict[str, Any], ...], providers: tuple[dict[str, Any], ...], diagnostics: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    """Return bounded status metadata without request, transcript, or artifact payloads."""

    def safe(row: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in row.items() if key not in {"payload", "content", "transcript", "artifact", "secret", "token"}}

    return {
        "services": tuple(safe(row) for row in services),
        "providers": tuple(safe(row) for row in providers),
        "diagnostics": tuple(safe(row) for row in diagnostics),
        "private_payloads_excluded": True,
    }
