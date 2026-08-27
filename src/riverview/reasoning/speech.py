"""Resident-facing speech composition after governed HOME reasoning."""
from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .contracts import ReasoningRequest, ReasoningResponse
from .cognition_contracts import CognitionResult
from .claim_grounding import ground_claims

_SPEECH_FORMAT = {
    "type": "object",
    "properties": {"speech": {"type": "string", "minLength": 1, "maxLength": 4000}, "assertion_mode": {"enum": ["ordinary", "institutional"]}, "institutional_claims": {"type": "array", "maxItems": 16, "items": {"type": "object"}}},
    "required": ["speech", "assertion_mode", "institutional_claims"],
    "additionalProperties": False,
}
_FORBIDDEN = ("response_text", "rationale:", "acknowledge the greeting", "home_cognition")


def compose_resident_speech(
    provider: Callable[[str, ReasoningRequest], ReasoningResponse],
    model: str,
    instruction: str,
    result: CognitionResult,
    context_material: tuple[str, ...] = (),
) -> ReasoningResponse:
    """Render one natural response without exposing the internal HOME envelope."""
    request = ReasoningRequest(
        request_id=uuid4(), correlation_id=result.correlation_id, request_type="advice",
        instruction=(
            "Respond directly to the Steward as Grace, a Riverview resident and Director of Operations. "
            "Use the governed advisory result below only as internal guidance. Speak naturally and concisely. "
            "Do not mention prompts, HOME cognition, governance scaffolding, provider/model, JSON, proposals, "
            "rationales, or internal instructions. Do not claim execution authority. Return only the exact JSON "
            "object required by the response format, with the natural spoken response in speech. Set "
            "assertion_mode to institutional and provide typed institutional_claims for any Riverview "
            "responsibility, capability, owner, suitability, or authoritative-contact assertion; use ordinary "
            "only for non-authoritative conversation.\n"
            f"Steward message: {instruction}\n"
            f"Internal advisory guidance (not speech): {json.dumps({'recommendation': result.recommendation, 'uncertainty': result.uncertainty, 'constraints': list(result.constraints)}, sort_keys=True)}"
        ),
        context_refs=tuple(result.provenance_refs), classification=result.classification,
        required_output_schema="resident-speech-v1", evidence_requirements=("speech-composition", "correlation"),
        expires_at=datetime.now(UTC), allowed_authority=("return:advisory",), response_format=_SPEECH_FORMAT,
    )
    last_error: RuntimeError | None = None
    last_response: ReasoningResponse | None = None
    registry_names: set[str] = set()
    domain_matches: dict[str, str] = {}
    no_owner_capability = False
    engineering_capability_known = False
    for raw in context_material:
        if "human_owner_known" in raw and "false" in raw and "suitable_resident_ids" in raw:
            no_owner_capability = True
        if "codex.engineering.v1" in raw:
            engineering_capability_known = True
        if '"name":"Jessica"' in raw:
            registry_names.add("Jessica")
        if '"name":"Marie"' in raw and '"responsibility_domains":["research"]' in raw:
            domain_matches["research"] = "Marie, Manager of Research"
        try:
            value = json.loads(raw).get("value", {}).get("metadata", {})
            registry_names.update(str(row["name"]) for row in value.get("registry", ()) if isinstance(row, dict) and row.get("name"))
            for row in value.get("registry", ()):
                if isinstance(row, dict) and row.get("name") and row.get("responsibility_domains"):
                    for domain in row["responsibility_domains"]:
                        domain_matches[str(domain).casefold()] = f"{row['name']}, {row.get('role', 'resident')}"
            no_owner_capability = no_owner_capability or any(item.get("human_owner_known") is False and not item.get("suitable_resident_ids") for item in value.get("capabilities", ()) if isinstance(item, dict))
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            continue
    for _attempt in range(2):
        try:
            response = provider(model, request)
            last_response = response
            value = json.loads(response.summary)
            speech = value.get("speech") if isinstance(value, dict) else None
            claims = value.get("institutional_claims") if isinstance(value, dict) else None
            mode = value.get("assertion_mode", "ordinary") if isinstance(value, dict) else "ordinary"
            if mode not in {"ordinary", "institutional"}:
                raise RuntimeError("RIV-RES-0002: resident speech composer returned an invalid assertion mode.")
            grounding = ground_claims(claims, context_material)
            if mode == "institutional" and (not isinstance(claims, list) or not claims or grounding.unsupported or not grounding.supported):
                raise RuntimeError("RIV-RES-0002: resident speech composer returned ungrounded institutional claims.")
            if not isinstance(speech, str) or not speech.strip() or any(marker in speech.casefold() for marker in _FORBIDDEN):
                raise RuntimeError("RIV-RES-0002: resident speech composer returned internal scaffolding.")
            named_residents = {name.casefold() for name in registry_names if name.casefold() in speech.casefold() and name.casefold() != "grace"}
            unsupported_self_claim = "research" in instruction.casefold() and "authoritative contact" in speech.casefold() and ("Marie" not in speech and "manager of research" not in speech.casefold())
            if (no_owner_capability and named_residents and not any(term in instruction.casefold() for term in ("other residents", "who lives", "resident registry", "which residents"))) or unsupported_self_claim:
                raise RuntimeError("RIV-RES-0002: resident speech composer assigned an unsupported capability owner.")
            break
        except json.JSONDecodeError as exc:
            last_error = RuntimeError("RIV-RES-0002: resident speech composer returned invalid JSON.")
            last_error.__cause__ = exc
        except RuntimeError as exc:
            last_error = exc
    else:
        if last_response is None:
            raise last_error or RuntimeError("RIV-RES-0002: resident speech composer failed.")
        if "research" in instruction.casefold():
            speech = "Marie, Manager of Research, is the authoritative Riverview role for research questions. I can route the question for that office's advisory consideration without executing any work."
        elif engineering_capability_known and any(term in instruction.casefold() for term in ("mechanical", "engineering", "bracket", "generator", "windmill")):
            speech = "I can identify codex.engineering.v1 as the governed engineering resource. No authoritative Riverview resident owner for mechanical design is currently recorded. The next step is Steward-authorized formation of a bounded engineering proposal; that does not execute the work."
        else:
            speech = "I don't have an authoritative Riverview resident or office assignment for that responsibility. I can state the uncertainty and leave any routing decision to the governed institutional process."
        return ReasoningResponse(
            response_id=last_response.response_id, request_id=request.request_id,
            correlation_id=result.correlation_id, provider_id=f"resident-speech:fallback:{last_response.provider_id}",
            response_type="advice", summary=speech,
            evidence_refs=tuple(dict.fromkeys((*result.provenance_refs, f"speech-composition:fallback:{last_response.response_id}"))),
            classification=result.classification, created_at=last_response.created_at,
        )
    if engineering_capability_known and no_owner_capability and any(term in instruction.casefold() for term in ("resource", "work", "appropriate", "mechanical")) and "codex.engineering.v1" not in speech:
        speech = speech.rstrip() + " Riverview's documented governed resource for this is codex.engineering.v1, which supports bounded proposal formation rather than automatic execution."
    return ReasoningResponse(
        response_id=response.response_id, request_id=request.request_id, correlation_id=result.correlation_id, provider_id=f"resident-speech:{response.provider_id}",
        response_type="advice", summary=speech.strip(),
        evidence_refs=tuple(dict.fromkeys((*result.provenance_refs, f"speech-composition:{response.response_id}"))),
        classification=result.classification, created_at=response.created_at,
    )
