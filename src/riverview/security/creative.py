"""Classification-aware creative routing without payload processing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreativeRoute:
    provider_id: str
    storage_classification: str
    protected_reference_only: bool


def select_creative_route(classification: str, provider_id: str) -> CreativeRoute:
    if classification == "adult-local":
        if not provider_id.startswith("local:"):
            raise PermissionError("RIV-CHAR-0003: adult-local creative route is local-only.")
        return CreativeRoute(provider_id, classification, True)
    if classification not in {"public", "operational", "private"}:
        raise PermissionError("RIV-CHAR-0003: creative classification is denied.")
    return CreativeRoute(provider_id, classification, False)
