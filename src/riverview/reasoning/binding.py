"""Topology-neutral cognition capability binding and candidate selection.

This module maps the resident-facing F1 capability request to configured tier
bindings and measured provider candidates. It does not invoke providers,
select a model/GPU, reserve capacity, or grant execution authority.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from .cognition_contracts import CapabilityResourceRequest, CognitionTier

_MAX_CONFIG_TEXT = 500
_UNAVAILABLE = "unavailable"
_AVAILABLE = "available"
_FORBIDDEN_CONFIG_KEYS = frozenset({
    "gpu",
    "gpu_id",
    "model",
    "model_id",
    "model_ref",
    "endpoint",
    "host",
    "host_ref",
    "resident_id",
    "occupant_id",
    "office_id",
})


class CapabilityBindingError(ValueError):
    """Fail-closed configuration or candidate error."""


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > _MAX_CONFIG_TEXT:
        raise CapabilityBindingError(f"RIV-COG-P2-0001: {name} is missing or invalid.")
    return value.strip()


@dataclass(frozen=True, slots=True)
class TierBinding:
    """Configuration that maps a cognition tier to a named capability class."""

    cognition_tier: CognitionTier
    capability_name: str
    policy_ref: str
    configuration_ref: str
    resource_class_ref: str | None = None

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "cognition_tier", CognitionTier(self.cognition_tier))
        except (TypeError, ValueError) as exc:
            raise CapabilityBindingError("RIV-COG-P2-0001: cognition tier is unsupported.") from exc
        _text(self.capability_name, "capability_name")
        _text(self.policy_ref, "policy_ref")
        _text(self.configuration_ref, "configuration_ref")
        if self.resource_class_ref is not None:
            _text(self.resource_class_ref, "resource_class_ref")


@dataclass(frozen=True, slots=True)
class BindingConfiguration:
    """Immutable tier-binding projection; physical topology is out of scope."""

    bindings: tuple[TierBinding, ...]

    def __post_init__(self) -> None:
        if not self.bindings or len({item.cognition_tier for item in self.bindings}) != len(self.bindings):
            raise CapabilityBindingError("RIV-COG-P2-0001: tier bindings must be present and unique.")

    def for_tier(self, tier: CognitionTier) -> TierBinding | None:
        tier = CognitionTier(tier)
        return next((item for item in self.bindings if item.cognition_tier is tier), None)


class BindingConfigurationLoader:
    """Load a small provider-neutral tier configuration projection."""

    @staticmethod
    def from_mapping(value: Mapping[str, Mapping[str, object]]) -> BindingConfiguration:
        if not isinstance(value, Mapping) or not value:
            raise CapabilityBindingError("RIV-COG-P2-0001: binding configuration is required.")
        bindings: list[TierBinding] = []
        for tier_name, raw in value.items():
            if not isinstance(raw, Mapping):
                raise CapabilityBindingError("RIV-COG-P2-0001: tier binding configuration must be an object.")
            forbidden = _FORBIDDEN_CONFIG_KEYS.intersection(raw)
            if forbidden:
                raise CapabilityBindingError(
                    f"RIV-COG-P2-0001: physical or resident identity key is not allowed: {sorted(forbidden)[0]}"
                )
            bindings.append(
                TierBinding(
                    cognition_tier=CognitionTier(tier_name),
                    capability_name=raw.get("capability_name"),
                    policy_ref=raw.get("policy_ref"),
                    configuration_ref=raw.get("configuration_ref"),
                    resource_class_ref=raw.get("resource_class_ref"),
                )
            )
        return BindingConfiguration(tuple(bindings))


@dataclass(frozen=True, slots=True)
class ProviderResourceCandidate:
    """A measured provider candidate; it is not a reservation or assignment."""

    participant_id: str
    provider_id: str
    provider_type: str
    role: str
    capability_name: str
    health: str
    capacity: int
    contract_version: str
    configuration_ref: str
    resource_class_ref: str | None = None

    def __post_init__(self) -> None:
        for value, name in ((self.participant_id, "participant_id"), (self.provider_id, "provider_id"), (self.provider_type, "provider_type"), (self.role, "role"), (self.capability_name, "capability_name"), (self.health, "health"), (self.contract_version, "contract_version"), (self.configuration_ref, "configuration_ref")):
            _text(value, name)
        if self.health != "healthy" or not isinstance(self.capacity, int) or self.capacity < 1:
            raise CapabilityBindingError("RIV-COG-P2-0002: candidate health or capacity is not eligible.")
        if self.resource_class_ref is not None:
            _text(self.resource_class_ref, "resource_class_ref")

    def evidence_refs(self) -> tuple[str, ...]:
        refs = [f"provider:{self.provider_id}", f"capability:{self.capability_name}", f"binding:{self.configuration_ref}"]
        if self.resource_class_ref:
            refs.append(f"resource-class:{self.resource_class_ref}")
        return tuple(refs)


@dataclass(frozen=True, slots=True)
class CapabilityBindingDecision:
    request_id: UUID
    correlation_id: UUID
    cognition_tier: CognitionTier
    policy_ref: str
    status: str
    reason: str
    candidates: tuple[ProviderResourceCandidate, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {_AVAILABLE, _UNAVAILABLE} or not self.reason.strip():
            raise CapabilityBindingError("RIV-COG-P2-0003: binding decision is invalid.")
        if self.status == _UNAVAILABLE and self.candidates:
            raise CapabilityBindingError("RIV-COG-P2-0003: unavailable decision cannot contain candidates.")

    @property
    def selected(self) -> None:
        """P2 returns candidates only; it never selects or reserves one."""
        return None

    def as_payload(self) -> dict[str, Any]:
        return {
            "request_id": str(self.request_id),
            "correlation_id": str(self.correlation_id),
            "cognition_tier": self.cognition_tier.value,
            "policy_ref": self.policy_ref,
            "status": self.status,
            "reason": self.reason,
            "candidates": [
                {
                    "participant_id": candidate.participant_id,
                    "provider_id": candidate.provider_id,
                    "provider_type": candidate.provider_type,
                    "role": candidate.role,
                    "capability_name": candidate.capability_name,
                    "health": candidate.health,
                    "capacity": candidate.capacity,
                    "contract_version": candidate.contract_version,
                    "configuration_ref": candidate.configuration_ref,
                    "resource_class_ref": candidate.resource_class_ref,
                    "evidence_refs": list(candidate.evidence_refs()),
                }
                for candidate in self.candidates
            ],
        }


class ProviderCandidateCatalog(Protocol):
    def available_for(self, *, request_classification: str, required_capability: str, max_age_seconds: int = 300) -> Sequence[Mapping[str, object]]: ...


class CognitionBindingAdapter:
    """Filter measured candidates for one topology-neutral F1 request."""

    def __init__(self, catalog: ProviderCandidateCatalog, configuration: BindingConfiguration) -> None:
        self.catalog = catalog
        self.configuration = configuration

    def candidates(self, request: CapabilityResourceRequest, *, max_age_seconds: int = 300) -> CapabilityBindingDecision:
        if not isinstance(request, CapabilityResourceRequest):
            raise CapabilityBindingError("RIV-COG-P2-0004: a typed capability request is required.")
        if not 1 <= max_age_seconds <= 86_400:
            raise CapabilityBindingError("RIV-COG-P2-0004: health freshness bound is invalid.")
        binding = self.configuration.for_tier(request.cognition_tier)
        if binding is None:
            return self._unavailable(request, "no configured binding exists for the requested cognition tier")
        if request.required_capability != binding.capability_name or request.policy_ref != binding.policy_ref:
            return self._unavailable(request, "request capability or policy does not match the configured tier binding")
        rows = self.catalog.available_for(
            request_classification=request.classification,
            required_capability=binding.capability_name,
            max_age_seconds=max_age_seconds,
        )
        candidates = tuple(
            self._candidate(row, binding)
            for row in rows
            if self._eligible_row(row, request, binding)
        )
        if not candidates:
            return self._unavailable(request, "no healthy, fresh, classified candidate has measured capacity")
        return CapabilityBindingDecision(request.request_id, request.correlation_id, request.cognition_tier, binding.policy_ref, _AVAILABLE, "eligible candidates are available", candidates)

    @staticmethod
    def _eligible_row(row: Mapping[str, object], request: CapabilityResourceRequest, binding: TierBinding) -> bool:
        provider_id = row.get("provider_id")
        participant_id = row.get("participant_id")
        if not isinstance(provider_id, str) or not isinstance(participant_id, str):
            return False
        if provider_id in request.exclusions or participant_id in request.exclusions:
            return False
        eligible_classifications = row.get("eligible_classifications")
        if isinstance(eligible_classifications, (tuple, list, set, frozenset)) and request.classification not in eligible_classifications:
            return False
        if row.get("classification") is False:
            return False
        return (
            row.get("health") == "healthy"
            and isinstance(row.get("capacity"), int)
            and int(row["capacity"]) > 0
            and row.get("capability_name", binding.capability_name) == binding.capability_name
        )

    @staticmethod
    def _candidate(row: Mapping[str, object], binding: TierBinding) -> ProviderResourceCandidate:
        return ProviderResourceCandidate(
            participant_id=row.get("participant_id"),
            provider_id=row.get("provider_id"),
            provider_type=row.get("provider_type"),
            role=row.get("role", "advisory"),
            capability_name=binding.capability_name,
            health=row.get("health"),
            capacity=row.get("capacity"),
            contract_version=row.get("contract_version", "unknown"),
            configuration_ref=binding.configuration_ref,
            resource_class_ref=binding.resource_class_ref,
        )

    @staticmethod
    def _unavailable(request: CapabilityResourceRequest, reason: str) -> CapabilityBindingDecision:
        return CapabilityBindingDecision(request.request_id, request.correlation_id, request.cognition_tier, request.policy_ref, _UNAVAILABLE, reason)
