"""Authoritative PostgreSQL projection for Grace HOME cognition."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from riverview.residents.context import AssignmentContext, BudgetSpec, PostgresContextSource, ResidentContextAssembler
from riverview.residents.persistence import ResidentContinuityStore, stable_id

from .home_cognition import AuthoritativeGraceState, AuthoritativeGraceStateSource, HomeCognitionExecutionError

GRACE_OCCUPANT_ID = stable_id("occupant:grace")
GRACE_OFFICE_ID = stable_id("office:operations")
GRACE_IMPLEMENTATION_ID = stable_id("implementation:grace-home-cognition:qwen3-coder-30b:ollama-4090")
GRACE_AUTHORITY_REF = "grace:authority-envelope:director-of-operations:v1"
GRACE_CONTEXT_STATE_KEY = "state:grace:home-cognition:authority-context:v1"
GRACE_BINDING_PURPOSE = "HOME_COGNITION"


class PostgresAuthoritativeGraceStateSource(AuthoritativeGraceStateSource):
    """Build one fail-closed Grace state from existing continuity authority."""

    def __init__(self, store: ResidentContinuityStore | None = None) -> None:
        self.store = store or ResidentContinuityStore()

    def load(self) -> AuthoritativeGraceState | None:
        try:
            projection = self.store.rehydration_projection(GRACE_OCCUPANT_ID)
        except (LookupError, RuntimeError, ValueError) as exc:
            raise HomeCognitionExecutionError("authoritative-state-unavailable", "Grace continuity projection is unavailable.") from exc
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
            bundle = ResidentContextAssembler(PostgresContextSource(self.store)).assemble(
                GRACE_OCCUPANT_ID,
                purpose="ENGINEERING_REVIEW",
                budget=BudgetSpec(),
                assignment=assignment,
            )
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
