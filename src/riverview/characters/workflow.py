"""Bounded Character Designer workflow; runtime code only consumes its output."""
from __future__ import annotations

from typing import Any

from .store import CharacterStore


JESSICA_CHARACTER_DEVELOPMENT_WORKFLOW = {
    "workflow_id": "jessica-character-development-v1",
    "owner": "grace",
    "resident_role": "Chief Character Architect",
    "mode": "advisory_workflow",
    "stages": ("inspect", "propose", "independent_review", "steward_review", "publish"),
    "required_evidence": ("source_evidence", "rationale", "base_character_version", "review_record"),
    "authority_boundary": "Grace may coordinate and propose; only an accepted review may publish canon.",
    "prohibited": ("invent_biography", "invent_visual_canon", "self_authorize_canon", "expand_operational_authority"),
}


class CharacterDesignerWorkflow:
    def __init__(self, store: CharacterStore) -> None:
        self.store = store

    def inspect(self, resident_id: str) -> dict[str, Any]:
        return self.store.current(resident_id)

    def propose(self, resident_id: str, changes: dict[str, Any], *, author: str, sources: list[str], rationale: str) -> dict[str, Any]:
        if not isinstance(changes, dict) or not changes:
            raise ValueError("RIV-CHAR-0003: character changes must be a non-empty object.")
        if any(key in {"authority", "operational_authority", "capabilities", "canonical_reference"} for key in changes):
            raise PermissionError("RIV-CHAR-0003: character development cannot expand authority or replace identity anchors.")
        if not author.strip() or not sources or not rationale.strip():
            raise ValueError("RIV-CHAR-0003: author, source evidence, and rationale are required.")
        return self.store.propose(resident_id, changes, author=author, source_evidence=sources, rationale=rationale)

    def review(self, proposal_id: str, *, decision: str, reviewer: str, rationale: str) -> dict[str, Any]:
        proposal = next((item for item in self.store.data["proposals"] if item["proposal_id"] == proposal_id), None)
        if proposal is None:
            raise LookupError("RIV-CHAR-0001: character proposal is unavailable.")
        if reviewer.strip().casefold() == str(proposal.get("author", "")).strip().casefold():
            raise PermissionError("RIV-CHAR-0003: character proposal requires independent review.")
        if not reviewer.strip() or not rationale.strip():
            raise ValueError("RIV-CHAR-0003: reviewer and review rationale are required.")
        return self.store.review(proposal_id, decision=decision, reviewer=reviewer, rationale=rationale)

    def steward_review(self, proposal_id: str, *, decision: str, rationale: str) -> dict[str, Any]:
        return self.store.steward_review(proposal_id, decision=decision, reviewer="Steward", rationale=rationale)

    def publish(self, proposal_id: str) -> dict[str, Any]:
        return self.store.publish(proposal_id)
