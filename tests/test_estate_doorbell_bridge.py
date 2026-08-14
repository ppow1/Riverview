from __future__ import annotations

import json
from subprocess import CompletedProcess, TimeoutExpired
from uuid import uuid4

import pytest

from riverview.doorbell.contract import DoorbellRequest
from riverview.doorbell.estate_bridge import (
    DESIGNATED_SELECTOR,
    MAILBOX_RESOURCE,
    EstateBridgeRunner,
)


def request() -> DoorbellRequest:
    return DoorbellRequest(uuid4(), uuid4(), DESIGNATED_SELECTOR, MAILBOX_RESOURCE)


def fake_runner(result: dict):
    def run(*args, **kwargs):
        assert args[0][-1] == "--ring"
        payload = json.loads(kwargs["input"])
        assert sorted(payload) == ["correlation_id", "operation", "request_id", "timeout_seconds"]
        assert payload["operation"] == "ring_riverview_doorbell"
        return CompletedProcess(args[0], 0, json.dumps(result) + "\n", "")

    return run


def test_adapter_calls_only_named_estate_operation_and_preserves_identity():
    source = fake_runner({"status": "succeeded", "evidence_ref": "estate://doorbell/a"})
    req = request()
    result = EstateBridgeRunner(runner=source).ring(req)
    assert result.state == "succeeded"
    assert result.request_id == req.request_id
    assert result.correlation_id == req.correlation_id
    assert result.evidence_ref == "estate://doorbell/a"


def test_adapter_rejects_general_target_and_mailbox_inputs():
    req = DoorbellRequest(uuid4(), uuid4(), "other-target", MAILBOX_RESOURCE)
    with pytest.raises(ValueError, match="only the Estate designated target"):
        EstateBridgeRunner().ring(req)


def test_adapter_maps_bounded_failure_without_exposing_output():
    req = request()
    result = EstateBridgeRunner(runner=fake_runner({"status": "failed", "failure_class": "RIV-PLY-0005", "body": "secret"})).ring(req)
    assert result.state == "failed"
    assert result.failure_class == "RIV-PLY-0005"
    assert result.evidence_ref is None


def test_adapter_maps_timeout():
    def timeout(*args, **kwargs):
        raise TimeoutExpired(args[0], kwargs["timeout"])

    result = EstateBridgeRunner(runner=timeout).ring(request())
    assert result.state == "failed"
    assert result.failure_class == "RIV-PLY-0009"
