"""Resident office capability packages built from existing Riverview services.

Packages are derived adapters. PostgreSQL, CharacterStore, CME, Comms5, and
Operator projections remain authoritative; this module only assembles bounded
named descriptors for a resident cognitive workspace.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TYPE_CHECKING
from uuid import UUID

from riverview.characters.store import CharacterStore
if TYPE_CHECKING:
    from riverview.residents.gateway import ResidentProfile

from riverview.reasoning.occupational import ResidentCapabilityDescriptor, ResidentCapabilityRequest, ResidentOfficeCapabilityPackage


def _limit(request: ResidentCapabilityRequest, default: int = 12) -> int:
    value = request.arguments.get("limit", default)
    return max(1, min(int(value), 50)) if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def _grace_work(request: ResidentCapabilityRequest) -> dict[str, Any]:
    from riverview.operator.hermes_projection import read_campaign_runner_snapshot
    snapshot = read_campaign_runner_snapshot(limit=_limit(request))
    return {"items": snapshot.get("items", []), "source": snapshot.get("source", "postgresql:campaign_runner"), "evidence_refs": ["postgresql:campaign_runner", "riverview://work-orders"]}


def _grace_cme(request: ResidentCapabilityRequest) -> dict[str, Any]:
    from riverview.autonomy.runtime import CMEStatusStore
    value = CMEStatusStore().read()
    return {"status": value or {"status": "not_observed"}, "evidence_refs": ["riverview://cme-runtime-status"]}


def _grace_resources(request: ResidentCapabilityRequest) -> dict[str, Any]:
    from riverview.mcp.comms5 import Comms5Service
    value = Comms5Service().resource_policy_status()
    return {"policy": value.get("policy"), "resources": value.get("resources", []), "claims": value.get("claims", []), "evidence_refs": ["postgresql:resource_policy", "riverview://codex-fleet"]}


def _grace_comms(request: ResidentCapabilityRequest) -> dict[str, Any]:
    from riverview.mcp.comms5 import Comms5Service
    return {"submissions": Comms5Service().recent_steward_submissions(limit=_limit(request)).get("items", []), "evidence_refs": ["postgresql:comms5_seed_drafts", "riverview://comms5"]}


def _grace_cookbook(request: ResidentCapabilityRequest) -> dict[str, Any]:
    from riverview.database import connect
    term = str(request.arguments.get("query", "")).strip()
    with connect() as connection, connection.cursor() as cursor:
        if term:
            like = f"%{term}%"
            cursor.execute("SELECT checkpoint_id,title,summary,diagnostic_procedure,repair_procedure,recovery_verification,source_path,validation_state FROM cookbook_entries WHERE title ILIKE %s OR summary ILIKE %s ORDER BY updated_at DESC LIMIT %s", (like, like, _limit(request)))
        else:
            cursor.execute("SELECT checkpoint_id,title,summary,diagnostic_procedure,repair_procedure,recovery_verification,source_path,validation_state FROM cookbook_entries ORDER BY updated_at DESC LIMIT %s", (_limit(request),))
        rows = [dict(zip(("checkpoint_id", "title", "summary", "diagnostic_procedure", "repair_procedure", "recovery_verification", "source_path", "validation_state"), row, strict=True)) for row in cursor.fetchall()]
    return {"items": rows, "evidence_refs": ["postgresql:cookbook_entries", "riverview://cookbook"]}


def _grace_responsibility(request: ResidentCapabilityRequest, profiles: tuple[ResidentProfile, ...]) -> dict[str, Any]:
    query = str(request.arguments.get("query", "")).casefold()
    rows = [{"resident_id": p.resident_id, "name": p.name, "role": p.role, "classification": p.classification, "canonical_reference": p.canonical_reference} for p in profiles if not query or query in p.name.casefold() or query in p.role.casefold()]
    return {"items": rows[:_limit(request)], "evidence_refs": ["riverview://resident-registry"]}


def _jessica_character(request: ResidentCapabilityRequest, store: CharacterStore, profiles: tuple[ResidentProfile, ...]) -> dict[str, Any]:
    target = str(request.arguments.get("resident_id", "")).strip()
    if not target:
        target = str(request.arguments.get("resident", "")).strip()
    if not target:
        target = str(request.arguments.get("target_resident", "")).strip()
    profile = next((p for p in profiles if p.resident_id == target or p.name.casefold() == target.casefold()), None)
    store_id = profile.resident_id if profile else target
    if not store_id:
        return {"target_resident_id": None, "character": None, "unknown": "target resident was not supplied", "evidence_refs": ["character-store:current"]}
    try:
        current = store.current(store_id)
    except LookupError:
        return {"target_resident_id": store_id, "character": None, "unknown": "no accepted character canon is established for this target", "evidence_refs": ["character-store:current"]}
    return {"target_resident_id": current["resident_id"], "character": current, "evidence_refs": tuple(current.get("source_evidence", ())) or ("character-store:current",)}


def _jessica_versions(request: ResidentCapabilityRequest, store: CharacterStore) -> dict[str, Any]:
    target = str(request.arguments.get("resident_id", "")).strip() or "grace"
    return {"versions": [v for v in store.data.get("versions", []) if v.get("resident_id") == target], "evidence_refs": ["character-store:versions"]}


def _jessica_proposals(request: ResidentCapabilityRequest, store: CharacterStore) -> dict[str, Any]:
    target = str(request.arguments.get("resident_id", "")).strip() or "grace"
    return {"proposals": store.proposals(target), "evidence_refs": ["character-store:proposals"]}


def _descriptor(capability_id: str, name: str, purpose: str, handler: Any, *, classification: str, authority: str = "READ", input_schema: dict[str, Any] | None = None, evidence: tuple[str, ...] = ()) -> ResidentCapabilityDescriptor:
    return ResidentCapabilityDescriptor(capability_id, "1.0.0", name, purpose, authority, input_schema or {"type": "object"}, {"type": "object"}, handler, classification, 300, 15, 24_000, evidence or (f"capability:{capability_id}",))


def build_grace_operations_package(profile: ResidentProfile, office_id: UUID, implementation_id: UUID, profiles: tuple[ResidentProfile, ...]) -> ResidentOfficeCapabilityPackage:
    capabilities = (
        _descriptor("operations.current-work.read", "Current work", "Read bounded active, ready, blocked, stale, and recent work projections.", _grace_work, classification=profile.classification, evidence=("postgresql:campaign_runner",)),
        _descriptor("operations.cme.read", "CME state", "Read current Continuous Momentum Engine health, cursor, progress, and attention state.", _grace_cme, classification=profile.classification, evidence=("riverview://cme-runtime-status",)),
        _descriptor("operations.resources.read", "Resources", "Read fresh bounded resource, capacity, policy, and claim metadata.", _grace_resources, classification=profile.classification, evidence=("postgresql:resource_policy",)),
        _descriptor("operations.comms5.lineage.read", "Comms5 lineage", "Read recent governed submissions and lineage metadata.", _grace_comms, classification=profile.classification, evidence=("riverview://comms5",)),
        _descriptor("operations.cookbook.lookup", "Cookbook", "Lookup bounded troubleshooting and recovery knowledge.", _grace_cookbook, classification=profile.classification, input_schema={"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}}, evidence=("postgresql:cookbook_entries",)),
        _descriptor("operations.responsibility.read", "Responsibilities", "Read resident and office responsibility metadata.", lambda request: _grace_responsibility(request, profiles), classification=profile.classification, evidence=("riverview://resident-registry",)),
    )
    return ResidentOfficeCapabilityPackage("grace-operations-v1", "1.0.0", UUID(profile.resident_id), UUID(profile.resident_id), UUID(str(office_id)), UUID(str(implementation_id)), profile.name, profile.role, "Coordinate bounded Riverview operations and progression.", ("observe operational state", "advise on progression", "prepare governed proposals"), ("riverview://office/operations",), ("riverview://cme-runtime-status", "riverview://capability/codex.engineering.v1"), capabilities, ("read:bounded", "return:advisory"), ("cookbook://operations",), profile.classification, 300, "institutional evidence outranks generic priors", "bounded operational metadata only", ("grace-authority:v1", "resident-continuity:operations"))


def build_jessica_character_package(profile: ResidentProfile, office_id: UUID, implementation_id: UUID, store: CharacterStore, profiles: tuple[ResidentProfile, ...]) -> ResidentOfficeCapabilityPackage:
    capabilities = (
        _descriptor("character.canon.read", "Accepted character canon", "Read the accepted character state for a named target resident.", lambda request: _jessica_character(request, store, profiles), classification=profile.classification, input_schema={"type": "object", "properties": {"target_resident": {"type": "string", "description": "Authoritative resident name or resident ID."}}, "required": ["target_resident"], "additionalProperties": False}, evidence=("character-store:current",)),
        _descriptor("character.versions.read", "Character versions", "Read bounded accepted version history for a target resident.", lambda request: _jessica_versions(request, store), classification=profile.classification, input_schema={"type": "object", "properties": {"target_resident": {"type": "string"}}, "required": ["target_resident"], "additionalProperties": False}, evidence=("character-store:versions",)),
        _descriptor("character.proposals.read", "Character proposals", "Read proposals and review/publication status without publishing.", lambda request: _jessica_proposals(request, store), classification=profile.classification, input_schema={"type": "object", "properties": {"target_resident": {"type": "string"}}, "required": ["target_resident"], "additionalProperties": False}, evidence=("character-store:proposals",)),
    )
    return ResidentOfficeCapabilityPackage("jessica-character-architecture-v1", "1.0.0", UUID(profile.resident_id), UUID(profile.resident_id), UUID(str(office_id)), UUID(str(implementation_id)), profile.name, profile.role, "Recover, inspect, and develop character architecture within governed review boundaries.", ("inspect character canon", "classify evidence", "prepare bounded proposals"), ("riverview://office/character-architecture",), ("character-store:current", "character-store:proposals"), capabilities, ("read:bounded", "return:advisory"), ("character://inspection",), profile.classification, 300, "accepted canon outranks proposal, observation, and generic priors", "bounded character metadata only", ("jessica-workflow:v1", "resident-continuity:character-architecture"))
