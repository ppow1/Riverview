"""Stable provider-neutral reasoning envelopes.

ChatGPT is an adapter, not part of the mailbox or Grace kernel contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

CONTRACT_VERSION = "riverview-reasoning-v1"
REQUEST_TYPES = frozenset({"advice", "analysis", "decision_proposal", "diagnostic"})
RESPONSE_TYPES = frozenset({"advice", "analysis", "decision_proposal", "escalation", "diagnostic_recommendation"})
SEMANTIC_OUTCOMES = frozenset({"CONTINUE", "OBJECTIVE_COMPLETE", "COMPLETED_NO_ATTENTION", "READY_FOR_STEWARD_REVIEW", "BLOCKED_REQUIRES_STEWARD", "STEWARD_DECISION_REQUIRED", "RETRYABLE_FAILURE", "TERMINAL_FAILURE"})
ALLOWED_CLASSIFICATIONS = frozenset({"public", "operational", "private", "river", "internal"})
MAX_INSTRUCTION = 16_000
MAX_SUMMARY = 8_000
MAX_REFS = 32


def _bounded_text(value: str, name: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"RIV-REASON-0001: {name} is missing or exceeds its bound.")
    return value.strip()


@dataclass(frozen=True, slots=True)
class ReasoningProvider:
    participant_id: str
    provider_id: str
    provider_type: str
    role: str
    capabilities: tuple[str, ...]
    eligible_classifications: tuple[str, ...]
    contract_version: str = CONTRACT_VERSION
    health: str = "unknown"
    capacity: int = 0

    def __post_init__(self) -> None:
        _bounded_text(self.participant_id, "participant_id", 200)
        _bounded_text(self.provider_id, "provider_id", 200)
        _bounded_text(self.provider_type, "provider_type", 100)
        if "openai" in self.provider_id.lower() or "openai" in self.provider_type.lower():
            raise ValueError("RIV-REASON-0001: OpenAI API model routes are not registered.")
        if not self.capabilities or not all(isinstance(item, str) and item.strip() for item in self.capabilities):
            raise ValueError("RIV-REASON-0001: provider capabilities are required.")
        if not set(self.eligible_classifications) <= ALLOWED_CLASSIFICATIONS:
            raise ValueError("RIV-SEC-0001: provider classification eligibility is closed.")
        if self.health not in {"unknown", "healthy", "unhealthy", "disabled"} or self.capacity < 0:
            raise ValueError("RIV-REASON-0001: provider health or capacity is invalid.")


@dataclass(frozen=True, slots=True)
class ReasoningRequest:
    request_id: UUID
    correlation_id: UUID
    request_type: str
    instruction: str
    context_refs: tuple[str, ...]
    classification: str
    required_output_schema: str
    evidence_requirements: tuple[str, ...]
    expires_at: datetime
    allowed_authority: tuple[str, ...]
    causation_id: UUID | None = None
    objective_id: UUID | None = None
    stage_id: UUID | None = None
    contract_version: str = CONTRACT_VERSION
    response_format: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.request_type not in REQUEST_TYPES:
            raise ValueError("RIV-REASON-0001: request type is unsupported.")
        _bounded_text(self.instruction, "instruction", MAX_INSTRUCTION)
        _bounded_text(self.required_output_schema, "required_output_schema", 200)
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError("RIV-SEC-0001: request classification is closed.")
        if len(self.context_refs) > MAX_REFS or len(self.evidence_requirements) > MAX_REFS:
            raise ValueError("RIV-REASON-0001: reference count exceeds its bound.")
        if not all(isinstance(item, str) and item.strip() for item in (*self.context_refs, *self.evidence_requirements)):
            raise ValueError("RIV-REASON-0001: references must be non-empty strings.")
        if not self.allowed_authority or any(item not in {"read:bounded", "return:advisory", "return:diagnostic"} for item in self.allowed_authority):
            raise ValueError("RIV-REASON-0001: authority is not an allowed reasoning capability.")
        if self.response_format is not None and not isinstance(self.response_format, dict):
            raise ValueError("RIV-REASON-0001: response format must be a bounded object.")


@dataclass(frozen=True, slots=True)
class ReasoningResponse:
    response_id: UUID
    request_id: UUID
    correlation_id: UUID
    provider_id: str
    response_type: str
    summary: str
    evidence_refs: tuple[str, ...]
    classification: str
    created_at: datetime
    contract_version: str = CONTRACT_VERSION
    semantic_outcome: str | None = None
    objective_disposition: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.response_type not in RESPONSE_TYPES:
            raise ValueError("RIV-REASON-0001: response type is unsupported.")
        _bounded_text(self.provider_id, "provider_id", 200)
        _bounded_text(self.summary, "summary", MAX_SUMMARY)
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError("RIV-SEC-0001: response classification is closed.")
        if self.semantic_outcome is not None and self.semantic_outcome not in SEMANTIC_OUTCOMES:
            raise ValueError("RIV-REASON-0001: semantic outcome is unsupported.")
        if self.objective_disposition is not None:
            if not isinstance(self.objective_disposition, dict):
                raise ValueError("RIV-REASON-0001: objective disposition must be an object.")
            if self.objective_disposition.get("disposition", self.objective_disposition.get("outcome")) not in SEMANTIC_OUTCOMES:
                raise ValueError("RIV-REASON-0001: objective disposition is unsupported.")
        if not 1 <= len(self.evidence_refs) <= MAX_REFS or not all(
            isinstance(item, str) and item.strip() for item in self.evidence_refs
        ):
            raise ValueError("RIV-REASON-0001: response evidence references are required and bounded.")

    def as_typed_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.contract_version,
            "response_id": str(self.response_id),
            "request_id": str(self.request_id),
            "correlation_id": str(self.correlation_id),
            "provider_id": self.provider_id,
            "response_type": self.response_type,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
            "classification": self.classification,
            "created_at": self.created_at.isoformat(),
            "semantic_outcome": self.semantic_outcome,
            "objective_disposition": self.objective_disposition,
        }
