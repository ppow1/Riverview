"""Separate character canon, proposals, sessions, and durable continuity.

Runtime conversation can consume accepted state and nominate continuity, but it
cannot silently mutate canon.  The store is intentionally file-backed so the
authoring round trip remains inspectable and recoverable without a database
schema expansion.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(UTC).isoformat()


class _JsonStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.data: dict[str, Any] = {"versions": [], "proposals": [], "continuity": [], "sessions": []}
        if path and path.exists():
            self.data.update(json.loads(path.read_text(encoding="utf-8")))

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)


class CharacterStore(_JsonStore):
    """Versioned accepted resident definitions and governed proposals."""

    @classmethod
    def from_profiles(cls, profiles: tuple[Any, ...], path: Path | None = None) -> CharacterStore:
        store = cls(path)
        if not store.data["versions"]:
            for profile in profiles:
                store.data["versions"].append({
                    "resident_id": profile.resident_id, "version": "v1", "name": profile.name,
                    "role": profile.role, "identity": {"name": profile.name, "role": profile.role},
                    "traits": {}, "speech": {}, "boundaries": {"authority": "runtime cannot confer authority"},
                    "source_evidence": [profile.source_reference, profile.canonical_reference],
                    "author": "Estate bounded registry", "rationale": "bounded identity baseline",
                    "review_state": "accepted", "status": "accepted", "classification": profile.classification,
                    "created_at": _now(), "prior_version": None,
                })
            store.save()
        return store

    def current(self, resident_id: str) -> dict[str, Any]:
        versions = [v for v in self.data["versions"] if v["resident_id"] == resident_id and v["status"] == "accepted"]
        if not versions:
            raise LookupError("RIV-CHAR-0001: accepted resident definition is unavailable.")
        return versions[-1].copy()

    def proposals(self, resident_id: str) -> list[dict[str, Any]]:
        """Return durable proposals for one resident without exposing other canon."""
        return [item.copy() for item in self.data["proposals"] if item["resident_id"] == resident_id]

    def propose(self, resident_id: str, changes: dict[str, Any], *, author: str, source_evidence: list[str], rationale: str, classification: str = "operational") -> dict[str, Any]:
        base = self.current(resident_id)
        proposal = {"proposal_id": f"char-proposal-{uuid4()}", "resident_id": resident_id,
                    "base_version": base["version"], "changes": changes, "author": author,
                    "source_evidence": source_evidence, "rationale": rationale,
                    "review_state": "proposed", "status": "proposed", "classification": classification, "created_at": _now()}
        self.data["proposals"].append(proposal); self.save(); return proposal.copy()

    def review(self, proposal_id: str, *, decision: str, reviewer: str, rationale: str) -> dict[str, Any]:
        if decision not in {"accepted", "rejected", "unresolved"}:
            raise ValueError("RIV-CHAR-0001: review decision is closed.")
        proposal = next((p for p in self.data["proposals"] if p["proposal_id"] == proposal_id), None)
        if proposal is None:
            raise LookupError("RIV-CHAR-0001: character proposal is unavailable.")
        proposal.update({
            "review_state": "independent_review_accepted" if decision == "accepted" else decision,
            "status": "independent_review_accepted" if decision == "accepted" else decision,
            "independent_reviewer": reviewer,
            "independent_review_rationale": rationale,
            "independent_reviewed_at": _now(),
        })
        self.save(); return proposal.copy()

    def steward_review(self, proposal_id: str, *, decision: str, reviewer: str, rationale: str) -> dict[str, Any]:
        """Apply the distinct final Steward review after independent review."""
        if decision not in {"accepted", "rejected", "unresolved"}:
            raise ValueError("RIV-CHAR-0001: review decision is closed.")
        proposal = next((p for p in self.data["proposals"] if p["proposal_id"] == proposal_id), None)
        if proposal is None:
            raise LookupError("RIV-CHAR-0001: character proposal is unavailable.")
        if proposal.get("status") != "independent_review_accepted":
            raise PermissionError("RIV-CHAR-0003: Steward review requires an independent review pass.")
        if reviewer.strip().casefold() != "steward" or not rationale.strip():
            raise PermissionError("RIV-CHAR-0003: final character review must be performed by the Steward with rationale.")
        proposal.update({
            "review_state": "steward_review_accepted" if decision == "accepted" else decision,
            "status": decision,
            "steward_reviewer": reviewer,
            "steward_review_rationale": rationale,
            "steward_reviewed_at": _now(),
        })
        self.save(); return proposal.copy()

    def publish(self, proposal_id: str) -> dict[str, Any]:
        proposal = next((p for p in self.data["proposals"] if p["proposal_id"] == proposal_id), None)
        if proposal is None or proposal["status"] != "accepted":
            raise PermissionError("RIV-CHAR-0001: only an accepted proposal can become canon.")
        base = self.current(proposal["resident_id"])
        version_number = int(base["version"].lstrip("v")) + 1
        published = {**base, **proposal["changes"], "resident_id": base["resident_id"],
                     "version": f"v{version_number}", "prior_version": base["version"],
                     "author": proposal["author"], "source_evidence": proposal["source_evidence"],
                     "rationale": proposal["rationale"], "reviewer": proposal.get("steward_reviewer", "Steward"),
                     "independent_reviewer": proposal.get("independent_reviewer"),
                     "independent_review_rationale": proposal.get("independent_review_rationale"),
                     "steward_reviewer": proposal.get("steward_reviewer"),
                     "steward_review_rationale": proposal.get("steward_review_rationale"),
                     "review_state": "accepted", "status": "accepted", "classification": proposal["classification"], "created_at": _now()}
        self.data["versions"].append(published); proposal["published_version"] = published["version"]; self.save(); return published.copy()


class ContinuityStore(_JsonStore):
    """Session history and accepted continuity are separate state classes."""

    def record_session(self, resident_id: str, session_id: str, turns: list[dict[str, str]]) -> None:
        self.data["sessions"].append({"resident_id": resident_id, "session_id": session_id, "turn_count": len(turns), "status": "history", "created_at": _now()}); self.save()

    def propose(self, resident_id: str, session_id: str, summary: str, *, source_evidence: list[str], classification: str = "operational") -> dict[str, Any]:
        item = {"continuity_id": f"continuity-{uuid4()}", "resident_id": resident_id, "session_id": session_id, "summary": summary, "source_evidence": source_evidence, "classification": classification, "review_state": "proposed", "status": "candidate", "created_at": _now()}
        self.data["continuity"].append(item); self.save(); return item.copy()

    def publish(self, continuity_id: str, *, reviewer: str, rationale: str) -> dict[str, Any]:
        item = next((x for x in self.data["continuity"] if x["continuity_id"] == continuity_id), None)
        if item is None or item["status"] != "candidate":
            raise PermissionError("RIV-CHAR-0002: continuity candidate is unavailable.")
        item.update({"status": "accepted", "review_state": "accepted", "reviewer": reviewer, "rationale": rationale, "published_at": _now()}); self.save(); return item.copy()

    def accepted(self, resident_id: str) -> list[dict[str, Any]]:
        return [x.copy() for x in self.data["continuity"] if x["resident_id"] == resident_id and x["status"] == "accepted"]
