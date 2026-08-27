"""Authoritative PostgreSQL projection for Grace HOME cognition."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import UUID

from riverview.autonomy.runtime import CMEStatusStore
from riverview.residents.context import AssignmentContext, BudgetSpec, ContextItem, PostgresContextSource, ResidentContextAssembler
from riverview.residents.persistence import ResidentContinuityStore, stable_id

from .home_cognition import AuthoritativeGraceState, AuthoritativeGraceStateSource, HomeCognitionExecutionError

GRACE_OCCUPANT_ID = stable_id("occupant:grace")
GRACE_OFFICE_ID = stable_id("office:operations")
GRACE_IMPLEMENTATION_ID = stable_id("implementation:grace-home-cognition:qwen3-coder-30b:ollama-4090")
GRACE_AUTHORITY_REF = "grace:authority-envelope:director-of-operations:v1"
GRACE_CONTEXT_STATE_KEY = "state:grace:home-cognition:authority-context:v1"
GRACE_BINDING_PURPOSE = "HOME_COGNITION"


class _GraceProjectionSource:
    """Context-source adapter that preserves one validated read projection."""

    def __init__(self, store: ResidentContinuityStore, projection: dict[str, Any]) -> None:
        self.store = store
        self.projection = projection

    def rehydration_projection(self, occupant_id: UUID) -> dict[str, Any]:
        if occupant_id != GRACE_OCCUPANT_ID:
            raise LookupError("Grace projection requested for a different occupant.")
        return self.projection

    def health(self) -> dict[str, Any]:
        return self.store.health()


class PostgresAuthoritativeGraceStateSource(AuthoritativeGraceStateSource):
    """Build one fail-closed Grace state from existing continuity authority."""

    def __init__(self, store: ResidentContinuityStore | None = None) -> None:
        self.store = store or ResidentContinuityStore()

    def load(self) -> AuthoritativeGraceState | None:
        try:
            projection = self.store.rehydration_projection(GRACE_OCCUPANT_ID)
        except (LookupError, RuntimeError, ValueError) as exc:
            raise HomeCognitionExecutionError("authoritative-state-unavailable", "Grace continuity projection is unavailable.") from exc
        projection = self._add_institutional_projection(projection)
        occupant = projection.get("occupant") or {}
        occupancy = projection.get("occupancy")
        bindings = projection.get("bindings") or []
        states = projection.get("state_records") or []
        if occupant.get("display_name") != "Grace" or occupant.get("status") != "active":
            raise HomeCognitionExecutionError("authoritative-state-mismatch", "Grace occupant projection is not active and canonical.")
        if not occupancy or UUID(occupancy["office_id"]) != GRACE_OFFICE_ID:
            raise HomeCognitionExecutionError("authoritative-state-mismatch", "Grace Director of Operations occupancy is unavailable.")
        if len(bindings) != 1 or UUID(bindings[0]["implementation_id"]) != GRACE_IMPLEMENTATION_ID or bindings[0]["purpose"] != GRACE_BINDING_PURPOSE:
            raise HomeCognitionExecutionError("authoritative-state-mismatch", "Grace HOME_COGNITION binding is unavailable or substituted.")
        state = next((item for item in states if item["value_ref"] == "grace:director-of-operations:bounded-authority-context"), None)
        if not state or state["status"] != "active":
            raise HomeCognitionExecutionError("authoritative-state-unavailable", "Grace authority context state is unavailable.")
        assignment = AssignmentContext(
            objective_ref=GRACE_CONTEXT_STATE_KEY,
            stage_ref="resident-continuity:current-authority-context",
            instruction="Use only the bounded current Director of Operations authority context and current operational evidence; return advisory reasoning only.",
            accepted_constraints=("advisory only", "no authority expansion", "no execution", "evidence before assumption"),
            authority_ref=GRACE_AUTHORITY_REF,
            expected_output="bounded advisory reasoning with uncertainty and provenance",
        )
        try:
            bundle = ResidentContextAssembler(_GraceProjectionSource(self.store, projection)).assemble(
                GRACE_OCCUPANT_ID,
                purpose="ENGINEERING_REVIEW",
                budget=BudgetSpec(),
                assignment=assignment,
            )
            institutional = next((item for item in projection.get("state_records", []) if item.get("value_ref") == "riverview:bounded-institutional-context:v1"), None)
            if institutional:
                bundle = replace(bundle, items=(*bundle.items, ContextItem(
                    "state:grace:bounded-institutional-context:v1", "professional_doctrine",
                    {"state_class": "professional_doctrine", "value_ref": institutional["value_ref"], "metadata": institutional["bounded_metadata"], "status": institutional["status"]},
                    None, "high", institutional["classification"], "1", institutional["provenance_id"],
                    "bounded institutional registry, subsystem, and capability projection", 2, False, "structured_projection", 1,
                )))
        except Exception as exc:
            raise HomeCognitionExecutionError("authoritative-state-unavailable", "Grace context assembly failed closed.") from exc
        observed = datetime.now(UTC)
        evidence_refs = tuple(dict.fromkeys((str(occupant["provenance_id"]), str(occupancy["provenance_id"]), str(state["provenance_id"]))))
        state_refs = tuple(dict.fromkeys((str(occupancy["occupancy_id"]), str(bindings[0]["binding_id"]), str(state["state_id"]))))
        return AuthoritativeGraceState(
            resident_id=GRACE_OCCUPANT_ID,
            occupant_id=GRACE_OCCUPANT_ID,
            office_id=GRACE_OFFICE_ID,
            implementation_id=GRACE_IMPLEMENTATION_ID,
            authority_ref=GRACE_AUTHORITY_REF,
            context_bundle=bundle,
            authoritative_state_refs=state_refs,
            evidence_refs=evidence_refs,
            observed_at=observed,
            classification=occupant["classification"],
        )

    def _add_institutional_projection(self, projection: dict[str, object]) -> dict[str, object]:
        """Add bounded read-only Riverview facts to the existing rehydration projection."""
        registry_path = Path(__file__).resolve().parents[3] / "docs/operations/roadmap/evidence/RV-014.1_RESIDENT_REGISTRY.json"
        registry: list[dict[str, str]] = []
        try:
            payload = json.loads(registry_path.read_text(encoding="utf-8"))
            registry = [
                {"name": str(row["name"]), "role": str(row["office"]), "resident_id": str(row["resident_id"]), "responsibility_domains": ["research"] if "research" in str(row["office"]).casefold() else []}
                for row in payload.get("records", [])[:32]
                if isinstance(row, dict) and row.get("name") and row.get("office") and row.get("resident_id")
            ]
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            registry = []
        try:
            durable = self.store.accepted_operator_residents()
        except (LookupError, RuntimeError, ValueError):
            durable = []
        by_name = {item["name"].casefold(): item for item in registry}
        for item in durable:
            by_name[str(item["name"]).casefold()] = {"name": str(item["name"]), "role": str(item["role"]), "resident_id": str(item["resident_id"]), "responsibility_domains": ["research"] if "research" in str(item["role"]).casefold() else []}
        registry = sorted(by_name.values(), key=lambda item: item["name"])[:32]
        try:
            cme = CMEStatusStore().read()
            cme_facts = {"subsystem": "CME", "meaning": "Continuous Momentum Engine", "status": cme.get("effective_state"), "heartbeat_health": cme.get("heartbeat_health"), "last_river_sequence_seen": cme.get("last_river_sequence_seen"), "source": "riverview://cme-runtime-status"}
        except (OSError, RuntimeError, TypeError, ValueError):
            cme_facts = {"subsystem": "CME", "meaning": "Continuous Momentum Engine", "status": "unavailable", "source": "riverview://cme-runtime-status"}
        material = {
            "registry": registry,
            "subsystems": [cme_facts, {"subsystem": "River", "meaning": "authoritative event stream", "source": "riverview://river"}, {"subsystem": "Relay", "meaning": "bounded work-order execution relay", "source": "riverview://relay"}],
            "capabilities": [
                {"capability": "codex.engineering.v1", "purpose": "bounded engineering proposal/work formation", "mode": "advisory proposal only", "execution": "requires separate Steward-authorized formation and lifecycle gate", "human_owner_known": False, "suitable_resident_ids": [], "source": "riverview://capability/codex.engineering.v1"},
                {"capability": "resident-continuity.read", "purpose": "read bounded resident identity, office, and role projections", "mode": "read-only", "execution": "none", "source": "riverview://capability/resident-continuity.read"},
            ],
            "capability_assignment_policy": "Assign a resident only when authoritative capability or responsibility evidence supports the assignment; role presence alone is insufficient.",
            "authority_boundary": "Reading institutional context does not grant mutation or execution authority.",
        }
        projection = dict(projection)
        states = list(projection.get("state_records") or [])
        states.append({"state_id": str(stable_id("state:grace:bounded-institutional-context:v1")), "state_class": "professional_doctrine", "value_kind": "structured_projection", "value_ref": "riverview:bounded-institutional-context:v1", "bounded_metadata": material, "classification": "operational", "retrieval_policy_ref": "grace-home-cognition-policy:v1", "status": "active", "effective_from": datetime.now(UTC).isoformat(), "provenance_id": "RV-014.1;RIV-COG-E1-0001"})
        projection["state_records"] = states[-32:]
        return projection
