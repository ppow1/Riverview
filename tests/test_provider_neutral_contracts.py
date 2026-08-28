import json
from datetime import UTC, datetime
from uuid import uuid4
from urllib.error import HTTPError

import pytest

from riverview.classification import Classification, StorageReference, classify_label
from riverview.reasoning import (
    LlamaCppReasoningAdapter,
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
    assert OllamaReasoningAdapter(endpoint="http://127.0.0.1:11438").endpoint.endswith(":11438")
    assert LlamaCppReasoningAdapter(endpoint="http://127.0.0.1:11439").endpoint.endswith(":11439")


def test_ollama_adapter_forwards_bounded_response_format(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, _limit: int) -> bytes:
            return json.dumps({"response": "bounded"}).encode()

    def fake_urlopen(request, timeout):
        captured.update({"body": json.loads(request.data), "timeout": timeout})
        return Response()

    monkeypatch.setattr("riverview.reasoning.ollama.urlopen", fake_urlopen)
    request = ReasoningRequest(
        uuid4(), uuid4(), "advice", "Inspect bounded state", ("riverview://state",),
        "operational", "resident-direct-grace-v2", ("resident",), datetime.now(UTC),
        ("read:bounded", "return:advisory"), response_format={"type": "object"},
    )
    response = OllamaReasoningAdapter().complete("qwen3-coder:30b-qwencode-20k", request)
    assert captured["body"]["format"] == {"type": "object"}
    assert captured["body"]["options"] == {"temperature": 0, "seed": 7, "num_predict": 2048}
    assert response.summary == "bounded"


def test_ollama_cuda_allocation_failure_is_typed_provider_resource_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_urlopen(request, timeout):
        raise HTTPError(request.full_url, 500, "provider failure", {}, _Body())

    class _Body:
        def read(self, _limit: int) -> bytes:
            return b'{"error":"llama-server reported out-of-memory during startup: cudaMalloc failed"}'

        def close(self) -> None:
            return None

    monkeypatch.setattr("riverview.reasoning.ollama.urlopen", fail_urlopen)
    request = ReasoningRequest(uuid4(), uuid4(), "advice", "hello", (), "operational", "advice-v1", (), datetime.now(UTC), ("read:bounded",))
    with pytest.raises(RuntimeError, match="RIV-REASON-0003.*provider resource unavailable"):
        OllamaReasoningAdapter().complete("qwen3-coder:30b-qwencode-20k", request)


def test_gpu_adapter_identity_is_closed() -> None:
    with pytest.raises(ValueError, match="identity"):
        LocalGpuReasoningAdapter("unknown", "GPU")
