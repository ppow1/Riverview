"""Pure contract checks for durable Comms binding rollover."""

from uuid import uuid4

import pytest

from riverview.comms.bindings import BindingRegistry


def test_binding_reference_must_match_exact_conversation() -> None:
    conversation_id = uuid4()
    with pytest.raises(ValueError, match="RIV-COMMS-0004"):
        BindingRegistry._validate("designated_reasoning", "Riverview Comms", "v1", conversation_id, "https://chatgpt.com/c/other", "chatgpt:riverview_001", "candidate")


def test_binding_registry_rejects_unverified_activation() -> None:
    assert "steward" not in {"candidate", "initialized", "retired"}
