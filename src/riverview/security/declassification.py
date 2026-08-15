"""Explicit synthetic promotion/declassification decision boundary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeclassificationRequest:
    object_reference: str
    current_classification: str
    target_classification: str
    authority_identity: str
    purpose: str
    audit_reference: str


def authorize_declassification(request: DeclassificationRequest, *, approved: bool) -> str:
    if not all(
        value.strip()
        for value in (
            request.object_reference,
            request.current_classification,
            request.target_classification,
            request.authority_identity,
            request.purpose,
            request.audit_reference,
        )
    ):
        raise ValueError("RIV-SEC-0005: declassification evidence is incomplete.")
    if not approved:
        raise PermissionError("RIV-SEC-0005: declassification denied without explicit approval.")
    return request.object_reference
