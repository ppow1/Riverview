import pytest

from riverview.control import Gesture, GestureGrammar


def test_gesture_mapping_is_deterministic_and_contextual() -> None:
    grammar=GestureGrammar((Gesture("deck-next","deck-1","short-press","next","default"),Gesture("dial","dial-1","rotary","volume","default")))
    assert grammar.resolve("deck-1","short-press").action == "next"
    assert grammar.resolve("deck-1","short-press","other") is None

def test_destructive_action_requires_guarded_hold_and_conflicts_fail() -> None:
    with pytest.raises(ValueError, match="destructive"):
        GestureGrammar((Gesture("shutdown","deck-1","short-press","shutdown",destructive=True),))
    grammar=GestureGrammar((Gesture("x","d","hold","a"),))
    with pytest.raises(ValueError, match="ambiguous"):
        grammar.add(Gesture("y","d","hold","b"))
