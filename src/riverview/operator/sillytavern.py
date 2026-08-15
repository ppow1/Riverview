"""Bounded SillyTavern-shaped adapter over the provider-neutral contract."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from riverview.reasoning import ReasoningRequest, ReasoningResponse
from riverview.residents.registry import ResidentRecord
from riverview.residents.roles import build_role_context


@dataclass(frozen=True, slots=True)
class SillyTavernSession:
    session_id: UUID
    resident_id: str
    classification: str
    provider_id: str


def ask_sillytavern(
    record: ResidentRecord,
    *,
    provider_id: str,
    classification: str,
    correlation_id: UUID,
    instruction: str,
    provider: Callable[[ReasoningRequest], ReasoningResponse],
) -> tuple[SillyTavernSession, ReasoningResponse]:
    if classification not in {"public", "operational", "private", "adult-local"}:
        raise PermissionError("RIV-CHAR-0001: creative classification is denied.")
    if classification == "adult-local" and not provider_id.startswith("local:"):
        raise PermissionError("RIV-CHAR-0001: protected creative work requires a local provider.")
    context = build_role_context(record, allowed_tools=("advisory_reasoning", "creative_context"))
    request = ReasoningRequest(
        request_id=uuid4(),
        correlation_id=correlation_id,
        request_type="advice",
        instruction=f"Role {context.role}; advisory creative context. {instruction}",
        context_refs=(record.canonical_reference,),
        classification="private" if classification == "adult-local" else classification,
        required_output_schema="creative-advice-v1",
        evidence_requirements=("resident-reference", "correlation"),
        expires_at=datetime.now(UTC),
        allowed_authority=("read:bounded", "return:advisory"),
    )
    response = provider(request)
    if response.correlation_id != correlation_id:
        raise RuntimeError("RIV-CHAR-0001: provider correlation mismatch.")
    return SillyTavernSession(uuid4(), record.resident_id, classification, provider_id), response
