"""Deterministic classification with reference-only protected data handling."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Classification(StrEnum):
    PUBLIC = "public"
    OPERATIONAL = "operational"
    PRIVATE = "private"
    SENSITIVE = "sensitive"
    CREDENTIAL = "credential"
    ADULT_LOCAL = "adult-local"
    UNDERCURRENT = "undercurrent"


def classify_label(value: str) -> Classification:
    try:
        return Classification(value.strip().lower())
    except (AttributeError, ValueError) as exc:
        raise ValueError("RIV-SEC-0001: unknown classification defaults closed.") from exc


@dataclass(frozen=True, slots=True)
class StorageReference:
    reference_id: str
    location_ref: str
    content_sha256: str
    owner: str
    classification: Classification
    size_bytes: int
    media_type: str
    provenance: str
    lifecycle: str = "active"

    def __post_init__(self) -> None:
        fields = (self.reference_id, self.location_ref, self.content_sha256, self.owner, self.media_type, self.provenance)
        if not all(isinstance(item, str) and item.strip() for item in fields):
            raise ValueError("RIV-SEC-0002: storage reference identity and provenance are required.")
        if len(self.content_sha256) != 64 or any(char not in "0123456789abcdefABCDEF" for char in self.content_sha256):
            raise ValueError("RIV-SEC-0002: storage reference hash is invalid.")
        if self.size_bytes < 0 or self.lifecycle not in {"active", "archived", "expired"}:
            raise ValueError("RIV-SEC-0002: storage reference bounds are invalid.")

    def ordinary_river_safe(self) -> bool:
        return self.classification in {Classification.PUBLIC, Classification.OPERATIONAL}
