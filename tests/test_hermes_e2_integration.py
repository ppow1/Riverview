from __future__ import annotations

import json

from riverview.reasoning import HermesReasoningProvider
from test_e2_high_reasoning import packet_and_assessment, coordinator
from test_e1_home_cognition import MemoryEventStore


class Response:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, limit=-1):
        return self.body


def test_real_hermes_provider_plugs_into_existing_riverview_e2_boundary():
    summary = {
        "recommendation": "Use the bounded advisory path.",
        "rationale": "Evidence supports review.",
        "uncertainty": None,
        "confidence": 0.8,
        "constraints": ["advisory only"],
        "unresolved_questions": [],
        "further_escalation_warranted": False,
        "authority_scope": ["return:advisory"],
        "live_generation": True,
        "provenance_refs": ["provider://hermes/e2"],
    }

    def opener(_request, timeout):
        assert timeout == 30.0
        return Response(json.dumps({
            "model": "codex-test",
            "choices": [{"message": {"content": json.dumps(summary)}}],
        }).encode())

    store = MemoryEventStore()
    _, packet, assessment = packet_and_assessment(store)
    provider = HermesReasoningProvider(
        provider_id="hermes:e2-test",
        resource_class_ref="resource:codex-test",
        model_ref="codex-test",
        opener=opener,
    )
    outcome = coordinator(store, provider.generate, provider_id="hermes:e2-test").execute(
        __import__("riverview.reasoning", fromlist=["HighReasoningInvocation"]).HighReasoningInvocation(
            packet, assessment, "authority://grace/high/e2"
        )
    )
    assert outcome.result.status.value == "completed"
    assert outcome.result.provider_ref == "hermes:e2-test"
    assert outcome.result.live_generation is True
    assert outcome.observation is not None
    assert outcome.observation.response_evidence_ref == next(
        ref for ref in outcome.result.provenance_refs if ref.startswith("provider-response:")
    )
