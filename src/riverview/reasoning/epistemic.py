"""Provider-neutral epistemic labels and lightweight message provenance."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

VERIFIED = 1
CANON = 2
REASONED = 4
GENERAL = 8
CREATIVE = 16
UNKNOWN = 32
ALL_MASK = VERIFIED | CANON | REASONED | GENERAL | CREATIVE | UNKNOWN
_LABELS = ((VERIFIED, "VERIFIED"), (CANON, "CANON"), (REASONED, "REASONED"), (GENERAL, "GENERAL"), (CREATIVE, "CREATIVE"), (UNKNOWN, "UNKNOWN"))
SOURCE_CLASSES = frozenset({"institutional", "live_telemetry", "postgresql", "river", "local_artifact", "repository", "steward", "canon", "external_authoritative", "web_research", "cross_validation"})


def mask_labels(mask: int) -> list[str]:
    if not isinstance(mask, int) or mask < 0 or mask & ~ALL_MASK:
        raise ValueError("epistemic mask is invalid")
    return [label for bit, label in _LABELS if mask & bit]


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    source_class: str
    evidence_ref: str
    observed_at: datetime | None = None
    freshness: str | None = None
    capability: str | None = None
    source_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.source_class not in SOURCE_CLASSES:
            raise ValueError("provenance source class is invalid")
        if not self.evidence_ref or len(self.evidence_ref) > 240:
            raise ValueError("provenance evidence reference is required and bounded")
        if self.freshness is not None and len(self.freshness) > 80:
            raise ValueError("provenance freshness is bounded")
        if self.capability is not None and len(self.capability) > 160:
            raise ValueError("provenance capability is bounded")
        if len(self.source_refs) > 8 or any(not isinstance(x, str) or not x for x in self.source_refs):
            raise ValueError("provenance source references are bounded")

    def as_dict(self) -> dict[str, Any]:
        return {"source_class": self.source_class, "evidence_ref": self.evidence_ref, "observed_at": self.observed_at.isoformat() if self.observed_at else None, "freshness": self.freshness, "capability": self.capability, "source_refs": list(self.source_refs)}


@dataclass(frozen=True, slots=True)
class EpistemicSpan:
    span_id: str
    start: int
    end: int
    mask: int
    provenance: tuple[ProvenanceRecord, ...] = ()

    def __post_init__(self) -> None:
        if not self.span_id or len(self.span_id) > 120:
            raise ValueError("span identity is required and bounded")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("span bounds are invalid")
        mask_labels(self.mask)
        if len(self.provenance) > 8:
            raise ValueError("span provenance is bounded")

    def as_dict(self) -> dict[str, Any]:
        return {"span_id": self.span_id, "start": self.start, "end": self.end, "mask": self.mask, "labels": mask_labels(self.mask), "provenance": [x.as_dict() for x in self.provenance]}


def build_epistemic_metadata(spans: list[EpistemicSpan], *, response_text: str) -> dict[str, Any]:
    if len(response_text) > 8000:
        raise ValueError("response text is too large")
    for span in spans:
        if span.end > len(response_text):
            raise ValueError("span exceeds response text")
    summary = 0
    for span in spans:
        summary |= span.mask
    return {"schema_version": "resident-epistemic-v1", "summary_mask": summary, "summary_labels": mask_labels(summary), "spans": [x.as_dict() for x in spans]}
