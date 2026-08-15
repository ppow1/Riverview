"""Reference-only Undercurrent broker; ordinary River callers are denied."""

from __future__ import annotations

from dataclasses import dataclass

from riverview.classification import Classification, StorageReference


@dataclass(frozen=True, slots=True)
class AccessDecision:
    allowed: bool
    caller: str
    capability: str
    purpose: str
    reference_id: str
    reason: str


class ProtectedAccessBroker:
    """Fail-closed decision boundary without retrieving protected payloads."""

    def decide(self, reference: StorageReference, *, caller: str, capability: str, purpose: str) -> AccessDecision:
        if reference.classification is not Classification.UNDERCURRENT:
            return AccessDecision(False, caller, capability, purpose, reference.reference_id, "not a protected reference")
        if not caller.strip() or not capability.strip() or not purpose.strip():
            return AccessDecision(False, caller, capability, purpose, reference.reference_id, "identity, capability, and purpose are required")
        if capability != "undercurrent:bounded-read":
            return AccessDecision(False, caller, capability, purpose, reference.reference_id, "capability denied")
        return AccessDecision(True, caller, capability, purpose, reference.reference_id, "authorized reference decision; payload remains outside River")
