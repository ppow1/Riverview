"""Bounded resident/session gateway shared by Riverview operator adapters."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from riverview.characters import CharacterStore, ContinuityStore
from riverview.reasoning import ReasoningRequest, ReasoningResponse


class RoomTurnPartialFailure(RuntimeError):
    """A room round stopped after bounded participant results were produced."""

    def __init__(self, completed: list[dict[str, Any]], failed_resident_id: str, cause: Exception) -> None:
        super().__init__(f"room participant {failed_resident_id} failed: {type(cause).__name__}")
        self.completed = completed
        self.failed_resident_id = failed_resident_id
        self.cause_type = type(cause).__name__
        self.failure_class = "provider_timeout" if isinstance(cause, TimeoutError) or "timed out" in str(cause).casefold() else "provider_failure"


@dataclass(frozen=True, slots=True)
class ResidentProfile:
    resident_id: str
    name: str
    role: str
    canonical_reference: str
    source_reference: str
    classification: str = "operational"
    certainty: str = "verified"
    eligible_providers: tuple[str, ...] = ("local",)
    is_grace: bool = False


@dataclass(slots=True)
class ResidentSession:
    session_id: UUID
    resident_id: str
    interface_id: str
    classification: str
    history: list[dict[str, str]] = field(default_factory=list)
    character_version: str = "v1"


class ResidentConversationGateway:
    """Resolve identity and continuity before provider selection or response."""

    def __init__(self, profiles: tuple[ResidentProfile, ...], *, character_store: CharacterStore | None = None, continuity_store: ContinuityStore | None = None) -> None:
        if not profiles:
            raise ValueError("RIV-RES-0002: resident gateway requires profiles.")
        self._profiles = {profile.resident_id: profile for profile in profiles}
        self._by_name = {profile.name.casefold(): profile for profile in profiles}
        self._sessions: dict[UUID, ResidentSession] = {}
        self._rooms: dict[UUID, dict[str, Any]] = {}
        self.character_store = character_store or CharacterStore.from_profiles(profiles)
        self.continuity_store = continuity_store or ContinuityStore()

    @classmethod
    def from_evidence(cls, path: Path | None = None) -> ResidentConversationGateway:
        evidence = path or Path(__file__).resolve().parents[3] / "docs/operations/roadmap/evidence/RV-014.1_RESIDENT_REGISTRY.json"
        payload = json.loads(evidence.read_text(encoding="utf-8"))
        profiles = [
            ResidentProfile(
                resident_id=row["resident_id"],
                name=row["name"],
                role=row["office"],
                canonical_reference=row["canonical_reference"],
                source_reference=row["source_reference"],
                classification=row["classification"],
                certainty=row["certainty"],
            )
            for row in payload["records"]
        ]
        profiles.append(ResidentProfile("grace", "Grace", "Director of Operations", "riverview://grace", "riverview://grace", is_grace=True))
        return cls(tuple(profiles))

    def residents(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                "resident_id": p.resident_id,
                "name": p.name,
                "role": p.role,
                "canonical_reference": p.canonical_reference,
                "classification": p.classification,
                "certainty": p.certainty,
                "eligible_providers": list(p.eligible_providers),
                "operational_participant": p.is_grace,
                "character_version": self.character_store.current(p.resident_id)["version"],
                "accepted_continuity_count": len(self.continuity_store.accepted(p.resident_id)),
            }
            for p in self._profiles.values()
        )

    def resolve(self, resident: str) -> ResidentProfile:
        profile = self._profiles.get(resident) or self._by_name.get(resident.casefold())
        if profile is None:
            raise LookupError("RIV-RES-0002: resident is not authoritative.")
        return profile

    def open_session(self, resident: str, *, interface_id: str, classification: str = "operational") -> ResidentSession:
        profile = self.resolve(resident)
        if classification != profile.classification:
            raise PermissionError("RIV-RES-0002: session classification does not match resident boundary.")
        session = ResidentSession(uuid4(), profile.resident_id, interface_id, classification, character_version=self.character_store.current(profile.resident_id)["version"])
        self._sessions[session.session_id] = session
        return session

    def chat(
        self,
        resident: str,
        instruction: str,
        *,
        provider: Callable[[ReasoningRequest], ReasoningResponse],
        interface_id: str,
        classification: str = "operational",
        session_id: UUID | None = None,
        correlation_id: UUID | None = None,
    ) -> tuple[ResidentSession, ReasoningResponse, dict[str, Any]]:
        profile = self.resolve(resident)
        session = self._sessions.get(session_id) if session_id else None
        if session is None:
            session = self.open_session(profile.resident_id, interface_id=interface_id, classification=classification)
        if session.resident_id != profile.resident_id or session.classification != classification:
            raise PermissionError("RIV-RES-0002: resident session identity or classification mismatch.")
        correlation = correlation_id or uuid4()
        provider_instruction = (
            f"You are responding as the named Riverview resident {profile.name}. "
            f"Your role is {profile.role}. Preserve this resident identity in your response; "
            "do not identify yourself as the underlying model or provider. "
            "This is bounded advisory conversation and does not grant operational authority.\n"
            f"Operator message: {instruction}"
        )
        request = ReasoningRequest(
            request_id=uuid4(), correlation_id=correlation, request_type="advice",
            instruction=provider_instruction, context_refs=(profile.canonical_reference, f"character:{profile.resident_id}:{session.character_version}", *tuple(f"continuity:{x['continuity_id']}" for x in self.continuity_store.accepted(profile.resident_id))),
            classification=classification, required_output_schema="resident-advice-v1",
            evidence_requirements=("resident-identity", "resident-provenance", "correlation"),
            expires_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
            allowed_authority=("read:bounded", "return:advisory"),
        )
        response = provider(request)
        if response.correlation_id != correlation:
            raise RuntimeError("RIV-RES-0002: resident response correlation mismatch.")
        session.history.append({"role": "user", "text": instruction})
        session.history.append({"role": "resident", "text": response.summary})
        addressed_grace = profile.is_grace or bool(re.match(r"^\s*grace\s*[,;:]", instruction, re.IGNORECASE))
        explicit_work = bool(re.search(r"\b(authori[sz]e|promote|create\s+(?:a\s+)?work|start\s+(?:this|the)\s+task)\b", instruction, re.IGNORECASE))
        metadata = {
            "resident_id": profile.resident_id, "resident_name": profile.name,
            "role": profile.role, "canonical_reference": profile.canonical_reference,
            "source_reference": profile.source_reference, "session_id": str(session.session_id),
            "history_turns": len(session.history), "grace_addressed": addressed_grace,
            "execution_intent_detected": addressed_grace and explicit_work,
            "execution_requires_seed_promotion": addressed_grace and explicit_work,
            "role_authority_expanded": False, "character_version": session.character_version,
            "continuity_refs": [x["continuity_id"] for x in self.continuity_store.accepted(profile.resident_id)],
        }
        self.continuity_store.record_session(profile.resident_id, str(session.session_id), session.history)
        return session, response, metadata

    def create_room(self, participants: tuple[str, ...], *, classification: str = "operational") -> UUID:
        resolved = [self.resolve(item) for item in participants]
        if len({p.resident_id for p in resolved}) != len(resolved):
            raise ValueError("RIV-RES-0002: room participants must be unique.")
        room_id = uuid4()
        self._rooms[room_id] = {"room_id": room_id, "participants": tuple(p.resident_id for p in resolved), "classification": classification, "turns": []}
        return room_id

    def restore_room(self, room_id: UUID, participants: tuple[str, ...], *, classification: str = "operational", turns: list[dict[str, Any]] | None = None) -> UUID:
        """Rehydrate a durable room projection without changing continuity authority."""
        resolved = [self.resolve(item) for item in participants]
        if len({p.resident_id for p in resolved}) != len(resolved):
            raise ValueError("RIV-RES-0002: room participants must be unique.")
        self._rooms[room_id] = {"room_id": room_id, "participants": tuple(p.resident_id for p in resolved), "classification": classification, "turns": list(turns or [])}
        return room_id

    def room_snapshot(self, room_id: UUID) -> dict[str, Any]:
        try:
            room = self._rooms[room_id]
        except KeyError as exc:
            raise LookupError("RIV-RES-0002: room is not authoritative.") from exc
        return {**room, "room_id": str(room["room_id"]), "participants": list(room["participants"]), "turns": list(room["turns"]), "no_authority_expansion": True}

    def set_room_participants(self, room_id: UUID, participants: tuple[str, ...]) -> None:
        """Reconcile the bounded room execution roster from authoritative membership."""
        room = self._rooms.get(room_id)
        if room is None:
            raise LookupError("RIV-RES-0002: room is not authoritative.")
        resolved = [self.resolve(item) for item in participants]
        if len({profile.resident_id for profile in resolved}) != len(resolved):
            raise ValueError("RIV-RES-0002: room participants must be unique.")
        room["participants"] = tuple(profile.resident_id for profile in resolved)

    def add_room_turn(self, room_id: UUID, *, speaker: str, text: str, correlation_id: UUID | None = None) -> dict[str, Any]:
        room = self._rooms.get(room_id)
        if room is None or self.resolve(speaker).resident_id not in room["participants"]:
            raise PermissionError("RIV-RES-0002: room speaker is not an admitted resident.")
        turn = {"speaker_id": self.resolve(speaker).resident_id, "text": text, "correlation_id": str(correlation_id or uuid4()), "no_authority_expansion": True}
        room["turns"].append(turn)
        return turn

    def room_chat(self, room_id: UUID, instruction: str, *, provider: Callable[[ReasoningRequest], ReasoningResponse], interface_id: str, correlation_id: UUID | None = None) -> list[dict[str, Any]]:
        """Run one bounded ordered round; resident turns never recurse or gain authority."""
        room = self._rooms.get(room_id)
        if room is None or not instruction.strip():
            raise ValueError("RIV-RES-0002: room request is bounded and requires an existing room.")
        correlation = correlation_id or uuid4()
        results = []
        for resident_id in room["participants"]:
            try:
                session, response, metadata = self.chat(resident_id, instruction, provider=provider, interface_id=interface_id, classification=room["classification"], correlation_id=correlation)
            except Exception as exc:
                raise RoomTurnPartialFailure(results, resident_id, exc) from exc
            turn = {"speaker_id": resident_id, "speaker_name": metadata["resident_name"], "session_id": str(session.session_id), "character_version": metadata["character_version"], "response": response.as_typed_payload(), "no_authority_expansion": True}
            room["turns"].append(turn); results.append(turn)
        return results
