"""Resident-generic HOME cognition over the occupational capability broker.

This is the resident-facing continuation seam. Identity, occupancy, and
implementation are read from resident continuity authority; package activation
is deterministic configuration derived from that binding; occupational tool
selection remains entirely with the model callback.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
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
    },
    "required": ["decision", "answer", "capability_id", "arguments"],
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

    def execute(self, profile: ResidentProfile, question: str, *, correlation_id: UUID, conversation_context: tuple[str, ...] = ()) -> ResidentHomeTurn:
        state = self.state_resolver.resolve(profile)
        package = self._package(profile, state)
        bound_model = str(state.implementation.get("model_ref") or self.model_ref)
        provider_ref = str(state.implementation.get("provider_ref") or "ollama")
        provider_id = f"{provider_ref}:{bound_model}"
        resource_ref = str(state.implementation.get("device_ref") or "local:RTX4090")
        if provider_ref != "ollama":
            raise RuntimeError("RIV-HOME-0002: resident implementation provider is not Ollama")
        def model(payload: Mapping[str, Any]) -> Mapping[str, Any]:
            phase = str(payload["phase"])
            catalog = payload.get("capability_catalog", package.catalog()) if phase == "first" else []
            tool_result = payload.get("tool_result")
            if tool_result is not None:
                tool_result = json.loads(json.dumps(tool_result, default=str))
                if isinstance(tool_result, dict) and isinstance(tool_result.get("value"), dict):
                    value = tool_result["value"]
                    if len(json.dumps(value, default=str)) > 8_000:
                        tool_result["value"] = {"bounded_result": "authoritative result exceeded continuation display bound; consult the capability status and evidence references", "evidence_refs": tool_result.get("evidence_refs", [])}
            request = ReasoningRequest(
                request_id=uuid4(), correlation_id=correlation_id, request_type="advice",
                instruction=json.dumps({"phase": phase, "question": question, "resident": {"id": str(state.resident_id), "name": state.resident_name, "title": state.title, "office_id": str(state.office_id), "authority_ref": state.authority_ref}, "conversation_context": list(conversation_context)[-4:], "capability_catalog": catalog, "available_capability_ids": [item.get("capability_id") for item in catalog], "tool_result": tool_result, "policy": "Qwen chooses capabilities; Riverview only validates and executes the named request. Return structured JSON; do not expose private reasoning. Use a capability when the Steward requests or clearly needs current authoritative Riverview or professional information, including questions about current work, progress, blockers, CME, resources, submissions, diagnostics, attention, or accepted character state. For a direct question asking what is established or known about a named resident, the first pass must use character.canon.read with a typed target_resident argument; do not answer from the base packet. Do not claim that authoritative character information is absent merely because it is not in the base packet; retrieve it through the catalog first. For an underspecified physical or other artifact request, ask only for missing domain parameters such as dimensions, tolerances, locations, interfaces, material, or acceptance criteria; do not ask whether to use an internal capability. Do not merely offer to invoke an internal capability and wait for the Steward to operate your toolbox. Never claim institutional access to a system, repository, file, resource, or capability unless it is represented in this active catalog or returned by an authoritative result; when it is absent, say that direct access is not currently available and identify only the bounded capabilities that are actually present. Generic knowledge of a system is not access. In ordinary conversation describe abilities naturally rather than dumping internal capability IDs; expose IDs only when explicitly requested for technical diagnostics or architecture. Greetings, pleasantries, compliments, personal household statements, and ordinary social conversation require decision=answer with no capability unless the user explicitly asks for operational or character-architecture work. When the Steward explicitly asks to prepare a governed engineering request or character proposal, select the corresponding PROPOSE capability and provide its typed arguments; do not answer as if preparation occurred without invoking that capability."}, separators=(",", ":")),
                context_refs=state.evidence_refs + state.state_refs + package.provenance_refs,
                classification=state.classification, required_output_schema="resident-home-occupational-v1",
                evidence_requirements=("resident-state", "package", "capability-selection", "provider-pass"),
                expires_at=datetime.now(UTC) + timedelta(minutes=5), allowed_authority=("read:bounded", "return:advisory"), response_format=_DECISION_FORMAT,
            )
            response = self.provider(bound_model, request)
            try:
                value = json.loads(response.summary)
            except (json.JSONDecodeError, TypeError) as exc:
                raise RuntimeError("RIV-HOME-0002: Qwen returned malformed structured HOME decision") from exc
            if not isinstance(value, dict):
                raise RuntimeError("RIV-HOME-0002: Qwen HOME decision is not an object")
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
        return ResidentHomeTurn(uuid4(), uuid4(), correlation_id, state, package, run, provider_id, bound_model, resource_ref)

    def _package(self, profile: ResidentProfile, state: AuthoritativeResidentState) -> ResidentOfficeCapabilityPackage:
        if profile.name.casefold() == "grace":
            return build_grace_operations_package(profile, state.office_id, state.implementation_id, self.profiles)
        if profile.name.casefold() == "jessica":
            return build_jessica_character_package(profile, state.office_id, state.implementation_id, self.character_store, self.profiles)
        raise RuntimeError("RIV-HOME-0003: no authoritative occupational package is activated for resident")
