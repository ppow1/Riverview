"""Bounded Playwright doorbell contract for RV-008.3 preparation.

Version: 0.1.0

This module defines a future browser adapter without opening a browser,
handling credentials, scraping conversations, or claiming live acceptance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class DoorbellRequest:
    request_id: UUID
    correlation_id: UUID
    conversation_selector: str
    mailbox_resource: str
    timeout_seconds: int = 30

    def __post_init__(self) -> None:
        if not self.conversation_selector.strip() or not self.mailbox_resource.strip():
            raise ValueError(
                "RIV-PLY-0001: conversation selector and mailbox resource are required."
            )
        if not 1 <= self.timeout_seconds <= 300:
            raise ValueError("RIV-PLY-0001: doorbell timeout is outside the bounded range.")


@dataclass(frozen=True, slots=True)
class DoorbellResult:
    request_id: UUID
    correlation_id: UUID
    state: str
    observed_at: datetime
    evidence_ref: str | None
    failure_class: str | None = None


class DoorbellAdapter(Protocol):
    """Named adapter boundary; implementations require separate Steward acceptance."""

    def ring(self, request: DoorbellRequest) -> DoorbellResult: ...


class LocalAcceptanceDoorbell:
    """Deterministic harness used to test the boundary without a browser."""

    def __init__(self, *, induced_failure: bool = False) -> None:
        self.induced_failure = induced_failure

    def ring(self, request: DoorbellRequest) -> DoorbellResult:
        if self.induced_failure:
            return DoorbellResult(
                request.request_id,
                request.correlation_id,
                "failed",
                datetime.now(UTC),
                "acceptance://doorbell/induced-timeout",
                "bounded-timeout",
            )
        return DoorbellResult(
            request.request_id,
            request.correlation_id,
            "prepared",
            datetime.now(UTC),
            "acceptance://doorbell/prepared-only",
        )


def acceptance_request() -> DoorbellRequest:
    """Create a safe local request for deterministic adapter tests."""
    request_id = uuid4()
    return DoorbellRequest(request_id, uuid4(), "designated-conversation", "riverview://mailbox")
