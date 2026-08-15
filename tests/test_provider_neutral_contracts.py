from datetime import UTC, datetime
from uuid import uuid4

import pytest

from riverview.classification import Classification, StorageReference, classify_label
from riverview.reasoning import (
    LocalGpuReasoningAdapter,
    OllamaReasoningAdapter,
    ReasoningProvider,
    ReasoningRequest,
    ReasoningResponse,
)


def test_provider_neutral_envelopes_validate() -> None:
    request_id, correlation_id = uuid4(), uuid4()
    provider = ReasoningProvider("chatgpt:riverview_001", "local-codex", "cli", "reasoning", ("advice",), ("operational",))
    request = ReasoningRequest(request_id, correlation_id, "advice", "Inspect bounded state", ("riverview://state",), "operational", "advice-v1", ("roadmap",), datetime.now(UTC), ("read:bounded", "return:advisory"))
    response = ReasoningResponse(uuid4(), request_id, correlation_id, provider.provider_id, "advice", "Bounded result", ("riverview://evidence",), "operational", datetime.now(UTC))
    assert request.request_id == request_id
    assert response.as_typed_payload()["correlation_id"] == str(correlation_id)


def test_provider_contract_rejects_openai_and_unknown_response() -> None:
    with pytest.raises(ValueError, match="OpenAI"):
        ReasoningProvider("x", "openai-api", "external", "reasoning", ("advice",), ("operational",))
    with pytest.raises(ValueError, match="unsupported"):
        ReasoningResponse(uuid4(), uuid4(), uuid4(), "codex", "execute", "x", ("e",), "operational", datetime.now(UTC))


def test_classification_and_reference_fail_closed() -> None:
    assert classify_label("PUBLIC") is Classification.PUBLIC
    assert not StorageReference("r", "ref://x", "a" * 64, "owner", Classification.SENSITIVE, 1, "text/plain", "test").ordinary_river_safe()
    with pytest.raises(ValueError, match="unknown classification"):
        classify_label("mystery")


def test_ollama_adapter_is_loopback_only() -> None:
    with pytest.raises(ValueError, match="loopback"):
        OllamaReasoningAdapter(endpoint="https://example.invalid")


def test_gpu_adapter_identity_is_closed() -> None:
    with pytest.raises(ValueError, match="identity"):
        LocalGpuReasoningAdapter("unknown", "GPU")
