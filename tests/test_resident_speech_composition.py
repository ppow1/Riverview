import json
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from riverview.reasoning.speech import compose_resident_speech
from riverview.reasoning import ReasoningResponse


def result():
    return SimpleNamespace(
        recommendation="Maintain bounded advisory oversight.",
        uncertainty="Some operational evidence remains incomplete.",
        constraints=("advisory only",),
        provenance_refs=("home:event:1",),
        correlation_id=uuid4(),
        classification="operational",
    )


def provider_with(value):
    def provider(model, request):
        return ReasoningResponse(uuid4(), request.request_id, request.correlation_id, "ollama:qwen3-coder:30b", "advice", json.dumps(value), ("provider:evidence",), request.classification, datetime.now(UTC))
    return provider


def test_home_result_composes_natural_speech_without_internal_envelope():
    response = compose_resident_speech(provider_with({"speech": "Good evening. I’m Grace, Director of Operations. How may I help?"}), "qwen3-coder:30b", "Good evening, Grace.", result())
    assert response.summary.startswith("Good evening.")
    assert "response_text" not in response.summary
    assert "proposal" not in response.summary
    assert "home:event:1" in response.evidence_refs


def test_governed_proposal_word_is_allowed_in_natural_speech():
    response = compose_resident_speech(provider_with({"speech": "The next step is a bounded engineering proposal for Steward review."}), "qwen3-coder:30b", "What resources are available?", result())
    assert "proposal" in response.summary


def test_unsupported_named_resident_is_not_presented_as_capability_owner():
    material = (json.dumps({"value": {"metadata": {"registry": [{"name": "Jessica"}], "capabilities": [{"human_owner_known": False, "suitable_resident_ids": []}]}}}),)
    response = compose_resident_speech(provider_with({"speech": "Jessica is the right person to handle that."}), "qwen3-coder:30b", "What internal resource is appropriate?", result(), material)
    assert "Jessica" not in response.summary
    assert "codex.engineering.v1" in response.summary
    assert "does not execute" in response.summary


@pytest.mark.parametrize("speech", [
    '{"response_text":"Hello","proposal":null}',
    "Acknowledge the greeting and respond appropriately.",
    "Rationale: internal guidance",
])
def test_home_speech_composer_rejects_internal_scaffolding(speech):
    value = json.loads(speech) if speech.startswith("{") else {"speech": speech}
    response = compose_resident_speech(provider_with(value), "qwen3-coder:30b", "Hello", result())
    assert "response_text" not in response.summary
    assert "Rationale:" not in response.summary
    assert "Acknowledge the greeting" not in response.summary
