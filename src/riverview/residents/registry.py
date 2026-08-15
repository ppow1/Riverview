"""Evidence-backed resident registry; generated characterization is not authority."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResidentRecord:
    resident_id: str
    canonical_reference: str
    role: str | None
    provenance: str
    classification: str
    certainty: str
    continuity_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.resident_id.strip() or not self.canonical_reference.strip():
            raise ValueError("RIV-RES-0001: resident identity reference is required.")
        if not self.provenance.strip():
            raise ValueError("RIV-RES-0001: resident provenance is required.")
        if self.certainty not in {"verified", "uncertain", "unknown"}:
            raise ValueError("RIV-RES-0001: resident certainty is closed.")


class ResidentRegistry:
    """In-memory bounded registry used before authoritative records are imported."""

    def __init__(self) -> None:
        self._records: dict[str, ResidentRecord] = {}

    def add(self, record: ResidentRecord) -> None:
        existing = self._records.get(record.resident_id)
        if existing is not None and existing != record:
            raise ValueError("RIV-RES-0001: resident identity has conflicting provenance.")
        self._records[record.resident_id] = record

    def get(self, resident_id: str) -> ResidentRecord:
        try:
            return self._records[resident_id]
        except KeyError as exc:
            raise LookupError("RIV-RES-0001: resident identity is not authoritative.") from exc

    def snapshot(self) -> tuple[ResidentRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))
