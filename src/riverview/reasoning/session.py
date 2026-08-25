"""Identity-preserving cognition session boundary for GRC-003-F3.

This module owns session identity and session-to-request correspondence.  It
does not invoke a provider, select a resource, interpret transcript content,
or grant execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from riverview.reasoning.cognition_contracts import CapabilityResourceRequest
from riverview.river.events import Classification, RiverEvent

SESSION_SCHEMA_VERSION = "cognition-session-f3-v1"
SESSION_AGGREGATE_TYPE = "cognition_session"
SESSION_CHECKPOINT = "RIV-COG-SESSION-0001"
MAX_SESSION_REFS = 64
MAX_REF_LENGTH = 512


class CognitionSessionError(ValueError):
    """Fail-closed F3 session boundary error."""


def _uuid(value: UUID, name: str) -> UUID:
    if not isinstance(value, UUID):
        raise CognitionSessionError(f"{SESSION_CHECKPOINT}: {name} is invalid.")
    return value


def _ref_tuple(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple) or len(values) > MAX_SESSION_REFS:
        raise CognitionSessionError(f"{SESSION_CHECKPOINT}: {name} is unbounded.")
    if any(not isinstance(value, str) or not value.strip() or len(value) > MAX_REF_LENGTH for value in values):
        raise CognitionSessionError(f"{SESSION_CHECKPOINT}: {name} contains an invalid reference.")
    return values


def _when(value: datetime, name: str = "occurred_at") -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise CognitionSessionError(f"{SESSION_CHECKPOINT}: {name} must be timezone-aware.")
    return value


@dataclass(frozen=True, slots=True)
class CognitionSession:
    """Estate session identity, deliberately distinct from request/result IDs."""

    session_id: UUID
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    authority_ref: str
    state_refs: tuple[str, ...]
    opened_at: datetime
    status: str = "active"
    schema_version: str = SESSION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("session_id", "resident_id", "occupant_id", "office_id", "implementation_id"):
            _uuid(getattr(self, name), name)
        if self.resident_id == self.session_id:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: session identity must not be resident identity.")
        if not isinstance(self.authority_ref, str) or not self.authority_ref.strip() or len(self.authority_ref) > MAX_REF_LENGTH:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: authority_ref is invalid.")
        _ref_tuple(self.state_refs, "state_refs")
        _when(self.opened_at, "opened_at")
        if self.status not in {"active", "closed"} or self.schema_version != SESSION_SCHEMA_VERSION:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: session envelope is invalid.")

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "session_id": str(self.session_id),
            "resident_id": str(self.resident_id),
            "occupant_id": str(self.occupant_id),
            "office_id": str(self.office_id),
            "implementation_id": str(self.implementation_id),
            "authority_ref": self.authority_ref,
            "state_refs": list(self.state_refs),
            "opened_at": self.opened_at.isoformat(),
            "status": self.status,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CognitionSession":
        if not isinstance(payload, dict) or payload.get("schema_version") != SESSION_SCHEMA_VERSION:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: session schema is unsupported.")
        try:
            values = {
                name: UUID(str(payload[name]))
                for name in ("session_id", "resident_id", "occupant_id", "office_id", "implementation_id")
            }
            opened_at = datetime.fromisoformat(str(payload["opened_at"]))
            refs = tuple(payload.get("state_refs", ()))
        except (KeyError, TypeError, ValueError) as exc:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: session payload is malformed.") from exc
        return cls(**values, authority_ref=payload.get("authority_ref"), state_refs=refs,
                   opened_at=opened_at, status=payload.get("status"), schema_version=payload["schema_version"])


@dataclass(frozen=True, slots=True)
class CognitionSessionTurn:
    """A bounded durable association; request identity remains request identity."""

    session_id: UUID
    request_id: UUID
    correlation_id: UUID
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    authority_ref: str
    attached_at: datetime
    schema_version: str = SESSION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("session_id", "request_id", "correlation_id", "resident_id", "occupant_id", "office_id", "implementation_id"):
            _uuid(getattr(self, name), name)
        if self.session_id == self.request_id:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: session and request identities must remain distinct.")
        if not isinstance(self.authority_ref, str) or not self.authority_ref.strip() or len(self.authority_ref) > MAX_REF_LENGTH:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: authority_ref is invalid.")
        _when(self.attached_at, "attached_at")
        if self.schema_version != SESSION_SCHEMA_VERSION:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: turn schema is unsupported.")

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "session_id": str(self.session_id), "request_id": str(self.request_id),
            "correlation_id": str(self.correlation_id), "resident_id": str(self.resident_id),
            "occupant_id": str(self.occupant_id), "office_id": str(self.office_id),
            "implementation_id": str(self.implementation_id), "authority_ref": self.authority_ref,
            "attached_at": self.attached_at.isoformat(),
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CognitionSessionTurn":
        if not isinstance(payload, dict) or payload.get("schema_version") != SESSION_SCHEMA_VERSION:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: turn schema is unsupported.")
        try:
            values = {name: UUID(str(payload[name])) for name in (
                "session_id", "request_id", "correlation_id", "resident_id", "occupant_id", "office_id", "implementation_id")}
            attached_at = datetime.fromisoformat(str(payload["attached_at"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: turn payload is malformed.") from exc
        return cls(**values, authority_ref=payload.get("authority_ref"), attached_at=attached_at,
                   schema_version=payload["schema_version"])


class SessionEventStore(Protocol):
    def append(self, event: RiverEvent) -> Any: ...

    def read_aggregate(self, aggregate_type: str, aggregate_id: UUID) -> list[dict[str, Any]]: ...


class CognitionSessionBoundary:
    """Create and correlate identity-preserving sessions without cognition."""

    def __init__(self, event_store: SessionEventStore | None = None) -> None:
        self.event_store = event_store

    def open(
        self, *, resident_id: UUID, occupant_id: UUID, office_id: UUID,
        implementation_id: UUID, authority_ref: str, state_refs: tuple[str, ...] = (),
        session_id: UUID | None = None, opened_at: datetime | None = None,
    ) -> CognitionSession:
        session = CognitionSession(
            session_id=session_id or uuid4(), resident_id=resident_id, occupant_id=occupant_id,
            office_id=office_id, implementation_id=implementation_id, authority_ref=authority_ref,
            state_refs=state_refs, opened_at=opened_at or datetime.now(UTC),
        )
        self._append("cognition.session.opened", session.session_id, f"opened:{session.session_id}", session.as_payload(), session.opened_at)
        return session

    def open_from_runtime(self, runtime_session: Any, binding: Any, bundle: Any, *, authority_ref: str, state_refs: tuple[str, ...] = ()) -> CognitionSession:
        """Adapt authoritative resident runtime/context records into F3 identity."""
        if getattr(binding, "status", "active") != "active":
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: active implementation binding is required.")
        if hasattr(runtime_session, "binding_id") and runtime_session.binding_id != binding.binding_id:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: runtime/binding identity mismatch.")
        if getattr(bundle, "stale", False):
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: authoritative context is stale.")
        if runtime_session.occupant_id != binding.occupant_id or runtime_session.office_id != bundle.office_id:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: runtime/binding/context identity mismatch.")
        if bundle.office_id is None:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: an occupied office is required.")
        return self.open(
            resident_id=bundle.resident_id, occupant_id=runtime_session.occupant_id,
            office_id=runtime_session.office_id, implementation_id=binding.implementation_id,
            authority_ref=authority_ref,
            state_refs=state_refs or tuple(getattr(bundle, "dependency_refs", ())),
        )

    def bind_request(self, session: CognitionSession, request: CapabilityResourceRequest, *, attached_at: datetime | None = None) -> CognitionSessionTurn:
        self._validate_session(session)
        for name in ("resident_id", "occupant_id", "office_id", "implementation_id", "authority_ref"):
            if getattr(request, name) != getattr(session, name):
                raise CognitionSessionError(f"{SESSION_CHECKPOINT}: {name} does not correspond to session.")
        turn = CognitionSessionTurn(
            session_id=session.session_id, request_id=request.request_id, correlation_id=request.correlation_id,
            resident_id=session.resident_id, occupant_id=session.occupant_id, office_id=session.office_id,
            implementation_id=session.implementation_id, authority_ref=session.authority_ref,
            attached_at=attached_at or datetime.now(UTC),
        )
        self._append("cognition.session.request_attached", session.session_id,
                     f"request-attached:{session.session_id}:{turn.request_id}", turn.as_payload(), turn.attached_at)
        return turn

    def replace_implementation(self, session: CognitionSession, implementation_id: UUID, *, state_refs: tuple[str, ...] | None = None) -> CognitionSession:
        """Record an implementation replacement while retaining Estate identity."""
        self._validate_session(session)
        _uuid(implementation_id, "implementation_id")
        replacement = CognitionSession(
            session_id=session.session_id, resident_id=session.resident_id, occupant_id=session.occupant_id,
            office_id=session.office_id, implementation_id=implementation_id,
            authority_ref=session.authority_ref, state_refs=state_refs if state_refs is not None else session.state_refs,
            opened_at=session.opened_at,
        )
        payload = replacement.as_payload() | {"previous_implementation_id": str(session.implementation_id)}
        self._append("cognition.session.implementation_replaced", session.session_id,
                     f"implementation-replaced:{session.session_id}:{implementation_id}", payload, datetime.now(UTC))
        return replacement

    def reconstruct(self, session_id: UUID) -> tuple[CognitionSession, tuple[CognitionSessionTurn, ...]]:
        _uuid(session_id, "session_id")
        if self.event_store is None:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: durable session store is unavailable.")
        rows = self.event_store.read_aggregate(SESSION_AGGREGATE_TYPE, session_id)
        opened = [row for row in rows if row.get("event_type") == "cognition.session.opened"]
        if len(opened) != 1:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: session opening lineage is invalid.")
        session = CognitionSession.from_payload(dict(opened[0]["payload"]))
        if session.session_id != session_id:
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: reconstructed session identity mismatch.")
        current = session
        turns: list[CognitionSessionTurn] = []
        for row in rows:
            event_type = row.get("event_type")
            if event_type == "cognition.session.request_attached":
                turn = CognitionSessionTurn.from_payload(dict(row["payload"]))
                self._validate_turn(current, turn)
                turns.append(turn)
            elif event_type == "cognition.session.implementation_replaced":
                current = CognitionSession.from_payload(dict(row["payload"]))
                if current.session_id != session_id or current.resident_id != session.resident_id or current.occupant_id != session.occupant_id or current.office_id != session.office_id or current.authority_ref != session.authority_ref:
                    raise CognitionSessionError(f"{SESSION_CHECKPOINT}: implementation transition changed resident identity.")
        return current, tuple(turns)

    def _validate_session(self, session: CognitionSession) -> None:
        if not isinstance(session, CognitionSession):
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: session envelope is required.")

    def _validate_turn(self, session: CognitionSession, turn: CognitionSessionTurn) -> None:
        for name in ("session_id", "resident_id", "occupant_id", "office_id", "implementation_id", "authority_ref"):
            if getattr(turn, name) != getattr(session, name):
                raise CognitionSessionError(f"{SESSION_CHECKPOINT}: turn {name} does not correspond to session.")

    def validate_turn(self, session: CognitionSession, turn: CognitionSessionTurn) -> None:
        """Validate an already materialized association before downstream use."""
        self._validate_session(session)
        if not isinstance(turn, CognitionSessionTurn):
            raise CognitionSessionError(f"{SESSION_CHECKPOINT}: turn envelope is required.")
        self._validate_turn(session, turn)

    def _append(self, event_type: str, session_id: UUID, key: str, payload: dict[str, Any], occurred_at: datetime) -> None:
        if self.event_store is not None:
            self.event_store.append(RiverEvent(
                event_type=event_type, aggregate_type=SESSION_AGGREGATE_TYPE, aggregate_id=session_id,
                idempotency_key=key, correlation_id=session_id, payload=payload,
                classification=Classification.INTERNAL, occurred_at=occurred_at,
            ))
