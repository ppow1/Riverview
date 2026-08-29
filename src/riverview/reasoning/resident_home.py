"""Resident-generic HOME cognition over the occupational capability broker.

This is the resident-facing continuation seam. Identity, occupancy, and
implementation are read from resident continuity authority; package activation
is deterministic configuration derived from that binding; occupational tool
selection remains entirely with the model callback.
"""
from __future__ import annotations

import json
import hashlib
from time import monotonic
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, Mapping, TYPE_CHECKING
from uuid import UUID, uuid4

from riverview.characters.store import CharacterStore
from riverview.residents.occupational_packages import build_grace_operations_package, build_jessica_character_package
from riverview.residents.persistence import ResidentContinuityStore

if TYPE_CHECKING:
    from riverview.residents.gateway import ResidentProfile

from .contracts import ReasoningRequest, ReasoningResponse
from .occupational import ResidentCapabilityResult, ResidentOfficeCapabilityPackage, ResidentOccupationalReasoner, ResidentOccupationalRun

_DECISION_FORMAT = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": ["answer", "capability", "synthesis"]},
        "answer": {"type": ["string", "null"]},
        "capability_id": {"type": ["string", "null"]},
        "arguments": {"type": "object"},
        "assertion_mode": {"type": "string", "enum": ["general", "institutional"]},
        "scope": {"type": "string", "enum": ["resident_local", "institutional_broad"]},
        "claims": {"type": "array", "maxItems": 4, "items": {"type": "object", "properties": {"span_id": {"type": "string", "minLength": 1, "maxLength": 120}, "claim_text": {"type": "string", "minLength": 1, "maxLength": 400}, "assertion_kind": {"type": "string", "enum": ["verified_fact", "authoritative_fact", "canonical_fact", "canonical_identity", "resident_canon"]}}, "required": ["span_id", "claim_text", "assertion_kind"], "additionalProperties": False}},
        "epistemic_spans": {"type": "array", "maxItems": 32, "items": {"type": "object", "properties": {"span_id": {"type": "string", "minLength": 1, "maxLength": 120}, "start": {"type": "integer", "minimum": 0}, "end": {"type": "integer", "minimum": 1}, "mask": {"type": "integer", "minimum": 1, "maximum": 63}, "evidence_choice_ids": {"type": "array", "maxItems": 8, "items": {"type": "integer", "minimum": 0}}, "provenance": {"type": "array", "maxItems": 8, "items": {"type": "object", "properties": {"source_class": {"type": "string", "enum": ["institutional", "live_telemetry", "postgresql", "river", "local_artifact", "repository", "steward", "canon", "external_authoritative", "web_research", "cross_validation"]}, "evidence_ref": {"type": "string", "minLength": 1, "maxLength": 240}, "observed_at": {"type": ["string", "null"]}, "freshness": {"type": ["string", "null"]}, "capability": {"type": ["string", "null"]}, "source_refs": {"type": "array", "maxItems": 8, "items": {"type": "string"}}}, "required": ["source_class", "evidence_ref", "observed_at", "freshness", "capability", "source_refs"], "additionalProperties": False}}}, "required": ["span_id", "start", "end", "mask", "evidence_choice_ids"], "additionalProperties": False}},
    },
    "required": ["decision", "answer", "capability_id", "arguments", "assertion_mode", "scope", "claims", "epistemic_spans"],
    "additionalProperties": False,
}


def _unsupported_access_claim(answer: str, catalog: list[dict[str, Any]]) -> bool:
    text = answer.casefold()
    access_claim = any(phrase in text for phrase in ("i can read", "i can access", "i have access", "i'm capable of reading", "i am capable of reading"))
    institutional_target = any(term in text for term in ("github", "repository", "local file", "filesystem", "shell", "sql database"))
    available = " ".join(f"{item.get('capability_id', '')} {item.get('purpose', '')}".casefold() for item in catalog)
    return access_claim and institutional_target and not any(term in available for term in ("github", "repository", "filesystem", "shell", "sql database"))


@dataclass(frozen=True, slots=True)
class AuthoritativeResidentState:
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    resident_name: str
    title: str
    authority_ref: str
    classification: str
    character_version: str | None
    continuity_refs: tuple[str, ...]
    state_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    implementation: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ResidentHomeTurn:
    user_turn_id: UUID
    cognition_session_id: UUID
    correlation_id: UUID
    state: AuthoritativeResidentState
    package: ResidentOfficeCapabilityPackage
    run: ResidentOccupationalRun
    provider_id: str
    model_ref: str
    resource_ref: str
    provider_calls: tuple[dict[str, Any], ...] = ()

    def metadata(self) -> dict[str, Any]:
        result = self.run.tool_result
        return {
            "home_cognition": True,
            "resident_generic": True,
            "user_turn_id": str(self.user_turn_id),
            "cognition_session_id": str(self.cognition_session_id),
            "cognition_correlation_id": str(self.correlation_id),
            "resident_id": str(self.state.resident_id),
            "occupant_id": str(self.state.occupant_id),
            "office_id": str(self.state.office_id),
            "implementation_id": str(self.state.implementation_id),
            "package_id": self.package.package_id,
            "package_version": self.package.package_version,
            "model_passes": self.run.model_passes,
            "selected_capability": result.capability_id if result else None,
            "tool_status": result.status.value if result else None,
            "tool_request_id": str(result.request_id) if result else None,
            "tool_result_id": str(result.result_id) if result else None,
            "tool_evidence_refs": list(result.evidence_refs) if result else [],
            "provider": self.provider_id.split(":", 1)[0] if ":" in self.provider_id else self.provider_id,
            "model": self.model_ref,
            "resource": self.resource_ref,
            "first_pass": "completed",
            "second_pass": "completed" if self.run.model_passes == 2 else None,
            "authority_scope": ["return:advisory"],
            "role_authority_expanded": False,
            "epistemic": self.run.epistemic,
            "provider_calls": list(self.provider_calls),
        }


class ResidentHomeStateResolver:
    """Resolve one active resident without synthetic identity fallback."""

    def __init__(self, store: ResidentContinuityStore | None = None):
        self.store = store or ResidentContinuityStore()

    def resolve(self, profile: ResidentProfile) -> AuthoritativeResidentState:
        try:
            projection = self.store.rehydration_projection(UUID(profile.resident_id))
        except (LookupError, RuntimeError, ValueError) as exc:
            raise RuntimeError("RIV-HOME-0001: authoritative resident projection unavailable") from exc
        occupant = projection.get("occupant") or {}
        occupancy = projection.get("occupancy") or {}
        bindings = projection.get("bindings") or []
        if occupant.get("display_name") != profile.name or occupant.get("status") != "active":
            raise RuntimeError("RIV-HOME-0001: resident identity is not active and canonical")
        if len(bindings) != 1:
            raise RuntimeError("RIV-HOME-0001: exactly one active resident implementation binding is required")
        binding = bindings[0]
        if not occupancy or not binding.get("implementation_id"):
            raise RuntimeError("RIV-HOME-0001: resident occupancy or implementation is unavailable")
        claims = projection.get("claims") or []
        title = str(occupancy.get("title") or profile.role)
        authority_ref = str(occupancy.get("authority_envelope_ref") or "")
        if not authority_ref:
            raise RuntimeError("RIV-HOME-0001: resident authority envelope is unavailable")
        character_version = None
        for claim in claims:
            if claim.get("predicate") == "character_version" and claim.get("status") == "accepted":
                character_version = str(claim.get("value"))
        return AuthoritativeResidentState(
            resident_id=UUID(str(occupant["occupant_id"])), occupant_id=UUID(str(occupant["occupant_id"])),
            office_id=UUID(str(occupancy["office_id"])), implementation_id=UUID(str(binding["implementation_id"])),
            resident_name=str(occupant["display_name"]), title=title, authority_ref=authority_ref,
            classification=str(occupant.get("classification") or profile.classification), character_version=character_version,
            continuity_refs=tuple(f"continuity:{item.get('state_id', item.get('provenance_id', 'unknown'))}" for item in projection.get("state_records", []) if item.get("state_class") in {"reflection_renewal", "episodic_institutional_history"}),
            state_refs=tuple(str(item.get("state_id")) for item in projection.get("state_records", []) if item.get("state_id")),
            evidence_refs=tuple(dict.fromkeys((str(occupant.get("provenance_id")), str(occupancy.get("provenance_id")), str(binding.get("binding_id"))))),
            implementation=binding,
        )


class ResidentHomeCognitionService:
    """Resident-generic HOME first pass, broker call, and continuation pass."""

    def __init__(self, *, profiles: tuple[ResidentProfile, ...], provider: Callable[[str, ReasoningRequest], ReasoningResponse], model_ref: str, character_store: CharacterStore | None = None, state_resolver: ResidentHomeStateResolver | None = None):
        self.profiles = profiles
        self.provider = provider
        self.model_ref = model_ref
        self.character_store = character_store or CharacterStore.from_profiles(profiles)
        self.state_resolver = state_resolver or ResidentHomeStateResolver()
        self.last_provider_calls: tuple[dict[str, Any], ...] = ()

    def execute(self, profile: ResidentProfile, question: str, *, correlation_id: UUID, conversation_context: tuple[str, ...] = (), conversation_id: UUID | None = None) -> ResidentHomeTurn:
        state = self.state_resolver.resolve(profile)
        package = self._package(profile, state)
        package = replace(package, provenance_refs=tuple(dict.fromkeys((*state.evidence_refs, *state.state_refs, *package.provenance_refs))))
        bound_model = str(state.implementation.get("model_ref") or self.model_ref)
        provider_ref = str(state.implementation.get("provider_ref") or "ollama")
        provider_id = f"{provider_ref}:{bound_model}"
        resource_ref = str(state.implementation.get("device_ref") or "local:RTX4090")
        if provider_ref != "ollama":
            raise RuntimeError("RIV-HOME-0002: resident implementation provider is not Ollama")
        turn_id = uuid4()
        provider_calls: list[dict[str, Any]] = []
        self.last_provider_calls = ()
        def model(payload: Mapping[str, Any]) -> Mapping[str, Any]:
            phase = str(payload["phase"])
            catalog = payload.get("capability_catalog", package.catalog()) if phase in {"first", "repair"} else []
            operational_context = []
            if phase == "first" and profile.name.casefold() == "grace":
                try:
                    from riverview.closed_loop.now_projection import read_now_roots
                    operational_context = [{key: (str(item.get(key))[:600] if key == "latest_result_summary" else item.get(key)) for key in ("root_task_id", "title", "state", "current_checkpoint", "binding_state", "current_actor", "current_executor", "resource", "semantic_outcome", "latest_result_summary", "attention_required") if item.get(key) is not None} for item in read_now_roots()["items"][:8]]
                except (LookupError, RuntimeError, ValueError):
                    operational_context = []
            tool_result = payload.get("tool_result")
            if tool_result is not None:
                tool_result = json.loads(json.dumps(tool_result, default=str))
                if isinstance(tool_result, dict) and isinstance(tool_result.get("value"), dict):
                    value = tool_result["value"]
                    if len(json.dumps(value, default=str)) > 8_000:
                        tool_result["value"] = {"bounded_result": "authoritative result exceeded continuation display bound; consult the capability status and evidence references", "evidence_refs": tool_result.get("evidence_refs", [])}
            evidence_catalog = []
            for handle in dict.fromkeys((*state.evidence_refs, *state.state_refs, *(tool_result or {}).get("evidence_refs", ()), *package.provenance_refs)):
                evidence_catalog.append({"handle": str(handle), "display_label": "Authoritative evidence handle supplied for this turn", "source_class": "institutional", "capability": (tool_result or {}).get("capability_id"), "freshness": "current"})
            response_format = json.loads(json.dumps(payload.get("response_format") or _DECISION_FORMAT))
            if evidence_catalog:
                response_format["properties"]["epistemic_spans"]["items"]["properties"]["provenance"]["items"]["properties"]["evidence_ref"]["enum"] = [item["handle"] for item in evidence_catalog]
            request = ReasoningRequest(
                request_id=uuid4(), correlation_id=correlation_id, request_type="advice",
                instruction=json.dumps({"phase": phase, "question": question, "resident": {"id": str(state.resident_id), "name": state.resident_name, "title": state.title, "office_id": str(state.office_id), "authority_ref": state.authority_ref}, "conversation_context": list(conversation_context)[-4:], "capability_catalog": catalog, "available_capability_ids": [item.get("capability_id") for item in catalog], "authoritative_current_work_context": operational_context, "tool_result": tool_result, "available_evidence": evidence_catalog, "available_evidence_handles_exact": [item["handle"] for item in evidence_catalog], "policy": "For phase=first or phase=repair, if decision=answer, return routing context only: assertion_mode=general, claims=[], epistemic_spans=[]; never attach final factual labels in a routing pass. For any request about the broader resident registry, resident inventory, who else is resident, or office associations, the authoritative capability is institutional.resident-registry.read; select it whenever the question asks for that broader state, even if the current resident context mentions only the speaker. Do not answer from bounded resident context or claim the registry is exhaustive without the capability result. phase=second/review may return the final synthesis. Qwen selects capabilities semantically; Riverview validates typed requests. Never invent identifiers or acceptance. General/social questions may be answered without a tool. Epistemic integrity is claim-centric: every epistemic span must have a claims item with the same span_id; claim_text must be copied exactly from answer[start:end]. Every VERIFIED/CANON span additionally requires its matching typed authoritative/canonical claim and supplied evidence_choice_ids. If no matching claim and supplied evidence can be produced, emit no VERIFIED/CANON span; use REASONED, GENERAL, CREATIVE, or UNKNOWN truthfully. evidence_choice_ids MUST contain only integer indexes into available_evidence_handles_exact; Riverview resolves choices to authoritative provenance. Do not emit evidence_ref for a choice-based span and do not invent evidence references or private reasoning."}, default=str, separators=(",", ":")),
                context_refs=state.evidence_refs + state.state_refs + package.provenance_refs,
                classification=state.classification, required_output_schema="resident-home-occupational-v1",
                evidence_requirements=("resident-state", "package", "capability-selection", "provider-pass"),
                expires_at=datetime.now(UTC) + timedelta(minutes=5), allowed_authority=("read:bounded", "return:advisory"), response_format=response_format,
            )
            call_id = uuid4()
            started = monotonic()
            schema_json = json.dumps(response_format, sort_keys=True, separators=(",", ":"))
            record = {"provider_call_id": str(call_id), "turn_id": str(turn_id), "conversation_id": str(conversation_id) if conversation_id else None, "resident_id": str(state.resident_id), "correlation_id": str(correlation_id), "request_id": str(request.request_id), "phase": phase, "attempt": len(provider_calls) + 1, "started_at": datetime.now(UTC).isoformat(), "provider": provider_ref, "model": bound_model, "resource": resource_ref, "schema_id": f"{request.required_output_schema}:{hashlib.sha256(schema_json.encode()).hexdigest()[:16]}", "structured_output": request.response_format is not None}
            try:
                response = self.provider(bound_model, request)
                record.update({"ended_at": datetime.now(UTC).isoformat(), "duration_ms": round((monotonic() - started) * 1000, 2), "status": "success", "failure_class": None, "error": None})
                provider_calls.append(record)
                self.last_provider_calls = tuple(provider_calls)
            except Exception as exc:
                record.update({"ended_at": datetime.now(UTC).isoformat(), "duration_ms": round((monotonic() - started) * 1000, 2), "status": "failure", "failure_class": type(exc).__name__, "error": str(exc)[:240]})
                provider_calls.append(record)
                self.last_provider_calls = tuple(provider_calls)
                raise
            try:
                value = json.loads(response.summary)
            except (json.JSONDecodeError, TypeError) as exc:
                if phase == "structured_repair":
                    raise RuntimeError("RIV-HOME-0002: Qwen structured-output repair remained malformed") from exc
                repair_request = replace(request, request_id=uuid4(), instruction=json.dumps({"phase": "structured_repair", "schema": _DECISION_FORMAT, "parse_error": str(exc)[:240], "malformed_output": response.summary[:8000], "instructions": "Return ONLY one complete JSON object conforming to the supplied schema. Repair syntax only; preserve the substantive answer and epistemic metadata. Do not add commentary, markdown fences, or invented evidence references."}, default=str, separators=(",", ":")))
                repaired = self.provider(bound_model, repair_request)
                try:
                    value = json.loads(repaired.summary)
                except (json.JSONDecodeError, TypeError) as repair_error:
                    raise RuntimeError("RIV-HOME-0002: Qwen structured-output repair remained malformed") from repair_error
            if not isinstance(value, dict):
                raise RuntimeError("RIV-HOME-0002: Qwen HOME decision is not an object")
            if provider_calls:
                provider_calls[-1]["structured_summary"] = {"answer_chars": len(value.get("answer")) if isinstance(value.get("answer"), str) else None, "assertion_mode": value.get("assertion_mode"), "claim_count": len(value.get("claims", ())) if isinstance(value.get("claims"), list) else None, "span_count": len(value.get("epistemic_spans", ())) if isinstance(value.get("epistemic_spans"), list) else None, "span_masks": [item.get("mask") for item in value.get("epistemic_spans", ()) if isinstance(item, Mapping)][:32], "span_ids": [item.get("span_id") for item in value.get("epistemic_spans", ()) if isinstance(item, Mapping)][:32], "claim_span_ids": [item.get("span_id") for item in value.get("claims", ()) if isinstance(item, Mapping)][:32], "evidence_choice_counts": [len(item.get("evidence_choice_ids", ())) for item in value.get("epistemic_spans", ()) if isinstance(item, Mapping)][:32]}
                self.last_provider_calls = tuple(provider_calls)
            if phase == "first" and ("assertion_mode" not in value or "claims" not in value):
                value = {**value, "_contract_missing": True}
            return value
        run = ResidentOccupationalReasoner(package, model).run(question, correlation_id=correlation_id, conversation_context=conversation_context)
        if run.tool_result is None and _unsupported_access_claim(run.final_answer, package.catalog()):
            correction = model({
                "phase": "validation",
                "tool_result": {"status": "UNAVAILABLE", "value": {"available_capabilities": package.catalog()}, "reason": "claimed institutional access is not present in the active resident package"},
            })
            if correction.get("decision") not in {"answer", "synthesis"}:
                raise RuntimeError("RIV-HOME-0004: capability claim correction did not synthesize an answer")
            run = ResidentOccupationalRun(run.correlation_id, run.first_decision, None, ResidentOccupationalReasoner._answer(correction), 2)
        return ResidentHomeTurn(uuid4(), uuid4(), correlation_id, state, package, run, provider_id, bound_model, resource_ref, tuple(provider_calls))

    def _package(self, profile: ResidentProfile, state: AuthoritativeResidentState) -> ResidentOfficeCapabilityPackage:
        if profile.name.casefold() == "grace":
            return build_grace_operations_package(profile, state.office_id, state.implementation_id, self.profiles)
        if profile.name.casefold() == "jessica":
            return build_jessica_character_package(profile, state.office_id, state.implementation_id, self.character_store, self.profiles)
        raise RuntimeError("RIV-HOME-0003: no authoritative occupational package is activated for resident")
