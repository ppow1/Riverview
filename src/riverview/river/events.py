"""Immutable River event contract.

Version: 0.2.0
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4


class Classification(StrEnum):
    """Initial routing classifications; Undercurrent never uses ordinary River storage."""

    RIVER = "river"
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True)
class RiverEvent:
    """A single immutable fact accepted by The River."""

    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    idempotency_key: str
    payload: Mapping[str, Any]
    correlation_id: UUID = field(default_factory=uuid4)
    causation_id: UUID | None = None
    classification: Classification = Classification.RIVER
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        for name in ("event_type", "aggregate_type", "idempotency_key"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))