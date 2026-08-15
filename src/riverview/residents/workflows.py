"""Advisory design workflows with explicit review and destination metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DesignProposal:
    author_reference: str
    rationale: str
    review_state: str
    destination: str


def propose_design(*, author_reference: str, rationale: str, destination: str) -> DesignProposal:
    if not all(value.strip() for value in (author_reference, rationale, destination)):
        raise ValueError("RIV-CHAR-0002: design proposal metadata is incomplete.")
    return DesignProposal(author_reference, rationale, "review_required", destination)
