import pytest

from riverview.control import Gesture, GestureGrammar
from riverview.control.adapters import (
    PhysicalControlAdapter,
    PhysicalSafetyGuard,
    StreamDeckStateBridge,
)


def test_streamdeck_projection_and_disconnect_are_bounded() -> None:
    state = StreamDeckStateBridge().render("deck-1", state="ready", projection_version="pg:1", acknowledged_action="next")
    assert state.state == "ready" and state.acknowledged_action == "next"
    grammar = GestureGrammar((Gesture("next", "dial-1", "rotary", "next"),))
    assert PhysicalControlAdapter("dial-1", grammar).disconnect().state == "offline"
    guard = PhysicalSafetyGuard()
    assert guard.authorize("stuck-input") is False
    with pytest.raises(PermissionError, match="confirmation"):
        guard.authorize("shutdown")
