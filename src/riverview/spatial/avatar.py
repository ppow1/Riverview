"""Reference-only avatar binding; assets never replace resident identity."""

from __future__ import annotations

from dataclasses import dataclass

from riverview.residents.registry import ResidentRecord


@dataclass(frozen=True, slots=True)
class AvatarBinding:
    resident_id: str
    asset_reference: str
    classification: str
    provenance: str


def bind_avatar(record: ResidentRecord, *, asset_reference: str, classification: str) -> AvatarBinding:
    if not asset_reference.strip() or classification not in {"public", "operational", "private", "sensitive"}:
        raise ValueError("RIV-SPAT-0002: avatar asset reference/classification is invalid.")
    return AvatarBinding(record.resident_id, asset_reference, classification, record.provenance)
