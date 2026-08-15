"""Reference-only resident continuity evaluation across provider/interface labels."""

from __future__ import annotations

from dataclasses import dataclass

from .registry import ResidentRecord


@dataclass(frozen=True, slots=True)
class ContinuityEvaluation:
    resident_id: str
    source_reference: str
    provider_id: str
    interface_id: str
    identity_preserved: bool
    classification_preserved: bool


def evaluate_continuity(record: ResidentRecord, *, provider_id: str, interface_id: str) -> ContinuityEvaluation:
    if not provider_id.strip() or not interface_id.strip():
        raise ValueError("RIV-CHAR-0004: continuity provider/interface references are required.")
    return ContinuityEvaluation(
        record.resident_id,
        record.provenance,
        provider_id,
        interface_id,
        True,
        bool(record.classification),
    )
