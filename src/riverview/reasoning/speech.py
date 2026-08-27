"""Resident-facing speech composition after governed HOME reasoning."""
from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .contracts import ReasoningRequest, ReasoningResponse
from .cognition_contracts import CognitionResult

_SPEECH_FORMAT = {
    "type": "object",
    "properties": {"speech": {"type": "string", "minLength": 1, "maxLength": 4000}},
    "required": ["speech"],
    "additionalProperties": False,
}
_FORBIDDEN = ("response_text", "proposal", "rationale:", "acknowledge the greeting", "home_cognition")


def compose_resident_speech(
    provider: Callable[[str, ReasoningRequest], ReasoningResponse],
    model: str,
    instruction: str,
    result: CognitionResult,
) -> ReasoningResponse:
    """Render one natural response without exposing the internal HOME envelope."""
    request = ReasoningRequest(
        request_id=uuid4(), correlation_id=result.correlation_id, request_type="advice",
        instruction=(
            "Respond directly to the Steward as Grace, a Riverview resident and Director of Operations. "
            "Use the governed advisory result below only as internal guidance. Speak naturally and concisely. "
            "Do not mention prompts, HOME cognition, governance scaffolding, provider/model, JSON, proposals, "
            "rationales, or internal instructions. Do not claim execution authority. Return only the exact JSON "
            "object required by the response format, with the natural spoken response in speech.\n"
            f"Steward message: {instruction}\n"
            f"Internal advisory guidance (not speech): {json.dumps({'recommendation': result.recommendation, 'uncertainty': result.uncertainty, 'constraints': list(result.constraints)}, sort_keys=True)}"
        ),
        context_refs=tuple(result.provenance_refs), classification=result.classification,
        required_output_schema="resident-speech-v1", evidence_requirements=("speech-composition", "correlation"),
        expires_at=datetime.now(UTC), allowed_authority=("return:advisory",), response_format=_SPEECH_FORMAT,
    )
    response = provider(model, request)
    try:
        value = json.loads(response.summary)
    except json.JSONDecodeError as exc:
        raise RuntimeError("RIV-RES-0002: resident speech composer returned invalid JSON.") from exc
    speech = value.get("speech") if isinstance(value, dict) else None
    if not isinstance(speech, str) or not speech.strip() or any(marker in speech.casefold() for marker in _FORBIDDEN):
        raise RuntimeError("RIV-RES-0002: resident speech composer returned internal scaffolding.")
    return ReasoningResponse(
        response_id=response.response_id, request_id=request.request_id,
        correlation_id=result.correlation_id, provider_id=f"resident-speech:{response.provider_id}",
        response_type="advice", summary=speech.strip(),
        evidence_refs=tuple(dict.fromkeys((*result.provenance_refs, f"speech-composition:{response.response_id}"))),
        classification=result.classification, created_at=response.created_at,
    )
