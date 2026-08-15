"""Project-separated memory publication over immutable evidence references."""

from __future__ import annotations

from dataclasses import dataclass

from .extract import ExtractionCandidate


@dataclass(frozen=True, slots=True)
class ProjectMemoryEntry:
    project: str
    candidate_id: str
    kind: str
    text: str
    source_ref: str
    classification: str
    confidence: float


def publish_candidates(candidates: tuple[ExtractionCandidate, ...]) -> tuple[ProjectMemoryEntry, ...]:
    return tuple(
        ProjectMemoryEntry(c.project, c.candidate_id, c.kind, c.text, c.source_ref, c.classification, c.confidence)
        for c in candidates
    )


def fresh_context(entries: tuple[ProjectMemoryEntry, ...], *, project: str) -> tuple[ProjectMemoryEntry, ...]:
    return tuple(entry for entry in entries if entry.project == project)
