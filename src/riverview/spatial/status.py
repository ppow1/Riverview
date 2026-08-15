"""Read-only spatial status projection."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SpatialStatus:
    services: tuple[str, ...]
    diagnostics: tuple[str, ...]
    objectives: tuple[str, ...]
    capacity: tuple[str, ...]


def project_status(*, services: tuple[str, ...], diagnostics: tuple[str, ...], objectives: tuple[str, ...], capacity: tuple[str, ...]) -> SpatialStatus:
    return SpatialStatus(services, diagnostics, objectives, capacity)
