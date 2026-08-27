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
ESTABLISHED_SAFE_FINGERPRINTS = {
    "C1": "000f32ae28fba7b8",
    "C2": "20521e97b56e0445",
    "C3": "ac91c17202d67add",
}


def reset_refill_observed(
    previous_capacity: float | None,
    current_capacity: float | None,
    *,
    minimum_jump: float = 20,
) -> bool:
    """Identify a material observed refill without trusting reset timestamps."""
    return (
        isinstance(previous_capacity, (int, float))
        and not isinstance(previous_capacity, bool)
        and isinstance(current_capacity, (int, float))
        and not isinstance(current_capacity, bool)
        and isinstance(minimum_jump, (int, float))
        and not isinstance(minimum_jump, bool)
        and minimum_jump >= 0
        and current_capacity - previous_capacity >= minimum_jump
    )


def _timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class ResourcePolicy:
    mode: str = "HIGHEST_CAPACITY"
    target_seat: str | None = None
    priority_order: tuple[str, ...] = ()
    fallback: bool = True

    def __post_init__(self) -> None:
        modes = {"BALANCED", "HIGHEST_CAPACITY", "ROUND_ROBIN", "DRAIN", "PRESERVE", "SOONEST_ROLLOVER", "MAXIMIZE_RUNWAY", "PRIORITY"}
        if self.mode not in modes:
            raise ValueError(f"RIV-RES-0004: unsupported resource policy mode: {self.mode}")
        if self.mode in {"DRAIN", "PRESERVE"} and self.target_seat not in {"C1", "C2", "C3"}:
            raise ValueError(f"RIV-RES-0004: {self.mode} requires a valid target seat.")


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
    seat_id: str | None = None
    identity_fingerprint: str | None = None
    current_execution_state: str | None = None
    reset_refill_observed: bool = False
    quota_windows: tuple[dict[str, Any], ...] = ()
    usage_resets_remaining: int | None = None
    usage_reset_scope: str | None = None
    usage_reset_period: str | None = None
    usage_reset_eligible: bool | None = None
    usage_reset_activation_method: str | None = None
    usage_reset_last_observed: datetime | None = None

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
            seat_id=str(value["seat_id"]).strip() if value.get("seat_id") else None,
            identity_fingerprint=str(value["identity_fingerprint"]).strip() if value.get("identity_fingerprint") else None,
            current_execution_state=str(value["current_execution_state"]).strip().lower() if value.get("current_execution_state") else None,
            reset_refill_observed=bool(value.get("reset_refill_observed", False)) or reset_refill_observed(
                value.get("previous_observed_capacity"), observed,
            ),
            quota_windows=tuple(item for item in value.get("quota_windows", ()) if isinstance(item, dict)),
            usage_resets_remaining=value.get("usage_resets_remaining") if isinstance(value.get("usage_resets_remaining"), int) else None,
            usage_reset_scope=str(value["usage_reset_scope"]).strip() if value.get("usage_reset_scope") else None,
            usage_reset_period=str(value["usage_reset_period"]).strip() if value.get("usage_reset_period") else None,
            usage_reset_eligible=value.get("usage_reset_eligible") if isinstance(value.get("usage_reset_eligible"), bool) else None,
            usage_reset_activation_method=str(value["usage_reset_activation_method"]).strip() if value.get("usage_reset_activation_method") else None,
            usage_reset_last_observed=_timestamp(value.get("usage_reset_last_observed")),
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
                "seat_id": seat.get("seat_id"),
                "identity_fingerprint": (seat.get("account") or {}).get("identity_fingerprint") or ESTABLISHED_SAFE_FINGERPRINTS.get(str(seat.get("seat_id"))),
                "current_execution_state": seat.get("current_execution_state"),
                "reset_refill_observed": bool(seat.get("reset_refill_observed", False)),
                "quota_windows": seat.get("windows", ()),
                "usage_resets_remaining": seat.get("usage_resets_remaining"),
                "usage_reset_scope": seat.get("usage_reset_scope"),
                "usage_reset_period": seat.get("usage_reset_period"),
                "usage_reset_eligible": seat.get("usage_reset_eligible"),
                "usage_reset_activation_method": seat.get("usage_reset_activation_method"),
                "usage_reset_last_observed": seat.get("usage_reset_last_observed"),
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
        excluded_seats: set[str] | None = None,
    ) -> ResourceSelection:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        candidates: list[ExecutionResource] = []
        rejected_independent = False
        for resource in self.resources:
            if resource.seat_id in (excluded_seats or set()):
                continue
            if required_capability not in resource.capabilities or classification not in resource.classification_eligibility:
                continue
            if role not in resource.roles or resource.health != "healthy" or not resource.available:
                continue
            if resource.current_execution_state in {"busy", "running", "claimed", "starting"}:
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

    def select_codex_seat(
        self,
        *,
        now: datetime | None = None,
        freshness: timedelta = timedelta(minutes=30),
        role: str = "writer",
        classification: str = "river",
    ) -> ResourceSelection:
        """Select the best eligible Codex seat using current telemetry."""
        return self.select(
            required_capability="bounded-engineering",
            classification=classification,
            role=role,
            now=now,
            freshness=freshness,
        )

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

class ResourcePlanner:
    """Deterministic strategic policy layer over the authoritative registry."""

    def __init__(self, registry: ResourceRegistry) -> None:
        self.registry = registry
        self._round_robin_cursor = 0

    @staticmethod
    def _soonest_reset(resource: ExecutionResource, now: datetime) -> float:
        times = []
        for window in resource.quota_windows:
            reset = _timestamp(window.get("resets_at") or window.get("reset_at"))
            if reset is not None and reset >= now:
                times.append((reset - now).total_seconds())
        if resource.reset_at is not None and resource.reset_at >= now:
            times.append((resource.reset_at - now).total_seconds())
        return min(times) if times else float("inf")

    def select(self, policy: ResourcePolicy, *, role: str = "writer", now: datetime | None = None, freshness: timedelta = timedelta(minutes=30), excluded_seats: set[str] | None = None) -> ResourceSelection:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        baseline = self.registry.select(required_capability="bounded-engineering", classification="river", role=role, now=current, freshness=freshness, excluded_seats=excluded_seats)
        if baseline.resource is None:
            return baseline
        candidates = [item for item in self.registry.resources if item.resource_id in baseline.candidates_considered]
        original = list(candidates)
        if policy.mode == "PRESERVE":
            alternatives = [item for item in candidates if item.seat_id != policy.target_seat]
            if alternatives:
                candidates = alternatives
        if policy.mode == "DRAIN":
            target = [item for item in candidates if item.seat_id == policy.target_seat]
            if target:
                candidates = target
        if policy.mode == "PRIORITY":
            order = {seat: index for index, seat in enumerate(policy.priority_order)}
            selected = min(candidates, key=lambda item: (order.get(item.seat_id, len(order)), item.resource_id))
        elif policy.mode == "ROUND_ROBIN":
            ordered = sorted(candidates, key=lambda item: item.seat_id or item.resource_id)
            selected = ordered[self._round_robin_cursor % len(ordered)]
            self._round_robin_cursor = (self._round_robin_cursor + 1) % len(ordered)
        elif policy.mode == "SOONEST_ROLLOVER":
            selected = min(candidates, key=lambda item: (self._soonest_reset(item, current), -(item.observed_capacity if item.observed_capacity is not None else -1), item.resource_id))
        elif policy.mode == "MAXIMIZE_RUNWAY":
            def runway(item: ExecutionResource) -> float:
                values = [float(w["remaining_percent"]) for w in item.quota_windows if isinstance(w.get("remaining_percent"), (int, float))]
                return min(values, default=item.observed_capacity if item.observed_capacity is not None else -1)
            selected = max(candidates, key=lambda item: (runway(item), item.resource_id))
        else:
            selected = max(candidates, key=lambda item: (item.observed_capacity is not None, item.observed_capacity if item.observed_capacity is not None else -1, -item.workload, item.resource_id))
        excluded = "" if len(candidates) == len(original) else f"; excluded target {policy.target_seat}"
        reason = f"selected {selected.seat_id or selected.resource_id} under {policy.mode}: candidates={[item.seat_id or item.resource_id for item in original]}{excluded}; observed windows and freshness passed eligibility"
        return ResourceSelection(selected, reason, tuple(item.resource_id for item in original))

__all__ = [
    "DEFAULT_CODEX_TELEMETRY",
    "ExecutionResource",
    "ResourcePlanner",
    "ResourcePolicy",
    "ResourceRegistry",
    "ResourceSelection",
    "ResourceSelectionError",
    "reset_refill_observed",
]
