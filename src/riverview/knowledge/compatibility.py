"""Bounded compatibility transformation with no shared mutable Estate state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CompatibilityResult:
    adapter_id: str
    identity: str
    classification: str
    output: dict[str, Any]
    provenance: str


def adapt_bounded(*, adapter_id: str, identity: str, classification: str, payload: dict[str, Any], provenance: str) -> CompatibilityResult:
    if not all(value.strip() for value in (adapter_id, identity, classification, provenance)):
        raise ValueError("RIV-MIG-0002: compatibility metadata is incomplete.")
    if classification not in {"public", "operational", "private", "sensitive"}:
        raise PermissionError("RIV-MIG-0002: compatibility classification is denied.")
    return CompatibilityResult(adapter_id, identity, classification, dict(payload), provenance)
