"""Synthetic adult-local routing policy; no payload processing."""

from __future__ import annotations

from dataclasses import dataclass

from riverview.classification import Classification


@dataclass(frozen=True, slots=True)
class AdultLocalDecision:
    allowed: bool
    provider_id: str
    reason: str

def route_adult_local(classification: Classification, provider_id: str, *, synthetic: bool) -> AdultLocalDecision:
    if classification is not Classification.ADULT_LOCAL:
        return AdultLocalDecision(False, provider_id, "classification_not_adult_local")
    if not synthetic:
        return AdultLocalDecision(False, provider_id, "real_activation_requires_steward")
    if not provider_id.startswith("local:"):
        return AdultLocalDecision(False, provider_id, "provider_not_local")
    return AdultLocalDecision(True, provider_id, "synthetic_local_only")
