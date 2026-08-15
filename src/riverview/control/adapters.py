"""Device-local adapters over the shared gesture grammar."""
from __future__ import annotations

from dataclasses import dataclass

from .gestures import GestureGrammar


@dataclass(frozen=True, slots=True)
class ControlState:
    control_id: str
    state: str
    projection_version: str
    acknowledged_action: str | None = None


class StreamDeckStateBridge:
    def render(self, control_id: str, *, state: str, projection_version: str, acknowledged_action: str | None = None) -> ControlState:
        if state not in {"ready", "running", "blocked", "error", "offline"}:
            raise ValueError("RIV-CTRL-0003: state is unsupported.")
        return ControlState(control_id, state, projection_version, acknowledged_action)


class PhysicalControlAdapter:
    def __init__(self, device_id: str, grammar: GestureGrammar) -> None:
        if not device_id.strip():
            raise ValueError("RIV-CTRL-0004: device identity is required.")
        self.device_id, self.grammar = device_id, grammar

    def resolve(self, event: str, context: str = "default"):
        return self.grammar.resolve(self.device_id, event, context)

    def disconnect(self) -> ControlState:
        return ControlState(self.device_id, "offline", "disconnect-recovery")


class PhysicalSafetyGuard:
    def authorize(self, event: str, *, confirmation: bool = False) -> bool:
        if event in {"shutdown", "emergency-stop"} and not confirmation:
            raise PermissionError("RIV-CTRL-0005: destructive control requires explicit confirmation.")
        return event not in {"duplicate-tap", "stuck-input", "profile-drift", "disconnect"}
