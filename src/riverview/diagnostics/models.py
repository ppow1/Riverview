"""Typed diagnostic event contract for the Riverview Kernel.

Version: 0.1.2
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4


class Severity(StrEnum):
    """Diagnostic severity values."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecoveryState(StrEnum):
    """Recovery lifecycle for a diagnostic event."""

    UNVERIFIED = "unverified"
    DIAGNOSED = "diagnosed"
    REPAIRING = "repairing"
    RECOVERED = "recovered"
    ESCALATED = "escalated"


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    """Immutable first-pass diagnostic event emitted at a stable checkpoint."""

    checkpoint_id: str
    component: str
    operation: str
    severity: Severity
    failure_class: str
    summary: str
    cookbook_entry: str
    workflow_id: UUID | None = None
    attempt: int = 1
    evidence_refs: tuple[str, ...] = ()
    dependency_state: Mapping[str, Any] = field(default_factory=dict)
    recovery_state: RecoveryState = RecoveryState.UNVERIFIED
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.checkpoint_id.startswith("RIV-"):
            raise ValueError("checkpoint_id must begin with 'RIV-'")
        if self.attempt < 1:
            raise ValueError("attempt must be at least 1")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        object.__setattr__(self, "dependency_state", MappingProxyType(dict(self.dependency_state)))

    def as_record(self) -> dict[str, Any]:
        """Return a database/transport-safe record."""

        return {
            "checkpoint_id": self.checkpoint_id,
            "event_id": str(self.event_id),
            "component": self.component,
            "operation": self.operation,
            "workflow_id": str(self.workflow_id) if self.workflow_id else None,
            "attempt": self.attempt,
            "severity": self.severity.value,
            "failure_class": self.failure_class,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
            "dependency_state": dict(self.dependency_state),
            "cookbook_entry": self.cookbook_entry,
            "recovery_state": self.recovery_state.value,
            "occurred_at": self.occurred_at.isoformat(),
        }
