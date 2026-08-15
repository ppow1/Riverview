"""Provenance-preserving idea/decision candidate extraction."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Kind = Literal["source_explicit_decision", "candidate_decision", "idea", "rejected", "unresolved", "ambiguous"]

@dataclass(frozen=True, slots=True)
class ExtractionCandidate:
    candidate_id: str
    project: str
    kind: Kind
    text: str
    source_ref: str
    timestamp: str
    classification: str
    confidence: float
    ambiguity: str | None = None

    def __post_init__(self) -> None:
        if not self.text.strip() or not self.source_ref.strip() or not 0 <= self.confidence <= 1:
            raise ValueError("RIV-KNW-0004: bounded candidate evidence is invalid.")

def extract_candidates(records: list[dict[str, str]], *, project: str) -> tuple[ExtractionCandidate, ...]:
    result=[]
    for i, record in enumerate(records, 1):
        text=record.get("text", "").strip(); kind=record.get("kind", "ambiguous")
        if not text: continue
        if kind not in {"source_explicit_decision","candidate_decision","idea","rejected","unresolved","ambiguous"}: kind="ambiguous"
        result.append(ExtractionCandidate(f"{project}:candidate:{i}", project, kind, text, record.get("source_ref","unknown"), record.get("timestamp","unknown"), record.get("classification","operational"), float(record.get("confidence", "0.0")), record.get("ambiguity")))
    return tuple(result)
