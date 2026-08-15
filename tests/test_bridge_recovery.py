"""Contract tests for the bounded RV-008.6 recovery state machine."""

from uuid import uuid4

import pytest

from riverview.bridge.recovery import BridgeRecoveryStore


def test_recovery_contract_rejects_unbounded_operations() -> None:
    store = BridgeRecoveryStore()
    with pytest.raises(ValueError, match="RIV-0086-0001"):
        store.begin(uuid4(), uuid4(), operation="browser")
    with pytest.raises(ValueError, match="RIV-0086-0001"):
        store.begin(uuid4(), uuid4(), max_attempts=4)
