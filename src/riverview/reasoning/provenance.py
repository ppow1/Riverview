"""GRC-003-F2 cognition provenance and River lineage contracts.

Version: 1.0.0 | Package: GRC-006

This module records cognition lineage as immutable River facts. It does not
select providers, invoke models, grant authority, or execute results.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID, uuid4

from riverview.river import Classification, RiverEvent

from .cognition_contracts import (
    ALLOWED_CLASSIFICATIONS,
    CognitionActorClass,
    CognitionFailureCode,
    CognitionResult,
    CognitionResultStatus,
    CognitionTier,
    CapabilityResourceRequest,
    ResidentReasoningPacket,
)

PROVENANCE_SCHEMA_VERSION = "cognition-provenance-f2-v1"
PROVENANCE_AGGREGATE_TYPE = "cognition_request"
PROVENANCE_CHECKPOINT = "RIV-COG-PROV-0001"
_ADVISORY_AUTHORITY = frozenset({"read:bounded", "return:advisory", "return:diagnostic"})


class CognitionProvenanceEventType(StrEnum):
    REQUESTED = "cognition.requested"
    ADMITTED = "cognition.admitted"
    HELD = "cognition.held"
    STARTED = "cognition.started"
    COMPLETED = "cognition.completed"
    UNAVAILABLE = "cognition.unavailable"
    REJECTED = "cognition.rejected"
    TIMED_OUT = "cognition.timed_out"
    INTEGRATED = "cognition.integrated"


class ProvenanceLineageError(ValueError):
    """Fail-closed provenance validation or reconstruction error."""


def _uuid(value: Any, name: str) -> None:
    if not isinstance(value, UUID):
        raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: {name} must be a UUID.")


def _optional_uuid(value: Any, name: str) -> None:
    if value is not None:
        _uuid(value, name)


def _text(value: Any, name: str, limit: int = 500) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: {name} is invalid or unbounded.")


def _refs(values: Any, name: str, limit: int = 64) -> None:
    if not isinstance(values, tuple) or len(values) > limit:
        raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: {name} exceeds its bound.")
    if not all(isinstance(value, str) and value.strip() and len(value) <= 500 for value in values):
        raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: {name} contains an invalid reference.")


def _aware(value: Any, name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: {name} must be timezone-aware.")


def _enum(value: Any, enum_type: type[StrEnum], name: str) -> StrEnum:
    try:
        return value if isinstance(value, enum_type) else enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: {name} is unsupported.") from exc


def _river_classification(value: str) -> Classification:
    return Classification.INTERNAL if value == "internal" else Classification.RIVER


@dataclass(frozen=True, slots=True)
class CognitionProvenance:
    """Versioned bounded provenance payload for one immutable River fact."""

    event_id: UUID
    event_type: CognitionProvenanceEventType
    actor_class: CognitionActorClass
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    authority_ref: str
    source_event_id: UUID
    request_id: UUID
    correlation_id: UUID
    causation_id: UUID | None
    cognition_tier: CognitionTier | None
    provider_ref: str | None
    resource_class_ref: str | None
    packet_id: UUID | None
    result_id: UUID | None
    policy_decision_ref: str | None
    status: str
    failure_code: CognitionFailureCode | None
    classification: str
    live_generation: bool
    evidence_refs: tuple[str, ...]
    authoritative_state_refs: tuple[str, ...]
    occurred_at: datetime
    result_reference: str | None = None
    schema_version: str = PROVENANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value, name in (
            (self.event_id, "event_id"), (self.resident_id, "resident_id"),
            (self.occupant_id, "occupant_id"), (self.office_id, "office_id"),
            (self.implementation_id, "implementation_id"), (self.source_event_id, "source_event_id"),
            (self.request_id, "request_id"), (self.correlation_id, "correlation_id"),
        ):
            _uuid(value, name)
        _optional_uuid(self.causation_id, "causation_id")
        _optional_uuid(self.packet_id, "packet_id")
        _optional_uuid(self.result_id, "result_id")
        object.__setattr__(self, "event_type", _enum(self.event_type, CognitionProvenanceEventType, "event_type"))
        object.__setattr__(self, "actor_class", _enum(self.actor_class, CognitionActorClass, "actor_class"))
        if self.cognition_tier is not None:
            object.__setattr__(self, "cognition_tier", _enum(self.cognition_tier, CognitionTier, "cognition_tier"))
        object.__setattr__(self, "failure_code", _enum(self.failure_code, CognitionFailureCode, "failure_code") if self.failure_code is not None else None)
        _text(self.authority_ref, "authority_ref")
        _text(self.status, "status", 100)
        if self.provider_ref is not None:
            _text(self.provider_ref, "provider_ref")
        if self.resource_class_ref is not None:
            _text(self.resource_class_ref, "resource_class_ref")
        if self.policy_decision_ref is not None:
            _text(self.policy_decision_ref, "policy_decision_ref")
        if self.result_reference is not None:
            _text(self.result_reference, "result_reference")
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: classification is not eligible.")
        if not isinstance(self.live_generation, bool):
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: live_generation must be boolean.")
        _refs(self.evidence_refs, "evidence_refs")
        _refs(self.authoritative_state_refs, "authoritative_state_refs")
        _aware(self.occurred_at, "occurred_at")
        _text(self.schema_version, "schema_version", 100)
        if self.actor_class == CognitionActorClass.DETERMINISTIC_SUBSTRATE and self.live_generation:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: deterministic event cannot claim live generation.")
        cognition_actors = {
            CognitionActorClass.GRACE_HOME_COGNITION,
            CognitionActorClass.GRACE_HIGH_REASONING,
            CognitionActorClass.EXTERNAL_REASONING,
        }
        if self.live_generation and self.actor_class not in cognition_actors:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: non-cognition actor cannot claim live generation.")
        if self.actor_class == CognitionActorClass.GRACE_HOME_COGNITION:
            if self.cognition_tier != CognitionTier.HOME_COGNITION:
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: home actor/tier mismatch.")
        if self.actor_class == CognitionActorClass.GRACE_HIGH_REASONING:
            if self.cognition_tier != CognitionTier.HIGH_REASONING:
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: high actor/tier mismatch.")
        if self.actor_class == CognitionActorClass.EXTERNAL_REASONING:
            if self.cognition_tier != CognitionTier.EXTERNAL_ESCALATION:
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: external actor/tier mismatch.")
        if self.live_generation and (self.provider_ref is None or self.resource_class_ref is None):
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: live cognition requires observed provider/resource references.")
        if self.event_type in {CognitionProvenanceEventType.COMPLETED, CognitionProvenanceEventType.INTEGRATED} and self.result_id is None:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: result event requires result_id.")
        if self.event_type in {CognitionProvenanceEventType.STARTED, CognitionProvenanceEventType.COMPLETED, CognitionProvenanceEventType.INTEGRATED} and self.packet_id is None:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: active cognition event requires packet_id.")
        if self.event_type in {CognitionProvenanceEventType.UNAVAILABLE, CognitionProvenanceEventType.REJECTED, CognitionProvenanceEventType.TIMED_OUT} and self.failure_code is None:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: failure event requires failure_code.")
        if self.actor_class in cognition_actors and not self.live_generation and self.event_type in {CognitionProvenanceEventType.COMPLETED, CognitionProvenanceEventType.INTEGRATED}:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: Grace/external result event requires live generation truth.")

    @classmethod
    def for_request(
        cls,
        request: CapabilityResourceRequest,
        *,
        source_event_id: UUID,
        office_id: UUID,
        implementation_id: UUID,
        authority_ref: str,
        authoritative_state_refs: tuple[str, ...] = (),
        evidence_refs: tuple[str, ...] = (),
        causation_id: UUID | None = None,
        event_id: UUID | None = None,
        occurred_at: datetime | None = None,
    ) -> "CognitionProvenance":
        if office_id != request.office_id:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: office_id does not match the request.")
        if implementation_id != request.implementation_id:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: implementation_id does not match the request.")
        if authority_ref != request.authority_ref:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: authority_ref does not match the request.")
        return cls(
            event_id=event_id or uuid4(), event_type=CognitionProvenanceEventType.REQUESTED,
            actor_class=CognitionActorClass.DETERMINISTIC_SUBSTRATE,
            resident_id=request.resident_id, occupant_id=request.occupant_id,
            office_id=office_id, implementation_id=implementation_id,
            authority_ref=authority_ref, source_event_id=source_event_id,
            request_id=request.request_id, correlation_id=request.correlation_id,
            causation_id=causation_id, cognition_tier=request.cognition_tier,
            provider_ref=None, resource_class_ref=None, packet_id=None, result_id=None,
            policy_decision_ref=request.policy_ref, status="requested", failure_code=None,
            classification=request.classification, live_generation=False,
            evidence_refs=evidence_refs, authoritative_state_refs=authoritative_state_refs,
            occurred_at=occurred_at or datetime.now(UTC),
        )

    @classmethod
    def for_result(
        cls,
        result: CognitionResult,
        *,
        source_event_id: UUID,
        event_type: CognitionProvenanceEventType | None = None,
        causation_id: UUID | None = None,
        event_id: UUID | None = None,
        occurred_at: datetime | None = None,
        authoritative_state_refs: tuple[str, ...] = (),
    ) -> "CognitionProvenance":
        selected_event = event_type or {
            CognitionResultStatus.COMPLETED: CognitionProvenanceEventType.COMPLETED,
            CognitionResultStatus.TIMEOUT: CognitionProvenanceEventType.TIMED_OUT,
            CognitionResultStatus.UNAVAILABLE: CognitionProvenanceEventType.UNAVAILABLE,
        }.get(result.status, CognitionProvenanceEventType.REJECTED)
        return cls(
            event_id=event_id or uuid4(), event_type=selected_event,
            actor_class=result.actor_class, resident_id=result.resident_id,
            occupant_id=result.occupant_id, office_id=result.office_id,
            implementation_id=result.implementation_id, authority_ref=result.authority_ref,
            source_event_id=source_event_id, request_id=result.request_id,
            correlation_id=result.correlation_id, causation_id=causation_id,
            cognition_tier=result.cognition_tier, provider_ref=result.provider_ref,
            resource_class_ref=result.resource_class_ref, packet_id=result.packet_id,
            result_id=result.result_id, policy_decision_ref=result.policy_decision_ref,
            status=result.status.value, failure_code=result.failure_code,
            classification=result.classification, live_generation=result.live_generation,
            evidence_refs=result.provenance_refs, authoritative_state_refs=authoritative_state_refs,
            occurred_at=occurred_at or result.created_at, result_reference=str(result.result_id),
        )

    def validate_against_request(
        self,
        request: CapabilityResourceRequest | ResidentReasoningPacket | "CognitionProvenance",
    ) -> None:
        if isinstance(request, CognitionProvenance):
            # A stored request is the durable authority for downstream lineage.
            # Provider/resource, result, status, failure, and live-generation
            # fields are intentionally not compared: those are result facts.
            for name in (
                "request_id", "correlation_id", "resident_id", "occupant_id",
                "office_id", "implementation_id", "authority_ref", "source_event_id",
                "cognition_tier", "classification",
            ):
                if getattr(self, name) != getattr(request, name):
                    raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: {name} correspondence mismatch.")
            if request.packet_id is not None and self.packet_id != request.packet_id:
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: packet correspondence mismatch.")
            return
        for name in ("request_id", "correlation_id", "resident_id", "occupant_id", "cognition_tier", "classification"):
            expected_name = "packet_id" if name == "request_id" and hasattr(request, "packet_id") else name
            if expected_name == "packet_id":
                if self.packet_id != request.packet_id:
                    raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: packet correspondence mismatch.")
                continue
            expected = getattr(request, name)
            actual = getattr(self, name)
            if actual != expected:
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: {name} correspondence mismatch.")
        for name in ("office_id", "implementation_id", "authority_ref"):
            if hasattr(request, name) and getattr(self, name) != getattr(request, name):
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: {name} correspondence mismatch.")
        if hasattr(request, "source_cognition_event_id") and self.source_event_id != request.source_cognition_event_id:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: source event correspondence mismatch.")

    def as_typed_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "event_id": str(self.event_id),
            "event_type": self.event_type.value, "actor_class": self.actor_class.value,
            "resident_id": str(self.resident_id), "occupant_id": str(self.occupant_id),
            "office_id": str(self.office_id), "implementation_id": str(self.implementation_id),
            "authority_ref": self.authority_ref, "source_event_id": str(self.source_event_id),
            "request_id": str(self.request_id), "correlation_id": str(self.correlation_id),
            "causation_id": str(self.causation_id) if self.causation_id else None,
            "cognition_tier": self.cognition_tier.value if self.cognition_tier else None,
            "provider_ref": self.provider_ref, "resource_class_ref": self.resource_class_ref,
            "packet_id": str(self.packet_id) if self.packet_id else None,
            "result_id": str(self.result_id) if self.result_id else None,
            "policy_decision_ref": self.policy_decision_ref, "status": self.status,
            "failure_code": self.failure_code.value if self.failure_code else None,
            "classification": self.classification, "live_generation": self.live_generation,
            "evidence_refs": list(self.evidence_refs),
            "authoritative_state_refs": list(self.authoritative_state_refs),
            "occurred_at": self.occurred_at.isoformat(), "result_reference": self.result_reference,
        }

    @classmethod
    def from_typed_payload(cls, payload: Mapping[str, Any]) -> "CognitionProvenance":
        if not isinstance(payload, Mapping) or payload.get("schema_version") != PROVENANCE_SCHEMA_VERSION:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: provenance schema is unsupported.")
        def uid(name: str) -> UUID:
            try:
                return UUID(str(payload[name]))
            except (KeyError, TypeError, ValueError) as exc:
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: {name} is invalid.") from exc
        def optional_uid(name: str) -> UUID | None:
            return None if payload.get(name) is None else uid(name)
        try:
            occurred_at = datetime.fromisoformat(str(payload["occurred_at"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: occurred_at is invalid.") from exc
        refs = lambda name: tuple(payload.get(name, ())) if isinstance(payload.get(name, ()), (list, tuple)) else payload.get(name)
        return cls(
            event_id=uid("event_id"), event_type=payload["event_type"], actor_class=payload["actor_class"],
            resident_id=uid("resident_id"), occupant_id=uid("occupant_id"), office_id=uid("office_id"),
            implementation_id=uid("implementation_id"), authority_ref=payload["authority_ref"],
            source_event_id=uid("source_event_id"), request_id=uid("request_id"), correlation_id=uid("correlation_id"),
            causation_id=optional_uid("causation_id"), cognition_tier=payload.get("cognition_tier"),
            provider_ref=payload.get("provider_ref"), resource_class_ref=payload.get("resource_class_ref"),
            packet_id=optional_uid("packet_id"), result_id=optional_uid("result_id"),
            policy_decision_ref=payload.get("policy_decision_ref"), status=payload["status"],
            failure_code=payload.get("failure_code"), classification=payload["classification"],
            live_generation=payload["live_generation"], evidence_refs=refs("evidence_refs"),
            authoritative_state_refs=refs("authoritative_state_refs"), occurred_at=occurred_at,
            result_reference=payload.get("result_reference"), schema_version=payload["schema_version"],
        )

    def to_river_event(self) -> RiverEvent:
        return RiverEvent(
            event_id=self.event_id, event_type=self.event_type.value,
            aggregate_type=PROVENANCE_AGGREGATE_TYPE, aggregate_id=self.request_id,
            idempotency_key=f"cognition:{self.request_id}:{self.event_id}",
            payload=self.as_typed_payload(), correlation_id=self.correlation_id,
            causation_id=self.causation_id, classification=_river_classification(self.classification),
            occurred_at=self.occurred_at,
        )


class CognitionEventStore(Protocol):
    def append(self, event: RiverEvent) -> Any: ...

    def read_aggregate(self, aggregate_type: str, aggregate_id: UUID) -> list[dict[str, Any]]: ...


class CognitionProvenanceWriter:
    """Append and reconstruct F2 provenance through the existing EventStore."""

    def __init__(self, event_store: CognitionEventStore) -> None:
        self.event_store = event_store

    def record(self, provenance: CognitionProvenance) -> Any:
        event = provenance.to_river_event()
        if provenance.event_type != CognitionProvenanceEventType.REQUESTED:
            prior = self.event_store.read_aggregate(PROVENANCE_AGGREGATE_TYPE, provenance.request_id)
            request_rows = [
                row for row in prior
                if (
                    row.get("event_type") == CognitionProvenanceEventType.REQUESTED.value
                    or row.get("payload", {}).get("event_type") == CognitionProvenanceEventType.REQUESTED.value
                )
            ]
            if not request_rows:
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: cognition event has no recorded request lineage.")
            if len(request_rows) != 1:
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: stored request lineage is ambiguous.")
            try:
                canonical_request = CognitionProvenance.from_typed_payload(request_rows[0]["payload"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ProvenanceLineageError(
                    f"{PROVENANCE_CHECKPOINT}: stored request lineage is malformed."
                ) from exc
            if canonical_request.event_type is not CognitionProvenanceEventType.REQUESTED:
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: stored request lineage is invalid.")
            provenance.validate_against_request(canonical_request)
        acknowledgement = self.event_store.append(event)
        if getattr(acknowledgement, "inserted", True) is False:
            existing = self.event_store.read_aggregate(PROVENANCE_AGGREGATE_TYPE, provenance.request_id)
            matching = next((row for row in existing if row.get("payload", {}).get("event_id") == str(provenance.event_id)), None)
            if matching is None or matching.get("payload") != provenance.as_typed_payload():
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: duplicate event has conflicting payload.")
        return acknowledgement

    def reconstruct(self, request_id: UUID) -> tuple[CognitionProvenance, ...]:
        _uuid(request_id, "request_id")
        rows = self.event_store.read_aggregate(PROVENANCE_AGGREGATE_TYPE, request_id)
        records = tuple(CognitionProvenance.from_typed_payload(row["payload"]) for row in rows)
        for record in records:
            if record.request_id != request_id:
                raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: aggregate contains another request.")
        if records:
            first = records[0]
            for record in records[1:]:
                if (record.correlation_id, record.resident_id, record.occupant_id, record.office_id) != (first.correlation_id, first.resident_id, first.occupant_id, first.office_id):
                    raise ProvenanceLineageError(f"{PROVENANCE_CHECKPOINT}: lineage identity/correlation mismatch.")
        return records
