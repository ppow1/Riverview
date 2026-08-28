"""Pure, secret-safe projections for the additive Operator vNext surface."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

PULSE_STATES = (
    "HEALTHY",
    "STALE",
    "INTENTIONALLY OFF",
    "STARTING / RECONNECTING",
    "UNREACHABLE",
    "ATTENTION REQUIRED",
)


@dataclass
class ConverseState:
    """Small pure model for the browser's requested/active safety invariant."""

    active_id: str = ""
    requested_id: str = ""
    load_state: str = "idle"
    generation: int = 0
    unavailable_id: str = ""

    def request(self, conversation_id: str) -> int:
        self.requested_id = str(conversation_id)
        self.load_state = "loading"
        self.generation += 1
        self.unavailable_id = ""
        return self.generation

    def loaded(self, conversation_id: str, generation: int) -> bool:
        if generation != self.generation or str(conversation_id) != self.requested_id:
            return False
        self.active_id = str(conversation_id)
        self.load_state = "active"
        self.unavailable_id = ""
        return True

    def failed(self, conversation_id: str, generation: int) -> bool:
        if generation != self.generation or str(conversation_id) != self.requested_id:
            return False
        self.load_state = "failed"
        self.unavailable_id = str(conversation_id)
        return True

    @property
    def transition_unresolved(self) -> bool:
        return self.load_state == "loading" and self.requested_id != self.active_id

    def send_target(self) -> str | None:
        return None if self.transition_unresolved or not self.active_id else self.active_id


def humanize_status(value: Any) -> str:
    """Make machine status readable while retaining the raw value elsewhere."""
    raw = str(value or "UNAVAILABLE").strip()
    return raw.replace("_", " ").replace("-", " ").title()


def humanize_event(value: Any) -> str:
    raw = str(value or "event unavailable").strip()
    return " ".join(humanize_status(part) for part in raw.split("."))


def humanize_heartbeat_age(value: Any) -> str:
    try:
        seconds = max(0, int(float(value)))
    except (TypeError, ValueError):
        return "Heartbeat age unavailable"
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    return f"{minutes}m ago" if minutes < 60 else f"{minutes // 60}h ago"


def _iso(value: Any) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else str(value) if value else None


def build_pulse(*, cme: Mapping[str, Any] | None, runtime: Mapping[str, Any] | None,
                now: datetime | None = None, stale_after_seconds: int = 30) -> dict[str, Any]:
    """Derive an honest pulse; missing telemetry is never healthy by inference."""
    now = now or datetime.now(UTC)
    cme = cme if isinstance(cme, Mapping) else None
    runtime = runtime if isinstance(runtime, Mapping) else None
    age = cme.get("heartbeat_age_seconds") if cme else None
    try:
        age = float(age) if age is not None else None
    except (TypeError, ValueError):
        age = None
    explicit = str((cme or {}).get("effective_state") or "").strip().upper()
    health = str((cme or {}).get("heartbeat_health") or "").strip().upper()
    attention = bool((cme or {}).get("steward_attention_required") or (cme or {}).get("attention_required"))
    if attention or explicit in {"ATTENTION REQUIRED", "ATTENTION_REQUIRED", "BLOCKED"}:
        state = "ATTENTION REQUIRED"
    elif explicit in {"INTENTIONALLY OFF", "OFF", "DISABLED"}:
        state = "INTENTIONALLY OFF"
    elif cme is None and runtime is None:
        state = "UNREACHABLE"
    elif cme is None:
        state = "STARTING / RECONNECTING"
    elif age is not None and age > stale_after_seconds:
        state = "STALE"
    elif health in {"HEALTHY", "OK", "FRESH"} and age is not None and age <= stale_after_seconds:
        state = "HEALTHY"
    else:
        state = "STARTING / RECONNECTING"
    return {
        "state": state,
        "allowed_states": list(PULSE_STATES),
        "observed_at": _iso((cme or {}).get("observed_at") or (runtime or {}).get("generated_at")) or now.isoformat(),
        "source": "cme_status_route" if cme else "runtime_status_file" if runtime else "unavailable",
        "freshness": {"heartbeat_age_seconds": age, "stale_after_seconds": stale_after_seconds},
        "reason": (cme or {}).get("waiting_reason") or (cme or {}).get("reason") or "No authoritative pulse projection available.",
        "authority": "Riverview CME status read model" if cme else "unknown",
        "checkpoint": (cme or {}).get("checkpoint") or "RIV-VNEXT-PULSE-0001",
    }


def build_resource_topology(observations: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return the fixed drilldown shape without inventing hardware telemetry."""
    observations = observations if isinstance(observations, Mapping) else {}
    chassis = []
    for chassis_name in ("Chassis A", "Chassis B"):
        tower = {"id": f"{chassis_name}:Tower 1", "label": "Tower 1", "state": "UNKNOWN", "children": []}
        for slot_number in range(1, 13):
            key = f"{chassis_name}:slot:{slot_number}"
            observed = observations.get(key) if isinstance(observations.get(key), Mapping) else {}
            gpu = observed.get("gpu") if isinstance(observed.get("gpu"), Mapping) else {}
            slot = {"id": key, "label": f"Slot {slot_number}", "state": observed.get("state", "UNKNOWN"),
                    "children": [{"id": f"{key}:gpu", "label": "GPU", "state": gpu.get("state", "UNKNOWN"),
                                  "model": gpu.get("model"), "process": gpu.get("process"), "workload": gpu.get("workload"),
                                  "source": gpu.get("source"), "observed_at": gpu.get("observed_at")} ]}
            tower["children"].append(slot)
        chassis.append({"id": chassis_name, "label": chassis_name, "independent": True, "children": [tower]})
    return {"schema_version": "riverview-resource-topology-v1", "source": "bounded_resource_observations", "chassis": chassis,
            "association_rule": "model/process/workload is shown only when its source observation proves the association"}


def build_vnext_projection(*, cme: Mapping[str, Any] | None, runtime: Mapping[str, Any] | None,
                           conversations: list[Mapping[str, Any]] | None = None,
                           residents: list[Mapping[str, Any]] | None = None,
                           context: Mapping[str, Any] | None = None,
                           activity: list[Mapping[str, Any]] | None = None,
                           now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    cme = dict(cme) if isinstance(cme, Mapping) else None
    heartbeat_age = cme.get("heartbeat_age_seconds") if cme else None
    bounded_activity = [dict(item) for item in (activity or [])[:12]]
    return {
        "schema_version": "riverview-operator-vnext-projection-v1",
        "observed_at": now.isoformat(),
        "authority": "derived read-only projection; PostgreSQL remains Riverview authority",
        "pulse": build_pulse(cme=cme, runtime=runtime, now=now),
        "liveness": {
            "heartbeat": {"state": "known" if cme and cme.get("heartbeat_age_seconds") is not None else "unknown",
                          "age_seconds": cme.get("heartbeat_age_seconds") if cme else None},
            "last_activity": {"value": cme.get("last_event_type") if cme else None, "state": "known" if cme and cme.get("last_event_type") else "unknown"},
            "working_state": {"value": cme.get("effective_state") if cme else None, "state": "known" if cme and cme.get("effective_state") else "unknown"},
        },
        "cme": cme or {"state": "UNAVAILABLE", "source": "cme_status_route"},
        "runtime": runtime or {"state": "UNAVAILABLE", "source": "runtime_status_file"},
        "conversations": [dict(item) for item in (conversations or [])[:24]],
        "residents": [dict(item) for item in (residents or [])],
        "context": dict(context) if isinstance(context, Mapping) else {
            "state": "empty", "reason": "No current conversation is available from the read model."
        },
        "activity": bounded_activity,
        "human": {
            "pulse": humanize_status(build_pulse(cme=cme, runtime=runtime, now=now)["state"]),
            "heartbeat": humanize_heartbeat_age(heartbeat_age),
            "last_activity": humanize_event((cme or {}).get("last_event_type")),
        },
        "resources": build_resource_topology(),
        "diagnostics": {"provenance": ["/api/cme/status", "/api/runtime/status", "operator_projection"],
                        "freshness": "See pulse.freshness; unknown means no trustworthy observation was available.",
                        "source_policy": "read-only, bounded, secret-safe; browser state is not authority"},
    }
