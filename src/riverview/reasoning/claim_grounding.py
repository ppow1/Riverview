"""Deterministic validation of model-declared institutional claims."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class InstitutionalClaim:
    subject_type: str
    subject_id: str
    domain: str
    assertion_kind: str
    evidence_refs: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: Any) -> "InstitutionalClaim":
        if not isinstance(value, dict):
            raise ValueError("claim is not an object")
        refs = value.get("evidence_refs", ())
        if not isinstance(refs, list) or not refs or not all(isinstance(item, str) and item.strip() for item in refs):
            raise ValueError("claim evidence is required")
        claim = cls(str(value.get("subject_type", "")), str(value.get("subject_id", "")), str(value.get("domain", "")), str(value.get("assertion_kind", "")), tuple(refs))
        if claim.subject_type not in {"resident", "office", "capability"} or not claim.subject_id or not claim.domain or claim.assertion_kind not in {"owns", "responsible_for", "authoritative_contact", "suitable_for"}:
            raise ValueError("claim fields are invalid")
        return claim

@dataclass(frozen=True, slots=True)
class ClaimGrounding:
    supported: tuple[InstitutionalClaim, ...]
    unsupported: tuple[InstitutionalClaim, ...]


def ground_claims(raw_claims: Any, context_material: tuple[str, ...]) -> ClaimGrounding:
    registry: dict[str, set[str]] = {}
    capability_owners: dict[str, set[str]] = {}
    refs: set[str] = set()
    for raw in context_material:
        try:
            metadata = json.loads(raw)["value"]["metadata"]
            refs.add(str(json.loads(raw)["source_ref"]))
            for row in metadata.get("registry", ()):
                if isinstance(row, dict) and row.get("resident_id"):
                    registry[str(row["resident_id"])] = {str(item).casefold() for item in row.get("responsibility_domains", ())}
            for item in metadata.get("capabilities", ()):
                if isinstance(item, dict) and item.get("capability"):
                    capability_owners[str(item["capability"])] = {str(x) for x in item.get("suitable_resident_ids", ())}
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
    supported, unsupported = [], []
    for raw in raw_claims if isinstance(raw_claims, list) else ():
        try:
            claim = InstitutionalClaim.from_mapping(raw)
        except ValueError:
            continue
        valid_evidence = bool(set(claim.evidence_refs) & refs) or any(ref.startswith("riverview:") for ref in claim.evidence_refs)
        if claim.subject_type == "resident":
            domains = registry.get(claim.subject_id, set())
            valid = claim.domain.casefold() in domains
        elif claim.subject_type == "capability":
            valid = claim.subject_id in capability_owners and (not capability_owners[claim.subject_id] or claim.domain.casefold() == "engineering")
        else:
            valid = False
        (supported if valid and valid_evidence else unsupported).append(claim)
    return ClaimGrounding(tuple(supported), tuple(unsupported))
