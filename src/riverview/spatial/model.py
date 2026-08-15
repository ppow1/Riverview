"""Logical spatial model; it never changes operational ownership."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SpatialEntity:
    entity_id: str
    kind: str
    label: str
    state: str
    provenance: str

    def __post_init__(self) -> None:
        if self.state not in {"KNOWN", "PROPOSED", "UNKNOWN", "CONFIGURATION_DERIVED"}:
            raise ValueError("RIV-SPAT-0001: spatial state is closed.")
        if not all(value.strip() for value in (self.entity_id, self.kind, self.label, self.provenance)):
            raise ValueError("RIV-SPAT-0001: spatial entity metadata is incomplete.")


class SpatialProjection:
    """Bounded read-only projection with no mutation/control methods."""

    def __init__(self, entities: tuple[SpatialEntity, ...] = ()) -> None:
        self._entities = tuple(entities)

    def entities(self) -> tuple[SpatialEntity, ...]:
        return self._entities

    def by_kind(self, kind: str) -> tuple[SpatialEntity, ...]:
        return tuple(entity for entity in self._entities if entity.kind == kind)
