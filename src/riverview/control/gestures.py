"""Deterministic gesture definitions with destructive-action guards."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Gesture:
    name: str
    control_id: str
    event: str
    action: str
    context: str = "default"
    destructive: bool = False

class GestureGrammar:
    def __init__(self, gestures: tuple[Gesture, ...] = ()) -> None:
        self._gestures: dict[tuple[str, str, str], Gesture] = {}
        for gesture in gestures: self.add(gesture)
    def add(self, gesture: Gesture) -> None:
        if not all(isinstance(x, str) and x.strip() for x in (gesture.name, gesture.control_id, gesture.event, gesture.action, gesture.context)):
            raise ValueError("RIV-CTRL-0002: gesture fields are required.")
        if gesture.destructive and gesture.event in {"short-press", "double-press", "rotary"}:
            raise ValueError("RIV-CTRL-0002: destructive actions require guarded hold semantics.")
        key = (gesture.control_id, gesture.event, gesture.context)
        if key in self._gestures and self._gestures[key].action != gesture.action:
            raise ValueError("RIV-CTRL-0002: ambiguous gesture mapping.")
        self._gestures[key] = gesture
    def resolve(self, control_id: str, event: str, context: str = "default") -> Gesture | None:
        return self._gestures.get((control_id, event, context))
