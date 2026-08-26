"""Dynamic, read-only execution-resource and Codex-fuel projections.

The Estate's Codex telemetry remains authoritative for observed weekly fuel and
reset windows. This module adapts that evidence for bounded Riverview selection;
it does not own credentials, authentication, seat count, or lifecycle state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_CODEX_TELEMETRY = Path(r"A:\theestate\runtime\engineering_capacity\codex_seat_telemetry.json")


def _timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class ExecutionResource:
    resource_id: str
    provider_id: str
    model: str | None
    capabilities: tuple[str, ...]
    classification_eligibility: tuple[str, ...]
    local: bool
    health: str
    available: bool
    observed_capacity: float | None
    observed_at: datetime | None
    reset_at: datetime | None
    workload: float
    roles: tuple[str, ...]
    independence_group: str | None = None
    independent_validation_only: bool = False

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ExecutionResource":
        resource_id = str(value.get("resource_id") or "").strip()
        provider_id = str(value.get("provider_id") or "").strip()
        if not resource_id or not provider_id:
            raise ValueError("RIV-RES-0001: resource and provider identities are required.")
        observed = value.get("observed_capacity")
        if observed is not None and (not isinstance(observed, (int, float)) or isinstance(observed, bool) or not 0 <= observed <= 100):
            raise ValueError("RIV-RES-0001: observed capacity is invalid.")
        workload = value.get("workload", 0)
        if not isinstance(workload, (int, float)) or isinstance(workload, bool) or workload < 0:
            raise ValueError("RIV-RES-0001: workload is invalid.")
        return cls(
            resource_id=resource_id,
            provider_id=provider_id,
            model=str(value["model"]).strip() if value.get("model") else None,
            capabilities=tuple(str(item) for item in value.get("capabilities", ()) if str(item).strip()),
            classification_eligibility=tuple(str(item) for item in value.get("classification_eligibility", ()) if str(item).strip()),
            local=bool(value.get("local", False)),
            health=str(value.get("health", "unknown")),
            available=bool(value.get("available", False)),
            observed_capacity=float(observed) if observed is not None else None,
            observed_at=_timestamp(value.get("observed_at")),
            reset_at=_timestamp(value.get("reset_at")),
            workload=float(workload),
            roles=tuple(str(item) for item in value.get("roles", ()) if str(item).strip()),
            independence_group=str(value["independence_group"]).strip() if value.get("independence_group") else None,
            independent_validation_only=bool(value.get("independent_validation_only", False)),
        )


@dataclass(frozen=True, slots=True)
class ResourceSelection:
    resource: ExecutionResource | None
    reason: str
    candidates_considered: tuple[str, ...] = ()


class ResourceSelectionError(RuntimeError):
    """The selected resource changed before the execution boundary."""


class ResourceRegistry:
    def __init__(self, resources: tuple[ExecutionResource, ...]) -> None:
        identities = [item.resource_id for item in resources]
        if len(identities) != len(set(identities)):
            raise ValueError("RIV-RES-0002: resource identities must be unique.")
        self.resources = resources

    @classmethod
    def from_mappings(cls, values: list[dict[str, Any]]) -> "ResourceRegistry":
        return cls(tuple(ExecutionResource.from_mapping(value) for value in values))

    @classmethod
    def from_codex_telemetry(cls, path: str | Path = DEFAULT_CODEX_TELEMETRY) -> "ResourceRegistry":
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("RIV-RES-0003: Codex fuel telemetry is unavailable.") from exc
        seats = payload.get("seats") if isinstance(payload, dict) else None
        if not isinstance(seats, list):
            raise RuntimeError("RIV-RES-0003: Codex fuel telemetry has no seat collection.")
        resources: list[dict[str, Any]] = []
        for seat in seats:
            if not isinstance(seat, dict) or not seat.get("seat_id"):
                continue
            resources.append({
                "resource_id": seat.get("capacity_identity") or f"codex.seat.{seat['seat_id']}",
                "provider_id": "codex-cli",
                "model": "codex-managed",
                "capabilities": ["bounded-engineering"],
                "classification_eligibility": ["river", "internal"],
                "local": False,
                "health": "healthy" if seat.get("collection_status") == "available" else "unknown",
                "available": seat.get("collection_status") == "available",
                "observed_capacity": seat.get("weekly_limit_percent_left"),
                "observed_at": seat.get("observed_at"),
                "reset_at": seat.get("weekly_limit_reset_at"),
                "workload": 0,
                "roles": ["writer", "validator", "repair_writer", "revalidator"],
                "independence_group": seat.get("seat_id"),
            })
        return cls.from_mappings(resources)

    def select(
        self,
        *,
        required_capability: str,
        classification: str,
        role: str,
        now: datetime | None = None,
        freshness: timedelta = timedelta(minutes=30),
    ) -> ResourceSelection:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        candidates: list[ExecutionResource] = []
        rejected_independent = False
        for resource in self.resources:
            if required_capability not in resource.capabilities or classification not in resource.classification_eligibility:
                continue
            if role not in resource.roles or resource.health != "healthy" or not resource.available:
                continue
            if resource.independent_validation_only and role not in {"validator", "revalidator"}:
                rejected_independent = True
                continue
            if resource.observed_at is None or current - resource.observed_at > freshness:
                continue
            candidates.append(resource)
        if not candidates:
            if rejected_independent:
                return ResourceSelection(None, "no eligible resource: only independent-validation capacity remains reserved", ())
            return ResourceSelection(None, "no eligible resource with healthy, available, fresh capacity", ())
        selected = max(
            candidates,
            key=lambda resource: (
                resource.observed_capacity is not None,
                resource.observed_capacity if resource.observed_capacity is not None else -1,
                -resource.workload,
                resource.resource_id,
            ),
        )
        fuel = "unknown" if selected.observed_capacity is None else f"{selected.observed_capacity:g}"
        reset = selected.reset_at.isoformat() if selected.reset_at else "unknown"
        reason = (
            f"selected {selected.resource_id}: weekly fuel {fuel}, reset {reset}, "
            f"fresh observation, workload {selected.workload:g}; capacity evidence preferred over round-robin"
        )
        return ResourceSelection(selected, reason, tuple(item.resource_id for item in candidates))

    def assert_current(
        self,
        selection: ResourceSelection,
        *,
        now: datetime | None = None,
        freshness: timedelta = timedelta(minutes=30),
    ) -> None:
        """Fail closed when the selected resource no longer matches evidence."""
        if selection.resource is None:
            raise ResourceSelectionError("no resource was selected")
        current = next((item for item in self.resources if item.resource_id == selection.resource.resource_id), None)
        if current is None or current != selection.resource:
            raise ResourceSelectionError("selected resource changed before execution")
        instant = (now or datetime.now(UTC)).astimezone(UTC)
        if not current.available or current.health != "healthy" or current.observed_at is None or instant - current.observed_at > freshness:
            raise ResourceSelectionError("selected resource changed or became stale before execution")


__all__ = ["DEFAULT_CODEX_TELEMETRY", "ExecutionResource", "ResourceRegistry", "ResourceSelection", "ResourceSelectionError"]
