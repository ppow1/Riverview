"""Minimum shared-resident capacity reservation seam for GRC-003-P3.

This adapter reserves one measured capacity unit from an accepted P2 candidate.
It records bounded ownership and lease metadata, but does not dispatch,
invoke, select a provider, or grant execution authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from threading import RLock
from typing import Any
from uuid import UUID, uuid4

from .binding import CapabilityBindingDecision, ProviderResourceCandidate
from .cognition_contracts import CapabilityResourceRequest, CognitionTier


RESERVATION_CHECKPOINT = "RIV-COG-P3-0001"
MAX_LEASE_SECONDS = 3_600
MAX_PRIORITY = 100


class ReservationError(ValueError):
    """A reservation input, identity, capacity, or lifecycle operation is invalid."""


class ReservationState(StrEnum):
    HELD = "held_for_capacity"
    RELEASED = "released"
    EXPIRED = "expired"


def _text(value: object, name: str, limit: int = 200) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ReservationError(f"{RESERVATION_CHECKPOINT}: {name} is invalid.")
    return value.strip()


@dataclass(frozen=True, slots=True)
class ResidentCognitionReservation:
    """One bounded unit held for one exact resident cognition request."""

    reservation_id: UUID
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    cognition_tier: CognitionTier
    request_id: UUID
    correlation_id: UUID
    binding_ref: str
    resource_participant_id: str
    resource_provider_id: str
    priority: int
    fairness_class: str
    capacity_units: int
    lease_expires_at: datetime
    state: ReservationState = ReservationState.HELD
    release_reason: str | None = None
    sequence: int = 0

    def __post_init__(self) -> None:
        for value, name in (
            (self.reservation_id, "reservation_id"),
            (self.resident_id, "resident_id"),
            (self.occupant_id, "occupant_id"),
            (self.office_id, "office_id"),
            (self.request_id, "request_id"),
            (self.correlation_id, "correlation_id"),
        ):
            if not isinstance(value, UUID):
                raise ReservationError(f"{RESERVATION_CHECKPOINT}: {name} must be a UUID.")
        object.__setattr__(self, "cognition_tier", CognitionTier(self.cognition_tier))
        object.__setattr__(self, "state", ReservationState(self.state))
        _text(self.binding_ref, "binding_ref")
        _text(self.resource_participant_id, "resource_participant_id")
        _text(self.resource_provider_id, "resource_provider_id")
        _text(self.fairness_class, "fairness_class")
        if not isinstance(self.priority, int) or not 0 <= self.priority <= MAX_PRIORITY:
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: priority is invalid.")
        if self.capacity_units != 1:
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: exactly one capacity unit is reserved per request.")
        if self.lease_expires_at.tzinfo is None or self.lease_expires_at.utcoffset() is None:
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: lease deadline must be timezone-aware.")
        if self.release_reason is not None:
            _text(self.release_reason, "release_reason", 500)

    def as_payload(self) -> dict[str, Any]:
        return {
            "reservation_id": str(self.reservation_id),
            "resident_id": str(self.resident_id),
            "occupant_id": str(self.occupant_id),
            "office_id": str(self.office_id),
            "cognition_tier": self.cognition_tier.value,
            "request_id": str(self.request_id),
            "correlation_id": str(self.correlation_id),
            "binding_ref": self.binding_ref,
            "resource_participant_id": self.resource_participant_id,
            "resource_provider_id": self.resource_provider_id,
            "priority": self.priority,
            "fairness_class": self.fairness_class,
            "capacity_units": self.capacity_units,
            "lease_expires_at": self.lease_expires_at.isoformat(),
            "state": self.state.value,
            "release_reason": self.release_reason,
            "sequence": self.sequence,
        }


@dataclass(frozen=True, slots=True)
class CapacitySnapshot:
    resource_participant_id: str
    total_units: int
    held_units: int
    available_units: int


class ResidentCognitionReservationAdapter:
    """Thread-safe bounded reservation seam over measured P2 candidates.

    Reservation state is intentionally ephemeral in P3. The adapter exposes
    readback, release, and expiry recovery; durable provider/capacity facts
    remain owned by the existing registry and later scheduler packages.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._reservations: dict[UUID, ResidentCognitionReservation] = {}
        self._idempotency: dict[str, tuple[UUID, tuple[object, ...]]] = {}
        self._sequence = 0

    def reserve(
        self,
        request: CapabilityResourceRequest,
        binding: CapabilityBindingDecision,
        candidate: ProviderResourceCandidate,
        *,
        priority: int,
        fairness_class: str,
        idempotency_key: str,
        lease_seconds: int = 120,
        now: datetime | None = None,
    ) -> ResidentCognitionReservation:
        self._validate_inputs(request, binding, candidate, priority, fairness_class, idempotency_key, lease_seconds)
        created = now or datetime.now(UTC)
        if created.tzinfo is None or created.utcoffset() is None:
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: reservation time must be timezone-aware.")
        deadline = created + timedelta(seconds=lease_seconds)
        if request.deadline_at is not None:
            deadline = min(deadline, request.deadline_at)
        if deadline <= created:
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: request deadline leaves no reservation interval.")
        signature = (
            request.request_id, request.resident_id, request.occupant_id,
            request.office_id, request.implementation_id, request.correlation_id,
            candidate.participant_id, candidate.provider_id,
                binding.policy_ref, candidate.configuration_ref, priority,
                fairness_class, lease_seconds,
        )
        with self._lock:
            prior = self._idempotency.get(idempotency_key)
            if prior is not None:
                reservation_id, prior_signature = prior
                if prior_signature != signature:
                    raise ReservationError(f"{RESERVATION_CHECKPOINT}: idempotency key conflicts with an existing reservation.")
                return self._reservations[reservation_id]
            self.expire(now=created)
            held = sum(
                item.capacity_units
                for item in self._reservations.values()
                if item.state is ReservationState.HELD
                and item.resource_participant_id == candidate.participant_id
            )
            if held + 1 > candidate.capacity:
                raise ReservationError(f"{RESERVATION_CHECKPOINT}: measured capacity is exhausted.")
            self._sequence += 1
            reservation = ResidentCognitionReservation(
                reservation_id=uuid4(), resident_id=request.resident_id,
                occupant_id=request.occupant_id, office_id=request.office_id,
                cognition_tier=request.cognition_tier, request_id=request.request_id,
                correlation_id=request.correlation_id, binding_ref=candidate.configuration_ref,
                resource_participant_id=candidate.participant_id,
                resource_provider_id=candidate.provider_id, priority=priority,
                fairness_class=fairness_class, capacity_units=1,
                lease_expires_at=deadline, sequence=self._sequence,
            )
            self._reservations[reservation.reservation_id] = reservation
            self._idempotency[idempotency_key] = (reservation.reservation_id, signature)
            return reservation

    def release(
        self,
        reservation_id: UUID,
        *,
        request_id: UUID,
        resident_id: UUID,
        occupant_id: UUID,
        office_id: UUID,
        reason: str,
    ) -> ResidentCognitionReservation:
        reason = _text(reason, "release_reason", 500)
        with self._lock:
            reservation = self._reservations.get(reservation_id)
            if reservation is None:
                raise ReservationError(f"{RESERVATION_CHECKPOINT}: reservation is unknown.")
            if (
                reservation.request_id != request_id
                or reservation.resident_id != resident_id
                or reservation.occupant_id != occupant_id
                or reservation.office_id != office_id
            ):
                raise ReservationError(f"{RESERVATION_CHECKPOINT}: reservation ownership does not correspond.")
            if reservation.state is not ReservationState.HELD:
                return reservation
            updated = self._replace(reservation, state=ReservationState.RELEASED, release_reason=reason)
            self._reservations[reservation_id] = updated
            return updated

    def expire(self, *, now: datetime | None = None) -> tuple[ResidentCognitionReservation, ...]:
        current = now or datetime.now(UTC)
        if current.tzinfo is None or current.utcoffset() is None:
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: expiry time must be timezone-aware.")
        expired: list[ResidentCognitionReservation] = []
        with self._lock:
            for reservation in tuple(self._reservations.values()):
                if reservation.state is ReservationState.HELD and reservation.lease_expires_at <= current:
                    updated = self._replace(reservation, state=ReservationState.EXPIRED, release_reason="lease_expired")
                    self._reservations[reservation.reservation_id] = updated
                    expired.append(updated)
        return tuple(expired)

    def read(self, reservation_id: UUID) -> ResidentCognitionReservation:
        with self._lock:
            try:
                return self._reservations[reservation_id]
            except KeyError as exc:
                raise ReservationError(f"{RESERVATION_CHECKPOINT}: reservation is unknown.") from exc

    def snapshot(self, resource_participant_id: str) -> tuple[ResidentCognitionReservation, ...]:
        resource_participant_id = _text(resource_participant_id, "resource_participant_id")
        with self._lock:
            return tuple(sorted(
                (item for item in self._reservations.values()
                 if item.resource_participant_id == resource_participant_id
                 and item.state is ReservationState.HELD),
                key=lambda item: (-item.priority, item.sequence),
            ))

    def capacity(self, candidate: ProviderResourceCandidate) -> CapacitySnapshot:
        held = sum(item.capacity_units for item in self.snapshot(candidate.participant_id))
        return CapacitySnapshot(candidate.participant_id, candidate.capacity, held, max(candidate.capacity - held, 0))

    @staticmethod
    def _replace(reservation: ResidentCognitionReservation, **changes: object) -> ResidentCognitionReservation:
        values = {field: getattr(reservation, field) for field in reservation.__dataclass_fields__}
        values.update(changes)
        return ResidentCognitionReservation(**values)

    @staticmethod
    def _validate_inputs(
        request: CapabilityResourceRequest,
        binding: CapabilityBindingDecision,
        candidate: ProviderResourceCandidate,
        priority: int,
        fairness_class: str,
        idempotency_key: str,
        lease_seconds: int,
    ) -> None:
        if not isinstance(request, CapabilityResourceRequest):
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: typed capability request is required.")
        if not isinstance(binding, CapabilityBindingDecision) or binding.status != "available":
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: an available P2 binding decision is required.")
        if (
            binding.request_id != request.request_id
            or binding.correlation_id != request.correlation_id
            or binding.policy_ref != request.policy_ref
        ):
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: binding does not correspond to the request.")
        if not isinstance(candidate, ProviderResourceCandidate) or candidate not in binding.candidates:
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: resource candidate is not part of the binding decision.")
        if candidate.capability_name != request.required_capability:
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: resource capability does not match the request.")
        if not isinstance(priority, int) or not 0 <= priority <= MAX_PRIORITY:
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: priority is invalid.")
        _text(fairness_class, "fairness_class")
        _text(idempotency_key, "idempotency_key", 500)
        if not isinstance(lease_seconds, int) or not 1 <= lease_seconds <= MAX_LEASE_SECONDS:
            raise ReservationError(f"{RESERVATION_CHECKPOINT}: lease duration is outside its bound.")
