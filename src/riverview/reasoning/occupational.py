"""Generic resident occupational capability package and broker.

This module owns deterministic capability enforcement only. It does not infer
intent, select capabilities from natural language, own authoritative data, or
replace any Riverview workflow. Handlers are injected adapters over existing
authoritative services.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Callable, Mapping
from uuid import UUID, uuid4
from .epistemic import EpistemicSpan, ProvenanceRecord, build_epistemic_metadata

MAX_ARGUMENT_BYTES = 16_000
MAX_RESULT_BYTES = 32_000
MAX_CAPABILITY_CALLS = 8


class CapabilityResultStatus(StrEnum):
    SUCCESS = "SUCCESS"
    EMPTY_AUTHORITATIVE_RESULT = "EMPTY_AUTHORITATIVE_RESULT"
    UNAVAILABLE = "UNAVAILABLE"
    DENIED = "DENIED"
    STALE = "STALE"
    TIMEOUT = "TIMEOUT"
    MALFORMED = "MALFORMED"
    BACKEND_FAILURE = "BACKEND_FAILURE"


class CapabilityAuthority(StrEnum):
    READ = "READ"
    ADVISE = "ADVISE"
    PROPOSE = "PROPOSE"


class CapabilityUnavailableError(RuntimeError):
    """The authoritative capability is temporarily unavailable."""


class CapabilityStaleError(RuntimeError):
    """The authoritative capability result is stale for this request."""


@dataclass(frozen=True, slots=True)
class ResidentCapabilityRequest:
    request_id: UUID
    correlation_id: UUID
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    package_id: str
    package_version: str
    capability_id: str
    arguments: Mapping[str, Any]
    classification: str
    authority: str
    call_index: int
    call_budget: int

    def __post_init__(self) -> None:
        for value, name in ((self.request_id, "request_id"), (self.correlation_id, "correlation_id"), (self.resident_id, "resident_id"), (self.occupant_id, "occupant_id"), (self.office_id, "office_id"), (self.implementation_id, "implementation_id")):
            if not isinstance(value, UUID):
                raise ValueError(f"RIV-OCC-0001: {name} must be a UUID.")
        for value, name in ((self.package_id, "package_id"), (self.package_version, "package_version"), (self.capability_id, "capability_id"), (self.classification, "classification"), (self.authority, "authority")):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"RIV-OCC-0001: {name} is required.")
        if not isinstance(self.arguments, Mapping) or len(json.dumps(self.arguments, default=str).encode()) > MAX_ARGUMENT_BYTES:
            raise ValueError("RIV-OCC-0001: capability arguments are invalid or oversized.")
        if self.call_budget < 1 or self.call_budget > MAX_CAPABILITY_CALLS or self.call_index < 1:
            raise ValueError("RIV-OCC-0001: capability call budget is invalid.")


@dataclass(frozen=True, slots=True)
class ResidentCapabilityDescriptor:
    capability_id: str
    capability_version: str
    name: str
    purpose: str
    authority_class: str
    input_schema: Mapping[str, Any]
    result_schema: Mapping[str, Any]
    handler: Callable[[ResidentCapabilityRequest], Mapping[str, Any]]
    classification: str
    freshness_seconds: int
    timeout_seconds: int
    max_result_bytes: int
    evidence_requirements: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, name in ((self.capability_id, "capability_id"), (self.capability_version, "capability_version"), (self.name, "name"), (self.purpose, "purpose"), (self.classification, "classification")):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"RIV-OCC-0002: {name} is required.")
        if self.authority_class not in {item.value for item in CapabilityAuthority}:
            raise ValueError("RIV-OCC-0002: capability authority class is invalid.")
        if not isinstance(self.input_schema, Mapping) or not isinstance(self.result_schema, Mapping):
            raise ValueError("RIV-OCC-0002: capability schemas are required.")
        if not callable(self.handler):
            raise ValueError("RIV-OCC-0002: authoritative handler is required.")
        if self.freshness_seconds < 0 or not 1 <= self.timeout_seconds <= 300 or not 1 <= self.max_result_bytes <= MAX_RESULT_BYTES:
            raise ValueError("RIV-OCC-0002: capability bounds are invalid.")
        if not self.evidence_requirements or not all(isinstance(item, str) and item.strip() for item in self.evidence_requirements):
            raise ValueError("RIV-OCC-0002: evidence requirements are required.")

    def catalog_entry(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "capability_version": self.capability_version,
            "name": self.name,
            "purpose": self.purpose,
            "authority_class": self.authority_class,
            "input_schema": dict(self.input_schema),
            "result_type": self.result_schema.get("type", "object"),
            "classification": self.classification,
            "freshness_seconds": self.freshness_seconds,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True, slots=True)
class ResidentCapabilityResult:
    result_id: UUID
    request_id: UUID
    correlation_id: UUID
    capability_id: str
    capability_version: str
    status: CapabilityResultStatus
    value: Mapping[str, Any] | None
    reason: str | None
    evidence_refs: tuple[str, ...]
    observed_at: datetime
    authoritative: bool = True

    def as_payload(self) -> dict[str, Any]:
        return {
            "result_id": str(self.result_id),
            "request_id": str(self.request_id),
            "correlation_id": str(self.correlation_id),
            "capability_id": self.capability_id,
            "capability_version": self.capability_version,
            "status": self.status.value,
            "value": dict(self.value) if self.value is not None else None,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
            "observed_at": self.observed_at.isoformat(),
            "authoritative": self.authoritative,
        }


@dataclass(frozen=True, slots=True)
class ResidentOfficeCapabilityPackage:
    package_id: str
    package_version: str
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    resident_name: str
    title: str
    office_purpose: str
    responsibilities: tuple[str, ...]
    professional_domain_refs: tuple[str, ...]
    domain_knowledge_refs: tuple[str, ...]
    capabilities: tuple[ResidentCapabilityDescriptor, ...]
    authority_boundaries: tuple[str, ...]
    procedure_refs: tuple[str, ...]
    classification: str
    freshness_seconds: int
    grounding_policy: str
    privacy_policy: str
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, name in ((self.package_id, "package_id"), (self.package_version, "package_version"), (self.resident_name, "resident_name"), (self.title, "title"), (self.office_purpose, "office_purpose"), (self.classification, "classification"), (self.grounding_policy, "grounding_policy"), (self.privacy_policy, "privacy_policy")):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"RIV-OCC-0003: {name} is required.")
        for value, name in ((self.resident_id, "resident_id"), (self.occupant_id, "occupant_id"), (self.office_id, "office_id"), (self.implementation_id, "implementation_id")):
            if not isinstance(value, UUID):
                raise ValueError(f"RIV-OCC-0003: {name} must be a UUID.")
        if self.resident_id != self.occupant_id or self.freshness_seconds < 0:
            raise ValueError("RIV-OCC-0003: package identity or capabilities are invalid.")
        ids = [item.capability_id for item in self.capabilities]
        if len(ids) != len(set(ids)):
            raise ValueError("RIV-OCC-0003: capability IDs must be unique within a package.")
        if not self.authority_boundaries or not self.provenance_refs:
            raise ValueError("RIV-OCC-0003: package authority and provenance are required.")

    def catalog(self) -> list[dict[str, Any]]:
        return [item.catalog_entry() for item in self.capabilities]


class ResidentCapabilityBroker:
    """Deterministic broker for model-selected package capabilities."""

    def __init__(self, package: ResidentOfficeCapabilityPackage):
        self.package = package

    def execute(self, request: ResidentCapabilityRequest) -> ResidentCapabilityResult:
        base = dict(result_id=uuid4(), request_id=request.request_id, correlation_id=request.correlation_id, capability_id=request.capability_id, capability_version=request.package_version, observed_at=datetime.now(UTC))
        if (request.resident_id, request.occupant_id, request.office_id, request.implementation_id) != (self.package.resident_id, self.package.occupant_id, self.package.office_id, self.package.implementation_id):
            return ResidentCapabilityResult(**base, status=CapabilityResultStatus.DENIED, value=None, reason="resident/occupant/office/implementation mismatch", evidence_refs=self.package.provenance_refs)
        if (request.package_id, request.package_version) != (self.package.package_id, self.package.package_version):
            return ResidentCapabilityResult(**base, status=CapabilityResultStatus.DENIED, value=None, reason="capability package mismatch", evidence_refs=self.package.provenance_refs)
        if request.call_index > request.call_budget:
            return ResidentCapabilityResult(**base, status=CapabilityResultStatus.DENIED, value=None, reason="capability call budget exhausted", evidence_refs=self.package.provenance_refs)
        descriptor = next((item for item in self.package.capabilities if item.capability_id == request.capability_id), None)
        if descriptor is None:
            return ResidentCapabilityResult(**base, status=CapabilityResultStatus.DENIED, value=None, reason="capability is not allowlisted", evidence_refs=self.package.provenance_refs)
        base["capability_version"] = descriptor.capability_version
        if request.classification != descriptor.classification or request.authority not in self.package.authority_boundaries:
            return ResidentCapabilityResult(**base, status=CapabilityResultStatus.DENIED, value=None, reason="classification or authority is not permitted", evidence_refs=self.package.provenance_refs)
        try:
            value = descriptor.handler(request)
        except CapabilityUnavailableError as exc:
            return ResidentCapabilityResult(**base, status=CapabilityResultStatus.UNAVAILABLE, value=None, reason=str(exc) or "authoritative capability unavailable", evidence_refs=descriptor.evidence_requirements)
        except CapabilityStaleError as exc:
            return ResidentCapabilityResult(**base, status=CapabilityResultStatus.STALE, value=None, reason=str(exc) or "authoritative capability result is stale", evidence_refs=descriptor.evidence_requirements)
        except TimeoutError:
            return ResidentCapabilityResult(**base, status=CapabilityResultStatus.TIMEOUT, value=None, reason="authoritative capability timed out", evidence_refs=descriptor.evidence_requirements)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            reason = str(exc).replace("\r", " ").replace("\n", " ").strip()[:240] or type(exc).__name__
            return ResidentCapabilityResult(**base, status=CapabilityResultStatus.BACKEND_FAILURE, value=None, reason=f"authoritative capability failed: {type(exc).__name__}: {reason}", evidence_refs=descriptor.evidence_requirements)
        if not isinstance(value, Mapping):
            return ResidentCapabilityResult(**base, status=CapabilityResultStatus.MALFORMED, value=None, reason="authoritative handler returned a non-object result", evidence_refs=descriptor.evidence_requirements)
        if len(json.dumps(value, default=str).encode()) > descriptor.max_result_bytes:
            return ResidentCapabilityResult(**base, status=CapabilityResultStatus.MALFORMED, value=None, reason="capability result exceeds its bound", evidence_refs=descriptor.evidence_requirements)
        evidence = tuple(dict.fromkeys((*descriptor.evidence_requirements, *(str(item) for item in value.get("evidence_refs", ()) if str(item).strip()))))
        clean_value = {key: item for key, item in value.items() if key != "evidence_refs"}
        status = CapabilityResultStatus.EMPTY_AUTHORITATIVE_RESULT if not clean_value or clean_value.get("items") == [] else CapabilityResultStatus.SUCCESS
        return ResidentCapabilityResult(**base, status=status, value=clean_value, reason=None if status is CapabilityResultStatus.SUCCESS else "authoritative query returned no records", evidence_refs=evidence)


@dataclass(frozen=True, slots=True)
class ResidentOccupationalRun:
    correlation_id: UUID
    first_decision: Mapping[str, Any]
    tool_result: ResidentCapabilityResult | None
    final_answer: str
    model_passes: int
    epistemic: dict[str, Any] | None = None


def _epistemic(value: Mapping[str, Any], answer: str) -> dict[str, Any] | None:
    raw = value.get("epistemic_spans")
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ValueError("RIV-OCC-0005: epistemic spans must be an array.")
    spans = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError("RIV-OCC-0005: epistemic span must be an object.")
        provenance = []
        for record in item.get("provenance", ()):
            if not isinstance(record, Mapping):
                raise ValueError("RIV-OCC-0005: epistemic provenance must be an object.")
            provenance.append(ProvenanceRecord(source_class=str(record.get("source_class", "")), evidence_ref=str(record.get("evidence_ref", "")), freshness=record.get("freshness"), capability=record.get("capability"), source_refs=tuple(str(x) for x in record.get("source_refs", ()))))
        spans.append(EpistemicSpan(span_id=str(item.get("span_id", "")), start=int(item.get("start", -1)), end=int(item.get("end", -1)), mask=int(item.get("mask", -1)), provenance=tuple(provenance)))
    return build_epistemic_metadata(spans, response_text=answer)


class ResidentOccupationalReasoner:
    """Run model decision -> bounded capability -> model synthesis."""

    def __init__(self, package: ResidentOfficeCapabilityPackage, model: Callable[[Mapping[str, Any]], Mapping[str, Any]], *, call_budget: int = 2):
        if not callable(model):
            raise ValueError("RIV-OCC-0004: occupational model callback is required.")
        if not 1 <= call_budget <= MAX_CAPABILITY_CALLS:
            raise ValueError("RIV-OCC-0004: occupational call budget is invalid.")
        self.package = package
        self.model = model
        self.call_budget = call_budget
        self.broker = ResidentCapabilityBroker(package)

    def run(self, question: str, *, correlation_id: UUID, conversation_context: tuple[str, ...] = ()) -> ResidentOccupationalRun:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("RIV-OCC-0004: occupational question is required.")
        first = self._model({
            "phase": "first", "question": question.strip(), "conversation_context": list(conversation_context),
            "resident": {"resident_id": str(self.package.resident_id), "occupant_id": str(self.package.occupant_id), "office_id": str(self.package.office_id), "title": self.package.title},
            "professional_context_refs": list(self.package.professional_domain_refs + self.package.domain_knowledge_refs + self.package.procedure_refs),
            "capability_catalog": self.package.catalog(),
        })
        extra_passes = 0
        if first.get("decision") == "answer" and (first.get("_contract_missing") or first.get("assertion_mode") == "institutional" or first.get("claims")):
            first = self._model({
                "phase": "repair", "question": question.strip(), "conversation_context": list(conversation_context),
                "resident": {"resident_id": str(self.package.resident_id), "occupant_id": str(self.package.occupant_id), "office_id": str(self.package.office_id), "title": self.package.title},
                "capability_catalog": self.package.catalog(),
                "previous_answer": first.get("answer"),
                "instructions": "The prior answer declared an institutional assertion without authoritative evidence. Reconsider the meaning using the capability catalog. Return decision=capability with typed arguments for the needed authoritative read, or decision=answer only if the question is not an institutional assertion.",
            })
            extra_passes = 1
        capability_id = first.get("capability_id")
        decision = first.get("decision")
        if decision == "answer":
            if first.get("assertion_mode") is not None or first.get("claims") is not None:
                review = self._model({"phase": "review", "question": question.strip(), "conversation_context": list(conversation_context), "resident": {"resident_id": str(self.package.resident_id), "office_id": str(self.package.office_id), "title": self.package.title}, "capability_catalog": self.package.catalog(), "proposed_answer": first.get("answer"), "assertion_mode": first.get("assertion_mode"), "claims": first.get("claims", []), "instructions": "Reassess the proposed answer epistemically. Mutable or institutional facts require authoritative evidence: select the appropriate capability with typed arguments. Stable general or social questions may remain decision=answer with assertion_mode=general and claims=[]. Do not guess identifiers or acceptance."})
                reviewed_id = review.get("capability_id")
                if review.get("decision") == "capability" and isinstance(reviewed_id, str) and reviewed_id.strip():
                    first, capability_id, decision, extra_passes = review, reviewed_id, "capability", 1
                else:
                    answer = self._answer(review)
                    return ResidentOccupationalRun(correlation_id, review, None, answer, 2, _epistemic(review, answer))
            else:
                answer = self._answer(first)
                return ResidentOccupationalRun(correlation_id, first, None, answer, 1, _epistemic(first, answer))
        if decision != "capability":
            raise ValueError("RIV-OCC-0005: model decision must be answer or capability.")
        arguments = first.get("arguments", {})
        if not isinstance(capability_id, str) or not capability_id.strip() or not isinstance(arguments, Mapping):
            raise ValueError("RIV-OCC-0005: model capability request is malformed.")
        descriptor = next((item for item in self.package.capabilities if item.capability_id == capability_id), None)
        authority = "read:bounded" if descriptor is None or descriptor.authority_class == CapabilityAuthority.READ.value else "return:advisory"
        request = ResidentCapabilityRequest(
            request_id=uuid4(), correlation_id=correlation_id, resident_id=self.package.resident_id,
            occupant_id=self.package.occupant_id, office_id=self.package.office_id,
            implementation_id=self.package.implementation_id, package_id=self.package.package_id,
            package_version=self.package.package_version, capability_id=capability_id,
            arguments=dict(arguments), classification=self.package.classification, authority=authority,
            call_index=1, call_budget=self.call_budget,
        )
        tool_result = self.broker.execute(request)
        if tool_result.status is CapabilityResultStatus.BACKEND_FAILURE and self.call_budget >= 2:
            repair = self._model({
                "phase": "repair", "question": question.strip(), "conversation_context": list(conversation_context),
                "resident": {"resident_id": str(self.package.resident_id), "occupant_id": str(self.package.occupant_id), "office_id": str(self.package.office_id), "title": self.package.title},
                "capability_catalog": self.package.catalog(), "previous_capability_request": {"capability_id": capability_id, "arguments": dict(arguments)},
                "tool_result": tool_result.as_payload(),
                "instructions": "Repair the same named capability request using the authoritative failure reason and exact active input schema. Return decision=capability with complete typed arguments, or decision=answer only when the capability cannot be repaired without missing legitimate domain information. Do not substitute another capability.",
            })
            repaired_id = repair.get("capability_id")
            repaired_args = repair.get("arguments", {})
            if isinstance(repaired_id, str) and repaired_id.strip() and isinstance(repaired_args, Mapping) and repaired_id == capability_id:
                repaired_request = ResidentCapabilityRequest(
                    request_id=uuid4(), correlation_id=correlation_id, resident_id=self.package.resident_id,
                    occupant_id=self.package.occupant_id, office_id=self.package.office_id,
                    implementation_id=self.package.implementation_id, package_id=self.package.package_id,
                    package_version=self.package.package_version, capability_id=repaired_id,
                    arguments=dict(repaired_args), classification=self.package.classification, authority=authority,
                    call_index=2, call_budget=self.call_budget,
                )
                tool_result = self.broker.execute(repaired_request)
        second = self._model({
            "phase": "second", "question": question.strip(), "conversation_context": list(conversation_context),
            "resident": {"resident_id": str(self.package.resident_id), "occupant_id": str(self.package.occupant_id), "office_id": str(self.package.office_id), "title": self.package.title},
            "tool_result": tool_result.as_payload(),
            "instructions": "This is the mandatory final continuation pass. Do not request another capability. Reason over the authoritative capability result, distinguish canon from unknown/proposal, and return decision=answer with a natural resident-facing answer only.",
        })
        if second.get("decision") not in {"answer", "synthesis"}:
            raise ValueError("RIV-OCC-0005: second model pass must synthesize an answer.")
        answer = self._answer(second)
        return ResidentOccupationalRun(correlation_id, first, tool_result, answer, 2 + extra_passes, _epistemic(second, answer))

    def _model(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        value = self.model(payload)
        if not isinstance(value, Mapping):
            raise ValueError("RIV-OCC-0005: model decision is not an object.")
        return value

    @staticmethod
    def _answer(value: Mapping[str, Any]) -> str:
        answer = value.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("RIV-OCC-0005: model answer is missing.")
        return answer.strip()
