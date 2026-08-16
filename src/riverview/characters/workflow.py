"""Bounded Character Designer workflow; runtime code only consumes its output."""
from __future__ import annotations

from typing import Any

from .store import CharacterStore


class CharacterDesignerWorkflow:
    def __init__(self, store: CharacterStore) -> None:
        self.store = store

    def inspect(self, resident_id: str) -> dict[str, Any]:
        return self.store.current(resident_id)

    def propose(self, resident_id: str, changes: dict[str, Any], *, author: str, sources: list[str], rationale: str) -> dict[str, Any]:
        return self.store.propose(resident_id, changes, author=author, source_evidence=sources, rationale=rationale)

    def review(self, proposal_id: str, *, decision: str, reviewer: str, rationale: str) -> dict[str, Any]:
        return self.store.review(proposal_id, decision=decision, reviewer=reviewer, rationale=rationale)

    def publish(self, proposal_id: str) -> dict[str, Any]:
        return self.store.publish(proposal_id)
