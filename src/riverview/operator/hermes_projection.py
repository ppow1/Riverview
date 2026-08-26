"""Derived, secret-safe Hermes execution status projection.

This is an operator read model only.  It does not persist state and never
changes Campaign Runner, River, diagnostics, or acceptance state.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_SECRET_KEYS = {
    "api_key", "apikey", "authorization", "password", "secret", "client_secret",
    "access_token", "refresh_token", "credential", "credentials",
}


def _is_secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in _SECRET_KEYS or normalized.endswith("_secret") or normalized.endswith("_api_key")


def _redact(value: Any) -> tuple[Any, bool]:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        redacted = False
        for key, item in value.items():
            if _is_secret_key(str(key)):
                result[key] = "[REDACTED]"
                redacted = True
            else:
                result[key], child_redacted = _redact(item)
                redacted = redacted or child_redacted
        return result, redacted
    if isinstance(value, list):
        values = []
        redacted = False
        for item in value:
            clean, child_redacted = _redact(item)
            values.append(clean)
            redacted = redacted or child_redacted
        return values, redacted
    if isinstance(value, tuple):
        clean, redacted = _redact(list(value))
        return tuple(clean), redacted
    return value, False


def project_hermes_execution(execution: Mapping[str, Any]) -> dict[str, Any]:
    """Project one execution envelope into a stable basic operator view."""
    if not isinstance(execution, Mapping) or not execution.get("execution_id"):
        raise ValueError("execution_id is required for Hermes projection")
    projected, secrets_redacted = _redact(dict(execution))
    projected.update({
        "execution_id": execution["execution_id"],
        "correlation_id": execution.get("correlation_id"),
        "resident": execution.get("resident_id"),
        "office": execution.get("office") or execution.get("role"),
        "campaign_package_id": execution.get("campaign_package_id") or execution.get("package_id"),
        "attempt_id": execution.get("attempt_id"),
        "hermes_profile": execution.get("hermes_profile") or execution.get("profile"),
        "worker": execution.get("worker_id") or execution.get("worker"),
        "provider": execution.get("provider_id"),
        "model": execution.get("model_ref") or execution.get("model"),
        "resource": execution.get("resource_class_ref") or execution.get("resource"),
        "state": execution.get("state") or execution.get("status"),
        "spawned_workers": list(execution.get("spawned_workers") or ()),
        "evidence_available": bool(execution.get("evidence_refs")),
        "failure": execution.get("failure"),
        "repair_state": execution.get("repair_state"),
        "canonical_reconciliation": execution.get("canonical_reconciliation", "unknown"),
        "acceptance_state": execution.get("acceptance_state", "not_accepted"),
        "secrets_redacted": secrets_redacted,
    })
    return projected


__all__ = ["project_hermes_execution"]
