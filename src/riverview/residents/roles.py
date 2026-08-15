"""Role context is advisory and cannot grant operational capabilities."""

from __future__ import annotations

from dataclasses import dataclass

from .registry import ResidentRecord


@dataclass(frozen=True, slots=True)
class RoleContext:
    resident_id: str
    role: str
    allowed_tools: tuple[str, ...]
    voice_style: str


def build_role_context(record: ResidentRecord, *, allowed_tools: tuple[str, ...] = ()) -> RoleContext:
    blocked = {"shell", "sql", "roadmap_mutation", "provider_control", "protected_data"}
    safe_tools = tuple(tool for tool in allowed_tools if tool not in blocked)
    return RoleContext(
        resident_id=record.resident_id,
        role=record.role or "unknown",
        allowed_tools=safe_tools,
        voice_style="advisory",
    )
