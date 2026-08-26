from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError
from uuid import uuid4

import pytest

from riverview.reasoning.contracts import ReasoningRequest
from riverview.reasoning.hermes import (
    HermesAuthenticationError,
    HermesMalformedResponseError,
    HermesPolicyViolationError,
    HermesReasoningProvider,
    HermesTimeoutError,
    HermesUnavailableError,
)


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit: int = -1) -> bytes:
        return self.payload


def request(**changes) -> ReasoningRequest:
    values = dict(
        request_id=uuid4(),
        correlation_id=uuid4(),
        request_type="analysis",
        instruction=json.dumps(
            {
                "resident_identity": {
                    "resident_id": str(uuid4()),
                    "occupant_id": str(uuid4()),
                    "office_id": str(uuid4()),
                    "implementation_id": str(uuid4()),
                },
                "objective": "Inspect one bounded repository seam.",
                "question": "What is the smallest safe next observation?",
            },
        ),
        context_refs=("river:state:bounded",),
        classification="operational",
        required_output_schema="grace-high-reasoning-e2-v1",
        evidence_requirements=("provider-request", "provider-response"),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        allowed_authority=("return:advisory",),
    )
    values.update(changes)
    return ReasoningRequest(**values)


def response(content: str = "{\"recommendation\":\"inspect\"}", model: str = "local-qwen") -> bytes:
    return json.dumps(
        {"model": model, "choices": [{"message": {"content": content}}]},
    ).encode()


def test_provider_preserves_riverview_correspondence_and_emits_evidence() -> None:
    captured: dict[str, object] = {}

    def opener(req, timeout):
        captured["timeout"] = timeout
        captured["headers"] = dict(req.headers)
        captured["body"] = json.loads(req.data)
        return FakeResponse(response())

    source = request()
    provider = HermesReasoningProvider(
        endpoint="http://127.0.0.1:8642/v1",
        provider_id="hermes:local-qwen",
        resource_class_ref="hermes:local-4090",
        api_key="unit-secret",
        opener=opener,
    )

    result = provider.generate(source)

    assert result.request_id == source.request_id
    assert result.correlation_id == source.correlation_id
    assert result.classification == source.classification
    assert result.provider_id == "hermes:local-qwen"
    assert result.response_type == "analysis"
    assert result.evidence_refs[:2] == (
        f"hermes:request:{source.request_id}",
        f"hermes:response:{result.response_id}",
    )
    assert "hermes:provider:hermes:local-qwen" in result.evidence_refs
    assert "hermes:resource:hermes:local-4090" in result.evidence_refs
    assert captured["headers"]["Authorization"] == "Bearer unit-secret"
    assert provider.resource_metadata() == {
        "provider_id": "hermes:local-qwen",
        "provider_type": "hermes",
        "resource_class_ref": "hermes:local-4090",
        "model_ref": None,
        "classification": "provider-declared",
    }
    assert captured["body"]["messages"][0]["content"].startswith("Riverview is authoritative")
    assert captured["body"]["messages"][1]["content"] == source.instruction


def test_provider_restricts_endpoint_and_timeout() -> None:
    with pytest.raises(ValueError, match="loopback"):
        HermesReasoningProvider(endpoint="http://example.com/v1")
    with pytest.raises(ValueError, match="timeout"):
        HermesReasoningProvider(timeout_seconds=0.01)
    with pytest.raises(ValueError, match="timeout"):
        HermesReasoningProvider(timeout_seconds=121)


def test_provider_maps_authentication_failure_without_leaking_secret() -> None:
    secret = "never-return-this-secret"

    def opener(*_args, **_kwargs):
        raise HTTPError("http://127.0.0.1:8642/v1/chat/completions", 401, secret, {}, None)

    with pytest.raises(HermesAuthenticationError) as error:
        HermesReasoningProvider(api_key=secret, opener=opener).generate(request())
    assert secret not in str(error.value)


def test_provider_maps_timeout_and_unavailable() -> None:
    def timed_out(*_args, **_kwargs):
        raise TimeoutError("provider timeout")

    with pytest.raises(HermesTimeoutError):
        HermesReasoningProvider(opener=timed_out).generate(request())

    def unavailable(*_args, **_kwargs):
        raise OSError("connection refused")

    with pytest.raises(HermesUnavailableError):
        HermesReasoningProvider(opener=unavailable).generate(request())


def test_provider_rejects_malformed_or_oversized_response() -> None:
    for payload in (b"{}", b"not-json", b'{"choices":[{"message":{}}]}'):
        with pytest.raises(HermesMalformedResponseError):
            HermesReasoningProvider(
                opener=lambda *_args, _payload=payload, **_kwargs: FakeResponse(_payload),
            ).generate(request())

    huge = b'{"choices":[{"message":{"content":"' + (b"x" * 12001) + b'"}}]}'
    with pytest.raises(HermesMalformedResponseError):
        HermesReasoningProvider(
            opener=lambda *_args, **_kwargs: FakeResponse(huge),
        ).generate(request())


def test_provider_fails_closed_on_expired_or_widened_request() -> None:
    with pytest.raises(HermesPolicyViolationError, match="expired"):
        HermesReasoningProvider(opener=lambda *_args, **_kwargs: FakeResponse(response())).generate(
            request(expires_at=datetime.now(UTC) - timedelta(seconds=1)),
        )
    with pytest.raises(HermesPolicyViolationError, match="authority"):
        HermesReasoningProvider(opener=lambda *_args, **_kwargs: FakeResponse(response())).generate(
            request(allowed_authority=("read:bounded", "return:advisory")),
        )


def test_provider_rejects_identity_override_in_advisory_output() -> None:
    payload = response('{"resident_id":"other-resident","recommendation":"inspect"}')
    with pytest.raises(HermesPolicyViolationError, match="identity"):
        HermesReasoningProvider(
            opener=lambda *_args, **_kwargs: FakeResponse(payload),
        ).generate(request())
