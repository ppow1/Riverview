from __future__ import annotations

from contextlib import contextmanager

import pytest

from riverview.mcp.comms5 import Comms5Error, Comms5Service


class Cursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query: str) -> None:
        assert query == "SELECT 1"

    def fetchone(self):
        return (1,)


class Connection:
    def cursor(self):
        return Cursor()


@contextmanager
def fake_connect():
    yield Connection()


def test_transport_probe_is_read_only_and_correlates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("riverview.mcp.comms5.connect", fake_connect)
    result = Comms5Service().transport_probe("chatgpt-test-001", "http-test-001")
    assert result == {
        "probe_id": "chatgpt-test-001",
        "server_request_id": "http-test-001",
        "database": "completed",
        "operation": "transport_probe",
    }


def test_transport_probe_rejects_unbounded_or_sensitive_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("riverview.mcp.comms5.connect", fake_connect)
    with pytest.raises(Comms5Error):
        Comms5Service().transport_probe("bad token", "http-test-001")


def test_resource_policy_operations_are_governed_and_not_reset_activation(monkeypatch: pytest.MonkeyPatch) -> None:
    service = Comms5Service()
    assert service.describe_operation("resource_policy_status")["authorization"] == "READ_ONLY"
    assert service.describe_operation("set_resource_policy")["authorization"] == "STEWARD-GATED_WRITE"
    with pytest.raises(Comms5Error, match="authenticated Steward"):
        service.set_resource_policy({"mode": "DRAIN", "parameters": {"target_seat": "C3"}, "explicit_steward_confirmation": True}, transport_principal=None)
