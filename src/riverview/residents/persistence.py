"""Bounded PostgreSQL resident-continuity persistence.

Version: 1.2.0 | C467 persistence, C469 projection, C470 transitions

This module owns typed persistence operations for the C466 contract and the
bounded C469 rehydration projection. It does not assemble prompts, select
providers, or invoke models.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

from riverview.database import DatabaseConfig, connect

MIGRATION_ID = "0041"
CHECKPOINT = "RIV-RES-0003"
DB_CHECKPOINT = "RIV-DB-0006"

PROVENANCE_CLASSES = frozenset({
    "STEWARD_AUTHORIZED_FACT",
    "ACCEPTED_INSTITUTIONAL_DECISION",
    "CANONICAL_CHARACTER_OR_RESIDENT_MATERIAL",
    "VERIFIED_PRIMARY_HISTORICAL_EVIDENCE",
    "REFLECTION_CONTINUITY_EVIDENCE",
    "IMPLEMENTATION_HISTORY",
    "DERIVED_OR_RECONSTRUCTED_INFERENCE",
    "UNCERTAIN_OR_CONFLICTING_EVIDENCE",
    "OBSOLETE_OR_SUPERSEDED",
})
CONFIDENCE_VALUES = frozenset({"high", "medium", "low", "unresolved"})


def stable_id(key: str) -> UUID:
    """Derive deterministic bootstrap identities without using display labels."""

    if not key.strip():
        raise ValueError("RIV-RES-0003: stable identity key is required.")
    return uuid5(NAMESPACE_URL, f"https://riverview.local/resident-continuity/{key}")


@dataclass(frozen=True, slots=True)
class EvidenceInput:
    source_key: str
    source_repository_or_store: str
    source_location: str
    source_revision: str | None
    content_hash: str | None
    authority_class: str
    confidence: str
    disposition: str
    classification: str = "internal"
    accepted_by: str | None = None
    derived_from: tuple[str, ...] = ()
    unresolved_status: str | None = None

    def __post_init__(self) -> None:
        if self.authority_class not in PROVENANCE_CLASSES:
            raise ValueError("RIV-RES-0003: provenance authority class is closed.")
        if self.confidence not in CONFIDENCE_VALUES:
            raise ValueError("RIV-RES-0003: evidence confidence is closed.")
        if self.confidence == "high" and self.authority_class == "UNCERTAIN_OR_CONFLICTING_EVIDENCE":
            raise ValueError("RIV-RES-0003: unresolved evidence cannot claim high confidence.")


@dataclass(frozen=True, slots=True)
class OfficeInput:
    bootstrap_key: str
    canonical_title: str
    purpose_ref: str
    authority_envelope_ref: str
    policy_profile_ref: str
    occupancy_policy: str
    classification: str
    provenance_id: UUID


@dataclass(frozen=True, slots=True)
class OccupantInput:
    bootstrap_key: str
    display_name: str
    classification: str
    provenance_id: UUID
    canonical_anchor_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ImplementationInput:
    implementation_key: str
    implementation_class: str
    implementation_version: str
    provider_ref: str | None = None
    model_ref: str | None = None
    host_ref: str | None = None
    device_ref: str | None = None
    capability_profile_ref: str | None = None
    classification_eligibility_ref: str | None = None
    configuration_ref: str | None = None
    provenance_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    office_id: UUID
    occupant_id: UUID
    occupancy_id: UUID
    artifact_ids: tuple[UUID, ...]
    contradiction_group_id: UUID
    inserted: bool


@dataclass(frozen=True, slots=True)
class ResidentContinuityStore:
    """Typed PostgreSQL boundary for resident continuity state."""

    config: DatabaseConfig | None = None
    connection_factory: Callable[..., Any] = connect

    @contextmanager
    def _transaction(self) -> Iterator[tuple[Any, Any]]:
        try:
            with self.connection_factory(self.config) as connection, connection.cursor() as cursor:
                yield connection, cursor
        except (RuntimeError, PermissionError, LookupError, ValueError):
            raise
        except Exception as exc:
            raise RuntimeError(f"{CHECKPOINT}: resident persistence transaction failed: {exc}") from exc

    @staticmethod
    def _event(cursor: Any, event_type: str, aggregate_type: str, aggregate_id: UUID, key: str, payload: dict[str, Any], *, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        cursor.execute(
            """INSERT INTO river_events(
                event_id,event_type,aggregate_type,aggregate_id,correlation_id,
                causation_id,idempotency_key,classification,payload,occurred_at
            ) VALUES(%s,%s,%s,%s,%s,%s,%s,'river',%s::jsonb,%s)
            ON CONFLICT(idempotency_key) DO NOTHING""",
            (uuid4(), event_type, aggregate_type, aggregate_id, correlation_id or uuid4(), causation_id, key, json.dumps(payload), datetime.now(UTC)),
        )

    @staticmethod
    def _evidence(cursor: Any, item: EvidenceInput, evidence_id: UUID | None = None) -> UUID:
        evidence_id = evidence_id or stable_id(f"evidence:{item.source_key}")
        cursor.execute(
            """INSERT INTO resident_evidence(
                evidence_id,source_key,source_repository_or_store,source_location,
                source_revision,content_hash,authority_class,confidence,disposition,
                classification,accepted_by,accepted_at,unresolved_status,derived_from
            ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
            ON CONFLICT(source_key) DO NOTHING""",
            (evidence_id, item.source_key, item.source_repository_or_store, item.source_location,
             item.source_revision, item.content_hash, item.authority_class, item.confidence,
             item.disposition, item.classification, item.accepted_by,
             datetime.now(UTC) if item.accepted_by else None, item.unresolved_status, json.dumps(item.derived_from)),
        )
        cursor.execute("SELECT evidence_id,authority_class,confidence,content_hash FROM resident_evidence WHERE source_key=%s", (item.source_key,))
        row = cursor.fetchone()
        if not row or row[1] != item.authority_class or row[2] != item.confidence or row[3] != item.content_hash:
            raise RuntimeError(f"{CHECKPOINT}: evidence identity or authority conflict for {item.source_key}.")
        return row[0]

    def create_office(self, item: OfficeInput, *, office_id: UUID | None = None) -> UUID:
        office_id = office_id or uuid4()
        with self._transaction() as (_, cursor):
            cursor.execute("""INSERT INTO resident_offices(office_id,bootstrap_key,canonical_title,purpose_ref,authority_envelope_ref,policy_profile_ref,occupancy_policy,lifecycle_status,classification,provenance_id)
                VALUES(%s,%s,%s,%s,%s,%s,%s,'active',%s,%s) ON CONFLICT(bootstrap_key) DO NOTHING""",
                (office_id, item.bootstrap_key, item.canonical_title, item.purpose_ref, item.authority_envelope_ref, item.policy_profile_ref, item.occupancy_policy, item.classification, item.provenance_id))
            cursor.execute("SELECT office_id,canonical_title,occupancy_policy FROM resident_offices WHERE bootstrap_key=%s", (item.bootstrap_key,))
            row = cursor.fetchone()
            if not row or row[1] != item.canonical_title or row[2] != item.occupancy_policy:
                raise RuntimeError(f"{CHECKPOINT}: office identity conflict for {item.bootstrap_key}.")
            self._event(cursor, "office.created", "office", row[0], f"office.created:{item.bootstrap_key}", {"office_id": str(row[0]), "title": row[1]})
            return row[0]

    def create_occupant(self, item: OccupantInput, *, occupant_id: UUID | None = None) -> UUID:
        occupant_id = occupant_id or uuid4()
        with self._transaction() as (_, cursor):
            cursor.execute("""INSERT INTO resident_occupants(occupant_id,bootstrap_key,display_name,lifecycle_status,classification,canonical_anchor_ref,provenance_id)
                VALUES(%s,%s,%s,'active',%s,%s,%s) ON CONFLICT(bootstrap_key) DO NOTHING""",
                (occupant_id, item.bootstrap_key, item.display_name, item.classification, item.canonical_anchor_ref, item.provenance_id))
            cursor.execute("SELECT occupant_id,display_name FROM resident_occupants WHERE bootstrap_key=%s", (item.bootstrap_key,))
            row = cursor.fetchone()
            if not row or row[1] != item.display_name:
                raise RuntimeError(f"{CHECKPOINT}: occupant identity conflict for {item.bootstrap_key}.")
            self._event(cursor, "resident.created", "occupant", row[0], f"resident.created:{item.bootstrap_key}", {"occupant_id": str(row[0])})
            return row[0]

    def record_evidence(self, item: EvidenceInput, *, evidence_id: UUID | None = None) -> UUID:
        with self._transaction() as (_, cursor):
            return self._evidence(cursor, item, evidence_id)

    def start_occupancy(self, office_id: UUID, occupant_id: UUID, *, provenance_id: UUID, assignment_authority_ref: str, assignment_reason_ref: str, idempotency_key: str, effective_from: datetime | None = None) -> UUID:
        effective_from = effective_from or datetime.now(UTC)
        occupancy_id = stable_id(f"occupancy:{idempotency_key}")
        with self._transaction() as (_, cursor):
            cursor.execute("SELECT occupancy_policy FROM resident_offices WHERE office_id=%s FOR UPDATE", (office_id,))
            policy = cursor.fetchone()
            if not policy:
                raise LookupError(f"{CHECKPOINT}: office is unavailable.")
            cursor.execute("SELECT occupancy_id FROM resident_occupancies WHERE idempotency_key=%s", (idempotency_key,))
            existing = cursor.fetchone()
            if existing:
                return existing[0]
            cursor.execute("SELECT 1 FROM resident_occupants WHERE occupant_id=%s", (occupant_id,))
            if not cursor.fetchone():
                raise LookupError(f"{CHECKPOINT}: occupant is unavailable.")
            if policy[0] == "single":
                cursor.execute("SELECT occupancy_id FROM resident_occupancies WHERE office_id=%s AND status='active' AND effective_from < %s AND (effective_to IS NULL OR effective_to > %s) FOR UPDATE", (office_id, effective_from, effective_from))
                if cursor.fetchone():
                    raise RuntimeError(f"{CHECKPOINT}: office occupancy policy prohibits overlap.")
            cursor.execute("""INSERT INTO resident_occupancies(occupancy_id,idempotency_key,office_id,occupant_id,status,effective_from,assignment_reason_ref,assignment_authority_ref,provenance_id)
                VALUES(%s,%s,%s,%s,'active',%s,%s,%s,%s)""", (occupancy_id, idempotency_key, office_id, occupant_id, effective_from, assignment_reason_ref, assignment_authority_ref, provenance_id))
            self._event(cursor, "office.occupancy.started", "occupancy", occupancy_id, f"office.occupancy.started:{idempotency_key}", {"office_id": str(office_id), "occupant_id": str(occupant_id), "occupancy_id": str(occupancy_id)})
            return occupancy_id

    def end_occupancy(self, occupancy_id: UUID, *, idempotency_key: str, effective_to: datetime | None = None) -> bool:
        effective_to = effective_to or datetime.now(UTC)
        with self._transaction() as (_, cursor):
            cursor.execute("SELECT occupancy_id,office_id,occupant_id,effective_from,status FROM resident_occupancies WHERE occupancy_id=%s FOR UPDATE", (occupancy_id,))
            row = cursor.fetchone()
            if not row:
                raise LookupError(f"{CHECKPOINT}: occupancy is unavailable.")
            if row[4] == "ended":
                return False
            if effective_to <= row[3]:
                raise ValueError(f"{CHECKPOINT}: occupancy end precedes start.")
            cursor.execute("UPDATE resident_occupancies SET status='ended',effective_to=%s,ended_at=%s,end_idempotency_key=%s WHERE occupancy_id=%s", (effective_to, datetime.now(UTC), idempotency_key, occupancy_id))
            self._event(cursor, "office.occupancy.ended", "occupancy", occupancy_id, f"office.occupancy.ended:{idempotency_key}", {"occupancy_id": str(occupancy_id)})
            return True

    def register_implementation(self, item: ImplementationInput, *, implementation_id: UUID | None = None) -> UUID:
        implementation_id = implementation_id or uuid4()
        with self._transaction() as (_, cursor):
            cursor.execute("""INSERT INTO resident_implementations(implementation_id,implementation_key,implementation_class,implementation_version,provider_ref,model_ref,host_ref,device_ref,capability_profile_ref,classification_eligibility_ref,configuration_ref,lifecycle_status,provenance_id)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'registered',%s) ON CONFLICT(implementation_key) DO NOTHING""", (implementation_id, item.implementation_key, item.implementation_class, item.implementation_version, item.provider_ref, item.model_ref, item.host_ref, item.device_ref, item.capability_profile_ref, item.classification_eligibility_ref, item.configuration_ref, item.provenance_id))
            cursor.execute("SELECT implementation_id FROM resident_implementations WHERE implementation_key=%s", (item.implementation_key,))
            row = cursor.fetchone()
            if not row:
                raise RuntimeError(f"{CHECKPOINT}: implementation registration reconciliation failed.")
            return row[0]

    def bind_implementation(self, occupant_id: UUID, implementation_id: UUID, *, purpose: str, policy_ref: str, idempotency_key: str, provenance_id: UUID, activation_evidence_id: UUID | None = None, effective_from: datetime | None = None) -> UUID:
        binding_id = stable_id(f"binding:{idempotency_key}")
        effective_from = effective_from or datetime.now(UTC)
        with self._transaction() as (_, cursor):
            cursor.execute("SELECT binding_id FROM resident_implementation_bindings WHERE idempotency_key=%s", (idempotency_key,))
            existing = cursor.fetchone()
            if existing:
                return existing[0]
            cursor.execute("SELECT 1 FROM resident_occupants WHERE occupant_id=%s", (occupant_id,))
            if not cursor.fetchone():
                raise LookupError(f"{CHECKPOINT}: binding occupant is unavailable.")
            cursor.execute("SELECT 1 FROM resident_implementations WHERE implementation_id=%s", (implementation_id,))
            if not cursor.fetchone():
                raise LookupError(f"{CHECKPOINT}: implementation is unavailable.")
            cursor.execute("""INSERT INTO resident_implementation_bindings(binding_id,idempotency_key,occupant_id,implementation_id,purpose,status,effective_from,policy_ref,activation_evidence_id)
                VALUES(%s,%s,%s,%s,%s,'active',%s,%s,%s)""", (binding_id, idempotency_key, occupant_id, implementation_id, purpose, effective_from, policy_ref, activation_evidence_id))
            self._event(cursor, "resident.implementation.bound", "binding", binding_id, f"resident.implementation.bound:{idempotency_key}", {"occupant_id": str(occupant_id), "implementation_id": str(implementation_id), "purpose": purpose})
            return binding_id

    def retire_implementation_binding(self, binding_id: UUID, *, idempotency_key: str, retirement_evidence_id: UUID | None = None, effective_to: datetime | None = None) -> bool:
        effective_to = effective_to or datetime.now(UTC)
        with self._transaction() as (_, cursor):
            cursor.execute("SELECT status,effective_from FROM resident_implementation_bindings WHERE binding_id=%s FOR UPDATE", (binding_id,))
            row = cursor.fetchone()
            if not row:
                raise LookupError(f"{CHECKPOINT}: implementation binding is unavailable.")
            if row[0] == "retired":
                return False
            if effective_to <= row[1]:
                raise ValueError(f"{CHECKPOINT}: binding retirement precedes start.")
            cursor.execute("UPDATE resident_implementation_bindings SET status='retired',effective_to=%s,retirement_evidence_id=%s,retirement_idempotency_key=%s WHERE binding_id=%s", (effective_to, retirement_evidence_id, idempotency_key, binding_id))
            self._event(cursor, "resident.implementation.retired", "binding", binding_id, f"resident.implementation.retired:{idempotency_key}", {"binding_id": str(binding_id)})
            return True

    def transition_implementation(self, *, occupant_id: UUID, old_binding_id: UUID, new_implementation_id: UUID, purpose: str, policy_ref: str, transition_key: str, provenance_id: UUID, activation_evidence_id: UUID | None = None, retirement_evidence_id: UUID | None = None, effective_at: datetime | None = None) -> UUID:
        """Atomically retire one binding and activate its successor.

        Validation and rehydration preflight belong to the runtime; this method
        is the PostgreSQL transaction boundary and is safe to replay by key.
        """
        if not transition_key.strip():
            raise ValueError(f"{CHECKPOINT}: transition idempotency key is required.")
        effective_at = effective_at or datetime.now(UTC)
        new_binding_id = stable_id(f"binding-transition:{transition_key}")
        with self._transaction() as (_, cursor):
            cursor.execute("SELECT binding_id FROM resident_implementation_bindings WHERE idempotency_key=%s", (f"transition:{transition_key}",))
            existing = cursor.fetchone()
            if existing:
                return existing[0]
            cursor.execute("SELECT occupant_id,status,effective_from FROM resident_implementation_bindings WHERE binding_id=%s FOR UPDATE", (old_binding_id,))
            old = cursor.fetchone()
            if not old or old[0] != occupant_id or old[1] != "active":
                raise RuntimeError(f"{CHECKPOINT}: active predecessor binding is unavailable.")
            if effective_at <= old[2]:
                raise ValueError(f"{CHECKPOINT}: transition precedes predecessor activation.")
            cursor.execute("SELECT 1 FROM resident_implementations WHERE implementation_id=%s AND lifecycle_status='registered'", (new_implementation_id,))
            if not cursor.fetchone():
                raise LookupError(f"{CHECKPOINT}: replacement implementation is unavailable.")
            # Insert the successor before linking the predecessor.  The
            # predecessor's successor_binding_id is a foreign key, so updating
            # it first makes every valid transition fail inside PostgreSQL.
            cursor.execute("INSERT INTO resident_implementation_bindings(binding_id,idempotency_key,occupant_id,implementation_id,purpose,status,effective_from,policy_ref,activation_evidence_id,predecessor_binding_id) VALUES(%s,%s,%s,%s,%s,'active',%s,%s,%s,%s)", (new_binding_id, f"transition:{transition_key}", occupant_id, new_implementation_id, purpose, effective_at, policy_ref, activation_evidence_id, old_binding_id))
            cursor.execute("UPDATE resident_implementation_bindings SET status='retired',effective_to=%s,retirement_evidence_id=%s,retirement_idempotency_key=%s,successor_binding_id=%s WHERE binding_id=%s", (effective_at, retirement_evidence_id, f"retire:{transition_key}", new_binding_id, old_binding_id))
            self._event(cursor, "resident.implementation.transition.completed", "binding", new_binding_id, f"resident.implementation.transition.completed:{transition_key}", {"occupant_id": str(occupant_id), "old_binding_id": str(old_binding_id), "new_binding_id": str(new_binding_id), "provenance_id": str(provenance_id)})
            self._event(cursor, "resident.context.invalidated", "occupant", occupant_id, f"resident.context.invalidated:transition:{transition_key}", {"occupant_id": str(occupant_id), "reason": "implementation transition", "old_binding_id": str(old_binding_id)})
            return new_binding_id

    def register_artifact(self, *, artifact_key: str, artifact_type: str, logical_version: str, content_hash: str, repository_or_store: str, source_location: str, classification: str, owner_ref: str, provenance_id: UUID, subject_occupant_id: UUID | None = None, office_id: UUID | None = None, canonical_revision: str | None = None, historical_revision: str | None = None, storage_class: str = "github", retrieval_eligibility: str = "eligible", artifact_id: UUID | None = None) -> UUID:
        artifact_id = artifact_id or stable_id(f"artifact:{artifact_key}")
        with self._transaction() as (_, cursor):
            cursor.execute("""INSERT INTO resident_artifact_references(artifact_id,artifact_key,artifact_type,logical_version,content_hash,repository_or_store,source_location,canonical_revision,historical_revision,classification,owner_ref,subject_occupant_id,office_id,provenance_id,availability,storage_class,retrieval_eligibility)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'available',%s,%s) ON CONFLICT(artifact_key) DO NOTHING""", (artifact_id, artifact_key, artifact_type, logical_version, content_hash, repository_or_store, source_location, canonical_revision, historical_revision, classification, owner_ref, subject_occupant_id, office_id, provenance_id, storage_class, retrieval_eligibility))
            cursor.execute("SELECT artifact_id,content_hash FROM resident_artifact_references WHERE artifact_key=%s", (artifact_key,))
            row = cursor.fetchone()
            if not row or row[1] != content_hash:
                raise RuntimeError(f"{CHECKPOINT}: artifact identity/hash conflict for {artifact_key}.")
            self._event(cursor, "resident.artifact.linked", "artifact", row[0], f"resident.artifact.linked:{artifact_key}", {"artifact_id": str(row[0]), "artifact_key": artifact_key})
            return row[0]

    def record_claim(self, *, claim_key: str, subject_type: str, subject_id: UUID, controlled_predicate: str, value_kind: str, value_text: str | None, value_reference: str | None, evidence_id: UUID, authority_class: str, confidence: str, status: str = "accepted", contradiction_group_id: UUID | None = None, supersedes_claim_id: UUID | None = None) -> UUID:
        if authority_class not in PROVENANCE_CLASSES or confidence not in CONFIDENCE_VALUES:
            raise ValueError(f"{CHECKPOINT}: claim authority/confidence value is invalid.")
        claim_id = stable_id(f"claim:{claim_key}")
        with self._transaction() as (_, cursor):
            return self._claim(cursor, claim_id, claim_key, subject_type, subject_id, controlled_predicate, value_kind, value_text, value_reference, evidence_id, authority_class, confidence, status, contradiction_group_id, supersedes_claim_id)

    @staticmethod
    def _claim(cursor: Any, claim_id: UUID, claim_key: str, subject_type: str, subject_id: UUID, controlled_predicate: str, value_kind: str, value_text: str | None, value_reference: str | None, evidence_id: UUID, authority_class: str, confidence: str, status: str, contradiction_group_id: UUID | None, supersedes_claim_id: UUID | None) -> UUID:
        cursor.execute("""INSERT INTO resident_claims(claim_id,claim_key,subject_type,subject_id,controlled_predicate,value_kind,value_text,value_reference,evidence_id,authority_class,confidence,status,contradiction_group_id,supersedes_claim_id)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(claim_key) DO NOTHING""", (claim_id, claim_key, subject_type, subject_id, controlled_predicate, value_kind, value_text, value_reference, evidence_id, authority_class, confidence, status, contradiction_group_id, supersedes_claim_id))
        cursor.execute("SELECT claim_id,authority_class,confidence FROM resident_claims WHERE claim_key=%s", (claim_key,))
        row = cursor.fetchone()
        if not row or row[1] != authority_class or row[2] != confidence:
            raise RuntimeError(f"{CHECKPOINT}: claim authority/confidence conflict for {claim_key}.")
        return row[0]

    def record_contradiction(self, *, subject_type: str, subject_id: UUID, provenance_id: UUID, claims: tuple[dict[str, Any], ...], contradiction_group_id: UUID | None = None) -> UUID:
        if len(claims) < 2:
            raise ValueError(f"{CHECKPOINT}: contradiction requires at least two claims.")
        group_id = contradiction_group_id or uuid4()
        with self._transaction() as (_, cursor):
            cursor.execute("INSERT INTO resident_contradiction_groups(contradiction_group_id,subject_type,subject_id,status,provenance_id) VALUES(%s,%s,%s,'unresolved',%s) ON CONFLICT(contradiction_group_id) DO NOTHING", (group_id, subject_type, subject_id, provenance_id))
            for claim in claims:
                self._claim(cursor, claim.get("claim_id") or stable_id(f"claim:{claim['claim_key']}"), claim["claim_key"], subject_type, subject_id, claim["predicate"], claim.get("value_kind", "text"), claim.get("value"), claim.get("value_reference"), claim["evidence_id"], claim["authority_class"], claim["confidence"], "contradicted", group_id, None)
            return group_id

    def supersede_claim(self, claim_id: UUID, *, claim_key: str, controlled_predicate: str, value_kind: str, value_text: str | None, value_reference: str | None, evidence_id: UUID, authority_class: str, confidence: str) -> UUID:
        """Append a successor claim and mark the predecessor superseded."""

        with self._transaction() as (_, cursor):
            cursor.execute("SELECT subject_type,subject_id,contradiction_group_id,status FROM resident_claims WHERE claim_id=%s FOR UPDATE", (claim_id,))
            predecessor = cursor.fetchone()
            if not predecessor:
                raise LookupError(f"{CHECKPOINT}: supersession predecessor is unavailable.")
            successor = self._claim(cursor, stable_id(f"claim:{claim_key}"), claim_key, predecessor[0], predecessor[1], controlled_predicate, value_kind, value_text, value_reference, evidence_id, authority_class, confidence, "accepted", predecessor[2], claim_id)
            cursor.execute("UPDATE resident_claims SET status='superseded' WHERE claim_id=%s", (claim_id,))
            self._event(cursor, "resident.canon.superseded", "claim", successor, f"resident.canon.superseded:{claim_id}:{successor}", {"predecessor_claim_id": str(claim_id), "successor_claim_id": str(successor)})
            return successor

    def record_relationship(self, *, relationship_key: str, subject_a_type: str, subject_a_id: UUID, subject_b_type: str, subject_b_id: UUID, relationship_type: str, authority_ref: str, provenance_id: UUID, classification: str = "test_fixture", visibility_policy_ref: str = "explicit") -> UUID:
        if subject_a_id == subject_b_id:
            raise ValueError(f"{CHECKPOINT}: a relationship cannot connect an identity to itself.")
        relationship_id = stable_id(f"relationship:{relationship_key}")
        with self._transaction() as (_, cursor):
            cursor.execute("""INSERT INTO resident_relationships(relationship_id,relationship_key,subject_a_type,subject_a_id,subject_b_type,subject_b_id,relationship_type,status,authority_ref,provenance_id,classification,visibility_policy_ref)
                VALUES(%s,%s,%s,%s,%s,%s,%s,'active',%s,%s,%s,%s) ON CONFLICT(relationship_key) DO NOTHING""", (relationship_id, relationship_key, subject_a_type, subject_a_id, subject_b_type, subject_b_id, relationship_type, authority_ref, provenance_id, classification, visibility_policy_ref))
            cursor.execute("SELECT relationship_id FROM resident_relationships WHERE relationship_key=%s", (relationship_key,))
            row = cursor.fetchone()
            if not row:
                raise RuntimeError(f"{CHECKPOINT}: relationship reconciliation failed.")
            return row[0]

    def record_state_reference(self, *, state_key: str, occupant_id: UUID | None, office_id: UUID | None, state_class: str, value_ref: str, provenance_id: UUID, classification: str = "internal", retrieval_policy_ref: str | None = None, value_kind: str = "reference", bounded_metadata: dict[str, Any] | None = None) -> UUID:
        state_id = stable_id(f"state:{state_key}")
        with self._transaction() as (_, cursor):
            cursor.execute("""INSERT INTO resident_state_records(state_id,state_key,subject_occupant_id,subject_office_id,state_class,value_kind,value_ref,bounded_metadata,provenance_id,classification,retrieval_policy_ref,status)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,'active') ON CONFLICT(state_key) DO NOTHING""", (state_id, state_key, occupant_id, office_id, state_class, value_kind, value_ref, json.dumps(bounded_metadata or {}), provenance_id, classification, retrieval_policy_ref))
            cursor.execute("SELECT state_id FROM resident_state_records WHERE state_key=%s", (state_key,))
            row = cursor.fetchone()
            if not row:
                raise RuntimeError(f"{CHECKPOINT}: state reference reconciliation failed.")
            return row[0]

    def record_residency_acceptance(
        self,
        *,
        occupant_id: UUID,
        office_id: UUID,
        evidence: EvidenceInput,
        acceptance_key: str,
        steward_ref: str,
        acceptance_ref: str,
        implementation_candidate: str | None = None,
    ) -> dict[str, str]:
        """Record a Steward residency decision as state plus an immutable River event.

        Acceptance is intentionally represented separately from occupant lifecycle
        and implementation binding.  The occupant and active office occupancy must
        already exist; this transition records the governed decision without
        inventing personal canon or activating a production implementation.
        """

        if not acceptance_key.strip() or not steward_ref.strip() or not acceptance_ref.strip():
            raise ValueError(f"{CHECKPOINT}: residency acceptance references are required.")
        state_key = f"residency:{acceptance_key}"
        state_id = stable_id(f"state:{state_key}")
        with self._transaction() as (_, cursor):
            cursor.execute(
                "SELECT 1 FROM resident_occupants WHERE occupant_id=%s AND lifecycle_status='active'",
                (occupant_id,),
            )
            if not cursor.fetchone():
                raise LookupError(f"{CHECKPOINT}: accepted occupant is unavailable or inactive.")
            cursor.execute(
                "SELECT 1 FROM resident_occupancies WHERE office_id=%s AND occupant_id=%s AND status='active'",
                (office_id, occupant_id),
            )
            if not cursor.fetchone():
                raise LookupError(f"{CHECKPOINT}: accepted office occupancy is unavailable or inactive.")
            evidence_id = self._evidence(cursor, evidence)
            metadata = {
                "state_type": "residency_acceptance",
                "residency_status": "accepted",
                "steward": steward_ref,
                "acceptance_ref": acceptance_ref,
                "implementation_candidate": implementation_candidate,
                "production_implementation_binding": False,
            }
            cursor.execute(
                """INSERT INTO resident_state_records(
                    state_id,state_key,subject_occupant_id,subject_office_id,
                    state_class,value_kind,value_ref,bounded_metadata,provenance_id,
                    classification,retrieval_policy_ref,status
                ) VALUES(%s,%s,%s,%s,'office_role_knowledge','reference',%s,%s::jsonb,%s,
                         'internal','resident-acceptance-state:v1','active')
                ON CONFLICT(state_key) DO NOTHING""",
                (
                    state_id,
                    state_key,
                    occupant_id,
                    office_id,
                    evidence.source_key,
                    json.dumps(metadata),
                    evidence_id,
                ),
            )
            cursor.execute(
                """SELECT state_id,value_ref,bounded_metadata,provenance_id
                   FROM resident_state_records WHERE state_key=%s""",
                (state_key,),
            )
            state = cursor.fetchone()
            if not state or state[0] != state_id or state[1] != evidence.source_key or state[3] != evidence_id:
                raise RuntimeError(f"{CHECKPOINT}: residency acceptance state reconciliation failed.")
            self._event(
                cursor,
                "resident.residency.accepted",
                "occupant",
                occupant_id,
                f"resident.residency.accepted:{acceptance_key}",
                {
                    "occupant_id": str(occupant_id),
                    "office_id": str(office_id),
                    "acceptance_ref": acceptance_ref,
                    "steward_ref": steward_ref,
                    "evidence_id": str(evidence_id),
                    "implementation_candidate": implementation_candidate,
                    "production_implementation_binding": False,
                },
            )
            return {"evidence_id": str(evidence_id), "state_id": str(state_id), "state_key": state_key}

    def historical_occupancies(self, occupant_id: UUID) -> list[dict[str, Any]]:
        with self._transaction() as (_, cursor):
            cursor.execute("""SELECT x.occupancy_id,x.office_id,o.canonical_title,x.status,x.effective_from,x.effective_to
                FROM resident_occupancies x JOIN resident_offices o ON o.office_id=x.office_id
                WHERE x.occupant_id=%s ORDER BY x.effective_from""", (occupant_id,))
            return [{"occupancy_id": str(row[0]), "office_id": str(row[1]), "title": row[2], "status": row[3], "effective_from": row[4].isoformat(), "effective_to": row[5].isoformat() if row[5] else None} for row in cursor.fetchall()]

    def accepted_operator_residents(self) -> list[dict[str, Any]]:
        """Return accepted active residents eligible for the Operator surface."""

        with self._transaction() as (_, cursor):
            cursor.execute(
                """SELECT o.occupant_id,o.display_name,o.classification,
                          x.office_id,office.canonical_title,
                          COALESCE(role.value_text, office.canonical_title),
                          acceptance.bounded_metadata,acceptance.provenance_id
                   FROM resident_occupants o
                   JOIN resident_occupancies x ON x.occupant_id=o.occupant_id
                   JOIN resident_offices office ON office.office_id=x.office_id
                   JOIN resident_state_records acceptance
                     ON acceptance.subject_occupant_id=o.occupant_id
                    AND acceptance.subject_office_id=office.office_id
                    AND acceptance.status='active'
                    AND acceptance.bounded_metadata->>'state_type'='residency_acceptance'
                    AND acceptance.bounded_metadata->>'residency_status'='accepted'
                   LEFT JOIN LATERAL (
                       SELECT c.value_text
                         FROM resident_claims c
                        WHERE c.subject_type='occupant'
                          AND c.subject_id=o.occupant_id
                          AND c.controlled_predicate='office_title'
                          AND c.status='accepted'
                        ORDER BY c.created_at DESC LIMIT 1
                   ) role ON TRUE
                  WHERE o.lifecycle_status='active' AND x.status='active'
                  ORDER BY o.display_name"""
            )
            return [
                {
                    "resident_id": str(row[0]),
                    "name": row[1],
                    "classification": row[2],
                    "office_id": str(row[3]),
                    "office": row[4],
                    "role": row[5],
                    "residency_status": "accepted",
                    "source": "resident_continuity_postgresql",
                    "acceptance_metadata": row[6],
                    "acceptance_provenance_id": str(row[7]),
                }
                for row in cursor.fetchall()
            ]

    def active_implementation_binding(self, occupant_id: UUID) -> dict[str, Any]:
        """Return the one active implementation binding for an occupant."""

        with self._transaction() as (_, cursor):
            cursor.execute(
                """SELECT b.binding_id,b.occupant_id,b.implementation_id,b.purpose,
                          b.policy_ref,b.status,i.implementation_key,
                          i.implementation_class,i.implementation_version,
                          i.provider_ref,i.model_ref,i.host_ref,i.device_ref,
                          i.capability_profile_ref,i.configuration_ref,
                          i.classification_eligibility_ref
                   FROM resident_implementation_bindings b
                   JOIN resident_implementations i ON i.implementation_id=b.implementation_id
                  WHERE b.occupant_id=%s AND b.status='active'
                  ORDER BY b.effective_from DESC""",
                (occupant_id,),
            )
            rows = cursor.fetchall()
            if len(rows) != 1:
                raise LookupError(f"{CHECKPOINT}: exactly one active implementation binding is required.")
            row = rows[0]
            return {
                "binding_id": row[0], "occupant_id": row[1], "implementation_id": row[2],
                "purpose": row[3], "policy_ref": row[4], "status": row[5],
                "implementation_key": row[6], "implementation_class": row[7],
                "implementation_version": row[8], "provider_ref": row[9],
                "model_ref": row[10], "host_ref": row[11], "device_ref": row[12],
                "capability_profile_ref": row[13], "configuration_ref": row[14],
                "classification_eligibility_ref": row[15],
            }

    def active_implementation_binding_by_id(self, implementation_id: UUID) -> dict[str, Any]:
        """Return an active binding by implementation identity for runtime checks."""

        with self._transaction() as (_, cursor):
            cursor.execute(
                """SELECT occupant_id FROM resident_implementation_bindings
                  WHERE implementation_id=%s AND status='active'
                  ORDER BY effective_from DESC LIMIT 1""",
                (implementation_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise LookupError(f"{CHECKPOINT}: active implementation is unavailable.")
            return self.active_implementation_binding(row[0])

    def implementation_history(self, occupant_id: UUID) -> list[dict[str, Any]]:
        with self._transaction() as (_, cursor):
            cursor.execute("""SELECT b.binding_id,b.purpose,b.status,i.implementation_key,i.implementation_version,b.effective_from,b.effective_to
                FROM resident_implementation_bindings b JOIN resident_implementations i ON i.implementation_id=b.implementation_id
                WHERE b.occupant_id=%s ORDER BY b.effective_from""", (occupant_id,))
            return [{"binding_id": str(row[0]), "purpose": row[1], "status": row[2], "implementation_key": row[3], "implementation_version": row[4], "effective_from": row[5].isoformat(), "effective_to": row[6].isoformat() if row[6] else None} for row in cursor.fetchall()]

    def record_reflection(self, *, proposal_key: str, proposer_ref: str, subject_type: str, subject_id: UUID, change_class: str, target_ref: str, proposal_ref: str, provenance_id: UUID, classification: str = "internal") -> UUID:
        proposal_id = stable_id(f"proposal:{proposal_key}")
        with self._transaction() as (_, cursor):
            cursor.execute("""INSERT INTO resident_change_proposals(proposal_id,proposal_key,proposer_ref,subject_type,subject_id,change_class,target_ref,proposal_ref,status,provenance_id,classification)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'recorded',%s,%s) ON CONFLICT(proposal_key) DO NOTHING""", (proposal_id, proposal_key, proposer_ref, subject_type, subject_id, change_class, target_ref, proposal_ref, provenance_id, classification))
            cursor.execute("SELECT proposal_id FROM resident_change_proposals WHERE proposal_key=%s", (proposal_key,))
            row = cursor.fetchone()
            if not row:
                raise RuntimeError(f"{CHECKPOINT}: reflection proposal reconciliation failed.")
            self._event(cursor, "resident.reflection.recorded", "proposal", row[0], f"resident.reflection.recorded:{proposal_key}", {"proposal_id": str(row[0]), "change_class": change_class})
            return row[0]

    def review_change(self, proposal_id: UUID, *, reviewer_ref: str, reviewer_capability_ref: str, decision: str, authority_ref: str, evidence_id: UUID, reason_ref: str) -> UUID:
        if decision not in {"accepted", "rejected", "unresolved"}:
            raise ValueError(f"{CHECKPOINT}: review decision is closed.")
        review_id = uuid4()
        with self._transaction() as (_, cursor):
            cursor.execute("SELECT proposal_id,status FROM resident_change_proposals WHERE proposal_id=%s FOR UPDATE", (proposal_id,))
            if not cursor.fetchone():
                raise LookupError(f"{CHECKPOINT}: proposal is unavailable.")
            cursor.execute("INSERT INTO resident_change_reviews(review_id,proposal_id,reviewer_ref,reviewer_capability_ref,decision,authority_ref,evidence_id,reason_ref) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)", (review_id, proposal_id, reviewer_ref, reviewer_capability_ref, decision, authority_ref, evidence_id, reason_ref))
            status = "under_review" if decision == "unresolved" else decision
            cursor.execute("UPDATE resident_change_proposals SET status=%s,reviewed_at=now() WHERE proposal_id=%s", (status, proposal_id))
            return review_id

    def accept_change(self, proposal_id: UUID, review_id: UUID, *, target_type: str, target_id: UUID, predecessor_version: int | None, successor_version: int, authority_ref: str, evidence_id: UUID) -> UUID:
        mutation_id = uuid4()
        with self._transaction() as (_, cursor):
            cursor.execute("SELECT status FROM resident_change_proposals WHERE proposal_id=%s FOR UPDATE", (proposal_id,))
            proposal = cursor.fetchone()
            cursor.execute("SELECT decision FROM resident_change_reviews WHERE review_id=%s AND proposal_id=%s", (review_id, proposal_id))
            review = cursor.fetchone()
            if not proposal or not review or proposal[0] != "accepted" or review[0] != "accepted":
                raise PermissionError(f"{CHECKPOINT}: canonical mutation requires accepted proposal and review.")
            cursor.execute("INSERT INTO resident_canonical_mutations(mutation_id,proposal_id,review_id,target_type,target_id,predecessor_version,successor_version,authority_ref,evidence_id,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'accepted')", (mutation_id, proposal_id, review_id, target_type, target_id, predecessor_version, successor_version, authority_ref, evidence_id))
            self._event(cursor, "resident.change.accepted", "mutation", mutation_id, f"resident.change.accepted:{mutation_id}", {"proposal_id": str(proposal_id), "target_type": target_type, "target_id": str(target_id)})
            return mutation_id

    def current_projection(self, occupant_id: UUID) -> dict[str, Any]:
        with self._transaction() as (_, cursor):
            cursor.execute("SELECT occupant_id,display_name,lifecycle_status,classification,version FROM resident_occupants WHERE occupant_id=%s", (occupant_id,))
            occupant = cursor.fetchone()
            if not occupant:
                raise LookupError(f"{CHECKPOINT}: occupant projection is unavailable.")
            cursor.execute("SELECT o.office_id,o.canonical_title,x.occupancy_id,x.effective_from FROM resident_occupancies x JOIN resident_offices o ON o.office_id=x.office_id WHERE x.occupant_id=%s AND x.status='active' ORDER BY x.effective_from DESC", (occupant_id,))
            occupancy = cursor.fetchone()
            cursor.execute("SELECT b.binding_id,b.purpose,b.implementation_id,i.implementation_key,i.implementation_version FROM resident_implementation_bindings b JOIN resident_implementations i ON i.implementation_id=b.implementation_id WHERE b.occupant_id=%s AND b.status='active' ORDER BY b.effective_from DESC", (occupant_id,))
            bindings = cursor.fetchall()
            cursor.execute("SELECT claim_id,controlled_predicate,value_kind,value_text,value_reference,authority_class,confidence,status FROM resident_claims WHERE subject_type='occupant' AND subject_id=%s ORDER BY created_at", (occupant_id,))
            claims = cursor.fetchall()
            return {"occupant": {"occupant_id": str(occupant[0]), "display_name": occupant[1], "status": occupant[2], "classification": occupant[3], "version": occupant[4]}, "occupancy": None if not occupancy else {"office_id": str(occupancy[0]), "title": occupancy[1], "occupancy_id": str(occupancy[2]), "effective_from": occupancy[3].isoformat()}, "bindings": [{"binding_id": str(row[0]), "purpose": row[1], "implementation_id": str(row[2]), "implementation_key": row[3], "implementation_version": row[4]} for row in bindings], "claims": [{"claim_id": str(row[0]), "predicate": row[1], "value_kind": row[2], "value": row[3] or row[4], "authority_class": row[5], "confidence": row[6], "status": row[7]} for row in claims]}

    def rehydration_projection(self, occupant_id: UUID) -> dict[str, Any]:
        """Return the bounded, provenance-bearing inputs allowed to rehydrate a resident."""

        with self._transaction() as (_, cursor):
            cursor.execute("SELECT occupant_id,display_name,lifecycle_status,classification,canonical_anchor_ref,provenance_id,version FROM resident_occupants WHERE occupant_id=%s", (occupant_id,))
            occupant = cursor.fetchone()
            if not occupant:
                raise LookupError(f"{CHECKPOINT}: rehydration occupant projection is unavailable.")
            cursor.execute("""SELECT o.office_id,o.canonical_title,o.purpose_ref,o.authority_envelope_ref,
                                      o.policy_profile_ref,o.occupancy_policy,o.classification,
                                      x.occupancy_id,x.effective_from,x.assignment_reason_ref,
                                      x.assignment_authority_ref,x.provenance_id
                               FROM resident_occupancies x
                               JOIN resident_offices o ON o.office_id=x.office_id
                               WHERE x.occupant_id=%s AND x.status='active'
                               ORDER BY x.effective_from DESC LIMIT 1""", (occupant_id,))
            occupancy = cursor.fetchone()
            cursor.execute("""SELECT b.binding_id,b.purpose,b.implementation_id,i.implementation_key,
                                      i.implementation_class,i.provider_ref,i.model_ref,i.host_ref,
                                      i.device_ref,i.implementation_version,i.classification_eligibility_ref,
                                      b.policy_ref,b.effective_from
                               FROM resident_implementation_bindings b
                               JOIN resident_implementations i ON i.implementation_id=b.implementation_id
                               WHERE b.occupant_id=%s AND b.status='active'
                               ORDER BY b.effective_from DESC""", (occupant_id,))
            bindings = cursor.fetchall()
            cursor.execute("""SELECT c.claim_id,c.controlled_predicate,c.value_kind,c.value_text,
                                      c.value_reference,c.authority_class,c.confidence,c.status,
                                      c.evidence_id,e.source_key,e.source_location,e.source_revision,
                                      e.content_hash,e.classification,c.contradiction_group_id,
                                      c.supersedes_claim_id
                               FROM resident_claims c JOIN resident_evidence e ON e.evidence_id=c.evidence_id
                               WHERE c.subject_type='occupant' AND c.subject_id=%s
                               ORDER BY c.created_at,c.claim_id""", (occupant_id,))
            claims = cursor.fetchall()
            office_id = occupancy[0] if occupancy else None
            cursor.execute("""SELECT artifact_id,artifact_key,artifact_type,logical_version,content_hash,
                                      repository_or_store,source_location,canonical_revision,historical_revision,
                                      classification,owner_ref,availability,storage_class,retrieval_eligibility,
                                      provenance_id,superseded_by
                               FROM resident_artifact_references
                               WHERE subject_occupant_id=%s OR office_id=%s
                               ORDER BY artifact_key""", (occupant_id, office_id))
            artifacts = cursor.fetchall()
            cursor.execute("""SELECT relationship_id,subject_a_type,subject_a_id,subject_b_type,subject_b_id,
                                      relationship_type,status,effective_from,effective_to,authority_ref,
                                      provenance_id,classification,visibility_policy_ref
                               FROM resident_relationships
                               WHERE (subject_a_type='occupant' AND subject_a_id=%s)
                                  OR (subject_b_type='occupant' AND subject_b_id=%s)
                               ORDER BY relationship_id""", (occupant_id, occupant_id))
            relationships = cursor.fetchall()
            cursor.execute("""SELECT state_id,state_class,value_kind,value_ref,bounded_metadata,classification,
                                      retrieval_policy_ref,status,effective_from,provenance_id
                               FROM resident_state_records
                               WHERE subject_occupant_id=%s OR subject_office_id=%s
                               ORDER BY state_class,state_id""", (occupant_id, office_id))
            state_records = cursor.fetchall()
            cursor.execute("""SELECT DISTINCT g.contradiction_group_id,g.subject_type,g.subject_id,g.status,
                                      g.resolution_ref,g.provenance_id
                               FROM resident_contradiction_groups g
                               JOIN resident_claims c ON c.contradiction_group_id=g.contradiction_group_id
                               WHERE c.subject_id=%s OR g.subject_id=%s
                               ORDER BY g.contradiction_group_id""", (occupant_id, occupant_id))
            contradictions = cursor.fetchall()
            cursor.execute("""SELECT retrieval_id,target_type,target_id,purpose,classification,policy_ref,
                                      policy_version,eligibility,decision_reason,freshness,availability,
                                      selected_at,expired_at,evidence_id
                               FROM resident_retrieval_metadata
                               WHERE target_type='occupant' AND target_id=%s
                               ORDER BY retrieval_id""", (occupant_id,))
            retrieval = cursor.fetchall()

            def evidence_fields(row: tuple[Any, ...], offset: int) -> dict[str, Any]:
                return {"evidence_id": str(row[offset]), "source_key": row[offset + 1], "source_location": row[offset + 2], "source_revision": row[offset + 3], "content_hash": row[offset + 4], "classification": row[offset + 5]}

            return {
                "occupant": {"occupant_id": str(occupant[0]), "display_name": occupant[1], "status": occupant[2], "classification": occupant[3], "canonical_anchor_ref": occupant[4], "provenance_id": str(occupant[5]), "version": occupant[6]},
                "occupancy": None if not occupancy else {"office_id": str(occupancy[0]), "title": occupancy[1], "purpose_ref": occupancy[2], "authority_envelope_ref": occupancy[3], "policy_profile_ref": occupancy[4], "occupancy_policy": occupancy[5], "classification": occupancy[6], "occupancy_id": str(occupancy[7]), "effective_from": occupancy[8].isoformat(), "assignment_reason_ref": occupancy[9], "assignment_authority_ref": occupancy[10], "provenance_id": str(occupancy[11])},
                "bindings": [{"binding_id": str(row[0]), "purpose": row[1], "implementation_id": str(row[2]), "implementation_key": row[3], "implementation_class": row[4], "provider_ref": row[5], "model_ref": row[6], "host_ref": row[7], "device_ref": row[8], "implementation_version": row[9], "classification_eligibility_ref": row[10], "policy_ref": row[11], "effective_from": row[12].isoformat()} for row in bindings],
                "claims": [{"claim_id": str(row[0]), "predicate": row[1], "value_kind": row[2], "value": row[3] or row[4], "authority_class": row[5], "confidence": row[6], "status": row[7], "contradiction_group_id": str(row[14]) if row[14] else None, "supersedes_claim_id": str(row[15]) if row[15] else None, "provenance": evidence_fields(row, 8)} for row in claims],
                "artifacts": [{"artifact_id": str(row[0]), "artifact_key": row[1], "artifact_type": row[2], "logical_version": row[3], "content_hash": row[4], "repository_or_store": row[5], "source_location": row[6], "canonical_revision": row[7], "historical_revision": row[8], "classification": row[9], "owner_ref": row[10], "availability": row[11], "storage_class": row[12], "retrieval_eligibility": row[13], "provenance_id": str(row[14]), "superseded_by": str(row[15]) if row[15] else None} for row in artifacts],
                "relationships": [{"relationship_id": str(row[0]), "subject_a_type": row[1], "subject_a_id": str(row[2]), "subject_b_type": row[3], "subject_b_id": str(row[4]), "relationship_type": row[5], "status": row[6], "effective_from": row[7].isoformat(), "effective_to": row[8].isoformat() if row[8] else None, "authority_ref": row[9], "provenance_id": str(row[10]), "classification": row[11], "visibility_policy_ref": row[12]} for row in relationships],
                "state_records": [{"state_id": str(row[0]), "state_class": row[1], "value_kind": row[2], "value_ref": row[3], "bounded_metadata": row[4], "classification": row[5], "retrieval_policy_ref": row[6], "status": row[7], "effective_from": row[8].isoformat(), "provenance_id": str(row[9])} for row in state_records],
                "contradictions": [{"contradiction_group_id": str(row[0]), "subject_type": row[1], "subject_id": str(row[2]), "status": row[3], "resolution_ref": row[4], "provenance_id": str(row[5])} for row in contradictions],
                "retrieval_metadata": [{"retrieval_id": str(row[0]), "target_type": row[1], "target_id": str(row[2]), "purpose": row[3], "classification": row[4], "policy_ref": row[5], "policy_version": row[6], "eligibility": row[7], "decision_reason": row[8], "freshness": row[9].isoformat() if row[9] else None, "availability": row[10], "selected_at": row[11].isoformat() if row[11] else None, "expired_at": row[12].isoformat() if row[12] else None, "evidence_id": str(row[13]) if row[13] else None} for row in retrieval],
            }

    def health(self) -> dict[str, Any]:
        with self._transaction() as (_, cursor):
            cursor.execute("SELECT 1")
            cursor.execute("SELECT version,checksum_sha256 FROM schema_migrations WHERE migration_id=%s", (MIGRATION_ID,))
            migration = cursor.fetchone()
            if not migration:
                raise RuntimeError(f"{DB_CHECKPOINT}: resident continuity migration is not applied.")
            for table in ("resident_offices", "resident_occupants", "resident_occupancies", "resident_evidence", "resident_claims"):
                cursor.execute("SELECT to_regclass(%s)", (f"public.{table}",))
                if cursor.fetchone()[0] is None:
                    raise RuntimeError(f"{DB_CHECKPOINT}: required resident table is missing: {table}.")
            cursor.execute("SELECT count(*) FROM resident_offices")
            offices = cursor.fetchone()[0]
            cursor.execute("SELECT count(*) FROM resident_occupants")
            occupants = cursor.fetchone()[0]
            return {"status": "healthy", "migration_id": MIGRATION_ID, "migration_version": migration[0], "offices": offices, "occupants": occupants}

    def bootstrap_jessica(self) -> BootstrapResult:
        """Idempotently persist only accepted Jessica identity and references."""

        evidence_specs = (
            EvidenceInput("c467:steward:jessica-identity", "Riverview Steward", "C465 current facts", "C465", None, "STEWARD_AUTHORIZED_FACT", "high", "accepted", accepted_by="Steward"),
            EvidenceInput("c467:accepted:office-character-architecture", "Riverview", "C466 office persistence contract", "C466", None, "ACCEPTED_INSTITUTIONAL_DECISION", "high", "accepted", accepted_by="C466 contract gate"),
            EvidenceInput("c464:recovery-corpus", "ppow1/theestate", "C464 recovery corpus manifest", "21af737b", "B46C1BAFB7C8DED8FC932918DEA30A63CC0D20459D1DB55A116B1BDBBE167745", "VERIFIED_PRIMARY_HISTORICAL_EVIDENCE", "high", "reference"),
            EvidenceInput("c465:identity-contract", "Riverview", "jessica_identity_continuity_contract_v1.json", "C465", None, "ACCEPTED_INSTITUTIONAL_DECISION", "high", "reference"),
            EvidenceInput("c466:persistence-contract", "Riverview", "resident_continuity_schema_contract_v1.json", "C466", None, "ACCEPTED_INSTITUTIONAL_DECISION", "high", "reference"),
            EvidenceInput("c464:missing-wp-4095-4130", "ppow1/theestate", "WP-4095-WP-4130 chat ingestion gap", "21af737b", None, "UNCERTAIN_OR_CONFLICTING_EVIDENCE", "unresolved", "gap", unresolved_status="missing_source"),
            EvidenceInput("c464:architect-identifier-conflict", "ppow1/theestate", "Chief Architect identifier conflict", "21af737b", None, "UNCERTAIN_OR_CONFLICTING_EVIDENCE", "unresolved", "contradiction", unresolved_status="conflicting_identifiers"),
        )
        with self._transaction() as (_, cursor):
            evidence = {item.source_key: self._evidence(cursor, item) for item in evidence_specs}
            office_id = stable_id("office:character-architecture")
            occupant_id = stable_id("occupant:jessica")
            cursor.execute("""INSERT INTO resident_offices(office_id,bootstrap_key,canonical_title,purpose_ref,authority_envelope_ref,policy_profile_ref,occupancy_policy,lifecycle_status,classification,provenance_id)
                VALUES(%s,'office:character-architecture','Office of Character Architecture','c465:office-purpose','c465:office-authority','resident-office-policy:single','single','active','internal',%s) ON CONFLICT(bootstrap_key) DO NOTHING""", (office_id, evidence["c467:accepted:office-character-architecture"]))
            cursor.execute("SELECT office_id,canonical_title FROM resident_offices WHERE bootstrap_key='office:character-architecture'")
            office = cursor.fetchone()
            if not office or office[1] != "Office of Character Architecture":
                raise RuntimeError(f"{CHECKPOINT}: Jessica bootstrap office conflict.")
            cursor.execute("""INSERT INTO resident_occupants(occupant_id,bootstrap_key,display_name,lifecycle_status,classification,canonical_anchor_ref,provenance_id)
                VALUES(%s,'occupant:jessica','Jessica','active','internal','c465:identity-anchor',%s) ON CONFLICT(bootstrap_key) DO NOTHING""", (occupant_id, evidence["c467:steward:jessica-identity"]))
            cursor.execute("SELECT occupant_id,display_name FROM resident_occupants WHERE bootstrap_key='occupant:jessica'")
            occupant = cursor.fetchone()
            if not occupant or occupant[1] != "Jessica":
                raise RuntimeError(f"{CHECKPOINT}: Jessica bootstrap occupant conflict.")
            occupancy_key = "bootstrap:jessica:office-occupancy:v1"
            occupancy_id = stable_id(f"occupancy:{occupancy_key}")
            cursor.execute("""INSERT INTO resident_occupancies(occupancy_id,idempotency_key,office_id,occupant_id,status,effective_from,assignment_reason_ref,assignment_authority_ref,provenance_id)
                VALUES(%s,%s,%s,%s,'active',now(),'Steward-established current office assignment','Steward',%s) ON CONFLICT(idempotency_key) DO NOTHING""", (occupancy_id, occupancy_key, office[0], occupant[0], evidence["c467:steward:jessica-identity"]))
            cursor.execute("SELECT occupancy_id FROM resident_occupancies WHERE idempotency_key=%s", (occupancy_key,))
            occupancy_id = cursor.fetchone()[0]
            claims = (("jessica:name", "name", "text", "Jessica", None, evidence["c467:steward:jessica-identity"], "STEWARD_AUTHORIZED_FACT", "high"), ("jessica:title", "office_title", "text", "Chief Character Architect", None, evidence["c467:steward:jessica-identity"], "STEWARD_AUTHORIZED_FACT", "high"), ("jessica:office", "office_binding", "reference", None, "office:character-architecture", evidence["c467:steward:jessica-identity"], "STEWARD_AUTHORIZED_FACT", "high"), ("jessica:name-origin", "name_origin", "text", "Steward-selected nod to Jessica Rabbit from Who Framed Roger Rabbit; no fictional traits imported", None, evidence["c467:steward:jessica-identity"], "STEWARD_AUTHORIZED_FACT", "high"))
            for key, predicate, kind, value, ref, ev, auth, confidence in claims:
                self._claim(cursor, stable_id(f"claim:{key}"), key, "occupant", occupant[0], predicate, kind, value, ref, ev, auth, confidence, "accepted", None, None)
            contradiction_id = stable_id("contradiction:historical-chief-architect-identifiers")
            cursor.execute("INSERT INTO resident_contradiction_groups(contradiction_group_id,subject_type,subject_id,status,provenance_id) VALUES(%s,'historical_architect_record',%s,'unresolved',%s) ON CONFLICT(contradiction_group_id) DO NOTHING", (contradiction_id, stable_id("historical:chief-architect-identifiers"), evidence["c464:architect-identifier-conflict"]))
            for key, value in (("historical:chief-architect-id-5", "employee/mailbox assignment variant 5"), ("historical:chief-architect-id-8", "employee/mailbox assignment variant 8")):
                self._claim(cursor, stable_id(f"claim:{key}"), key, "historical_architect_record", stable_id("historical:chief-architect-identifiers"), "historical_identifier", "text", value, None, evidence["c464:architect-identifier-conflict"], "UNCERTAIN_OR_CONFLICTING_EVIDENCE", "unresolved", "contradicted", contradiction_id, None)
            artifact_specs = (("c464:corpus", "recovery_corpus", "1.1", "B46C1BAFB7C8DED8FC932918DEA30A63CC0D20459D1DB55A116B1BDBBE167745", "docs/architecture/resident_localization/jessica_recovery_corpus_manifest_v1.json", evidence["c464:recovery-corpus"], "github", "eligible"), ("c465:identity-contract", "identity_contract", "1.0", "", "docs/architecture/resident_localization/jessica_identity_continuity_contract_v1.json", evidence["c465:identity-contract"], "github", "eligible"), ("c466:persistence-contract", "persistence_contract", "1.0", "", "docs/architecture/resident_localization/resident_continuity_schema_contract_v1.json", evidence["c466:persistence-contract"], "github", "eligible"), ("c464:missing-wp-4095-4130", "missing_source_marker", "1.0", "", "WP-4095-WP-4130 chat ingestion gap", evidence["c464:missing-wp-4095-4130"], "github", "review_required"))
            artifact_ids: list[UUID] = []
            for key, kind, version, content_hash, location, ev, storage, retrieval in artifact_specs:
                artifact_id = stable_id(f"artifact:{key}")
                cursor.execute("""INSERT INTO resident_artifact_references(artifact_id,artifact_key,artifact_type,logical_version,content_hash,repository_or_store,source_location,classification,owner_ref,subject_occupant_id,office_id,provenance_id,availability,storage_class,retrieval_eligibility)
                    VALUES(%s,%s,%s,%s,%s,'Riverview',%s,'internal','Office of Character Architecture',%s,%s,%s,'available',%s,%s) ON CONFLICT(artifact_key) DO NOTHING""", (artifact_id, key, kind, version, content_hash or f"reference:{key}", location, occupant[0], office[0], ev, storage, retrieval))
                cursor.execute("SELECT artifact_id FROM resident_artifact_references WHERE artifact_key=%s", (key,))
                artifact_ids.append(cursor.fetchone()[0])
            state_key = "state:jessica:professional-methods:c464-corrected"
            cursor.execute("""INSERT INTO resident_state_records(state_id,state_key,subject_occupant_id,state_class,value_kind,value_ref,bounded_metadata,provenance_id,classification,status)
                VALUES(%s,%s,%s,'professional_methods','reference','artifact:c464:corpus','{"method_count":13,"source":"C464/C465 correction"}'::jsonb,%s,'internal','active') ON CONFLICT(state_key) DO NOTHING""", (stable_id(state_key), state_key, occupant[0], evidence["c464:recovery-corpus"]))
            self._event(cursor, "office.created", "office", office[0], "bootstrap:jessica:office-created:v1", {"office_id": str(office[0]), "bootstrap_version": "1.0"})
            self._event(cursor, "resident.created", "occupant", occupant[0], "bootstrap:jessica:occupant-created:v1", {"occupant_id": str(occupant[0]), "bootstrap_version": "1.0"})
            self._event(cursor, "office.occupancy.started", "occupancy", occupancy_id, "bootstrap:jessica:occupancy-started:v1", {"occupancy_id": str(occupancy_id)})
            return BootstrapResult(office[0], occupant[0], occupancy_id, tuple(artifact_ids), contradiction_id, False)
