"""Quest/voice input mapping into existing bounded gesture semantics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InputResolution:
    input_kind: str
    gesture: str
    requires_confirmation: bool


def resolve_input(input_kind: str, gesture: str) -> InputResolution:
    if input_kind not in {"voice", "controller", "gaze", "hand"} or not gesture.strip():
        raise ValueError("RIV-SPAT-0003: input mapping is outside the bounded grammar.")
    destructive = gesture in {"shutdown", "power_off", "retire"}
    return InputResolution(input_kind, gesture, destructive)
