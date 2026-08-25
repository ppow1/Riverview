-- Resident continuity persistence foundation.
-- Version: 1.0.0 | Migration: 0041 | Campaign: C467
-- This migration stores bounded structured state and references only.

BEGIN;

CREATE TABLE IF NOT EXISTS resident_evidence (
    evidence_id uuid PRIMARY KEY,
    source_key text NOT NULL UNIQUE,
    source_repository_or_store text NOT NULL,
    source_location text NOT NULL,
    source_revision text,
    content_hash text,
    authority_class text NOT NULL CHECK (authority_class IN (
        'STEWARD_AUTHORIZED_FACT', 'ACCEPTED_INSTITUTIONAL_DECISION',
        'CANONICAL_CHARACTER_OR_RESIDENT_MATERIAL',
        'VERIFIED_PRIMARY_HISTORICAL_EVIDENCE', 'REFLECTION_CONTINUITY_EVIDENCE',
        'IMPLEMENTATION_HISTORY', 'DERIVED_OR_RECONSTRUCTED_INFERENCE',
        'UNCERTAIN_OR_CONFLICTING_EVIDENCE', 'OBSOLETE_OR_SUPERSEDED'
    )),
    confidence text NOT NULL CHECK (confidence IN ('high', 'medium', 'low', 'unresolved')),
    accepted_by text,
    accepted_at timestamptz,
    disposition text NOT NULL,
    classification text NOT NULL,
    superseded_by uuid REFERENCES resident_evidence(evidence_id),
    unresolved_status text,
    derived_from jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (accepted_at IS NULL OR accepted_by IS NOT NULL),
    CHECK (jsonb_typeof(derived_from) = 'array')
);

CREATE INDEX IF NOT EXISTS resident_evidence_authority_confidence_idx
    ON resident_evidence (authority_class, confidence, created_at DESC);
CREATE INDEX IF NOT EXISTS resident_evidence_unresolved_idx
    ON resident_evidence (unresolved_status) WHERE unresolved_status IS NOT NULL;

CREATE TABLE IF NOT EXISTS resident_offices (
    office_id uuid PRIMARY KEY,
    bootstrap_key text NOT NULL UNIQUE,
    canonical_title text NOT NULL,
    purpose_ref text NOT NULL,
    authority_envelope_ref text NOT NULL,
    policy_profile_ref text NOT NULL,
    occupancy_policy text NOT NULL CHECK (occupancy_policy IN ('single', 'multiple')),
    lifecycle_status text NOT NULL CHECK (lifecycle_status IN ('proposed', 'active', 'superseded', 'retired')),
    classification text NOT NULL,
    provenance_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    superseded_by uuid REFERENCES resident_offices(office_id),
    version integer NOT NULL DEFAULT 1 CHECK (version > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    effective_from timestamptz NOT NULL DEFAULT now(),
    retired_at timestamptz
);

CREATE INDEX IF NOT EXISTS resident_offices_status_idx ON resident_offices (lifecycle_status, canonical_title);

CREATE TABLE IF NOT EXISTS resident_occupants (
    occupant_id uuid PRIMARY KEY,
    bootstrap_key text NOT NULL UNIQUE,
    display_name text NOT NULL,
    lifecycle_status text NOT NULL CHECK (lifecycle_status IN ('proposed', 'active', 'suspended', 'retired', 'archived')),
    classification text NOT NULL,
    canonical_anchor_ref text,
    provenance_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    version integer NOT NULL DEFAULT 1 CHECK (version > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    retired_at timestamptz
);

CREATE INDEX IF NOT EXISTS resident_occupants_status_idx ON resident_occupants (lifecycle_status, display_name);

CREATE TABLE IF NOT EXISTS resident_office_aliases (
    alias_id uuid PRIMARY KEY,
    office_id uuid NOT NULL REFERENCES resident_offices(office_id),
    alias text NOT NULL,
    alias_kind text NOT NULL,
    provenance_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    effective_from timestamptz NOT NULL DEFAULT now(),
    effective_to timestamptz,
    UNIQUE (office_id, alias, effective_from)
);

CREATE INDEX IF NOT EXISTS resident_office_alias_lookup_idx ON resident_office_aliases (alias);

CREATE TABLE IF NOT EXISTS resident_artifact_references (
    artifact_id uuid PRIMARY KEY,
    artifact_key text NOT NULL UNIQUE,
    artifact_type text NOT NULL,
    logical_version text NOT NULL,
    content_hash text NOT NULL,
    repository_or_store text NOT NULL,
    source_location text NOT NULL,
    canonical_revision text,
    historical_revision text,
    classification text NOT NULL,
    owner_ref text NOT NULL,
    subject_occupant_id uuid REFERENCES resident_occupants(occupant_id),
    office_id uuid REFERENCES resident_offices(office_id),
    provenance_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    superseded_by uuid REFERENCES resident_artifact_references(artifact_id),
    availability text NOT NULL CHECK (availability IN ('available', 'unavailable', 'superseded', 'archived')),
    storage_class text NOT NULL CHECK (storage_class IN ('github', 'protected_local', 'external_reference', 'postgresql_metadata')),
    retrieval_eligibility text NOT NULL CHECK (retrieval_eligibility IN ('eligible', 'blocked', 'review_required', 'expired')),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (repository_or_store, source_location, canonical_revision, content_hash)
);

CREATE INDEX IF NOT EXISTS resident_artifact_hash_idx ON resident_artifact_references (content_hash);
CREATE INDEX IF NOT EXISTS resident_artifact_subject_idx ON resident_artifact_references (subject_occupant_id, office_id);
CREATE INDEX IF NOT EXISTS resident_artifact_retrieval_idx ON resident_artifact_references (retrieval_eligibility, classification);

CREATE TABLE IF NOT EXISTS resident_occupancies (
    occupancy_id uuid PRIMARY KEY,
    idempotency_key text NOT NULL UNIQUE,
    office_id uuid NOT NULL REFERENCES resident_offices(office_id),
    occupant_id uuid NOT NULL REFERENCES resident_occupants(occupant_id),
    status text NOT NULL CHECK (status IN ('active', 'ended', 'superseded', 'proposed')),
    effective_from timestamptz NOT NULL,
    effective_to timestamptz,
    assignment_reason_ref text NOT NULL,
    assignment_authority_ref text NOT NULL,
    provenance_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    end_idempotency_key text UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    ended_at timestamptz,
    version integer NOT NULL DEFAULT 1 CHECK (version > 0),
    CHECK (effective_to IS NULL OR effective_to > effective_from),
    CHECK ((status = 'active' AND effective_to IS NULL) OR status <> 'active')
);

CREATE INDEX IF NOT EXISTS resident_occupancy_office_current_idx
    ON resident_occupancies (office_id, status, effective_from DESC);
CREATE INDEX IF NOT EXISTS resident_occupancy_occupant_history_idx
    ON resident_occupancies (occupant_id, effective_from DESC);

CREATE TABLE IF NOT EXISTS resident_implementations (
    implementation_id uuid PRIMARY KEY,
    implementation_key text NOT NULL UNIQUE,
    implementation_class text NOT NULL,
    provider_ref text,
    model_ref text,
    host_ref text,
    device_ref text,
    capability_profile_ref text,
    implementation_version text NOT NULL,
    classification_eligibility_ref text,
    configuration_ref text,
    lifecycle_status text NOT NULL CHECK (lifecycle_status IN ('registered', 'eligible', 'active', 'failed', 'retired', 'archived')),
    provenance_id uuid REFERENCES resident_evidence(evidence_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    retired_at timestamptz
);

CREATE TABLE IF NOT EXISTS resident_implementation_bindings (
    binding_id uuid PRIMARY KEY,
    idempotency_key text NOT NULL UNIQUE,
    occupant_id uuid NOT NULL REFERENCES resident_occupants(occupant_id),
    implementation_id uuid NOT NULL REFERENCES resident_implementations(implementation_id),
    purpose text NOT NULL,
    status text NOT NULL CHECK (status IN ('active', 'ended', 'retired', 'proposed')),
    effective_from timestamptz NOT NULL,
    effective_to timestamptz,
    policy_ref text NOT NULL,
    activation_evidence_id uuid REFERENCES resident_evidence(evidence_id),
    retirement_evidence_id uuid REFERENCES resident_evidence(evidence_id),
    predecessor_binding_id uuid REFERENCES resident_implementation_bindings(binding_id),
    successor_binding_id uuid REFERENCES resident_implementation_bindings(binding_id),
    retirement_idempotency_key text UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (effective_to IS NULL OR effective_to > effective_from),
    CHECK ((status = 'active' AND effective_to IS NULL) OR status <> 'active')
);

CREATE INDEX IF NOT EXISTS resident_binding_current_idx
    ON resident_implementation_bindings (occupant_id, purpose, status);
CREATE INDEX IF NOT EXISTS resident_binding_implementation_idx
    ON resident_implementation_bindings (implementation_id, effective_from DESC);

CREATE TABLE IF NOT EXISTS resident_contradiction_groups (
    contradiction_group_id uuid PRIMARY KEY,
    subject_type text NOT NULL,
    subject_id uuid NOT NULL,
    status text NOT NULL CHECK (status IN ('unresolved', 'resolved', 'accepted_split', 'archived')),
    resolution_ref text,
    provenance_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz
);

CREATE TABLE IF NOT EXISTS resident_claims (
    claim_id uuid PRIMARY KEY,
    claim_key text NOT NULL UNIQUE,
    subject_type text NOT NULL,
    subject_id uuid NOT NULL,
    controlled_predicate text NOT NULL,
    value_kind text NOT NULL CHECK (value_kind IN ('text', 'number', 'boolean', 'reference', 'interval', 'artifact')),
    value_text text,
    value_reference text,
    evidence_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    authority_class text NOT NULL CHECK (authority_class IN (
        'STEWARD_AUTHORIZED_FACT', 'ACCEPTED_INSTITUTIONAL_DECISION',
        'CANONICAL_CHARACTER_OR_RESIDENT_MATERIAL',
        'VERIFIED_PRIMARY_HISTORICAL_EVIDENCE', 'REFLECTION_CONTINUITY_EVIDENCE',
        'IMPLEMENTATION_HISTORY', 'DERIVED_OR_RECONSTRUCTED_INFERENCE',
        'UNCERTAIN_OR_CONFLICTING_EVIDENCE', 'OBSOLETE_OR_SUPERSEDED'
    )),
    confidence text NOT NULL CHECK (confidence IN ('high', 'medium', 'low', 'unresolved')),
    status text NOT NULL CHECK (status IN ('proposed', 'accepted', 'rejected', 'superseded', 'unresolved', 'contradicted')),
    contradiction_group_id uuid REFERENCES resident_contradiction_groups(contradiction_group_id),
    supersedes_claim_id uuid REFERENCES resident_claims(claim_id),
    derived_from jsonb NOT NULL DEFAULT '[]'::jsonb,
    effective_from timestamptz NOT NULL DEFAULT now(),
    effective_to timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((value_kind IN ('text', 'number', 'boolean') AND value_text IS NOT NULL) OR (value_kind IN ('reference', 'artifact', 'interval') AND value_reference IS NOT NULL)),
    CHECK (jsonb_typeof(derived_from) = 'array')
);

CREATE INDEX IF NOT EXISTS resident_claim_subject_idx ON resident_claims (subject_type, subject_id, status);
CREATE INDEX IF NOT EXISTS resident_claim_contradiction_idx ON resident_claims (contradiction_group_id);
CREATE INDEX IF NOT EXISTS resident_claim_supersession_idx ON resident_claims (supersedes_claim_id);

CREATE TABLE IF NOT EXISTS resident_relationships (
    relationship_id uuid PRIMARY KEY,
    relationship_key text NOT NULL UNIQUE,
    subject_a_type text NOT NULL,
    subject_a_id uuid NOT NULL,
    subject_b_type text NOT NULL,
    subject_b_id uuid NOT NULL,
    relationship_type text NOT NULL,
    status text NOT NULL CHECK (status IN ('proposed', 'active', 'ended', 'superseded', 'archived')),
    effective_from timestamptz NOT NULL DEFAULT now(),
    effective_to timestamptz,
    authority_ref text NOT NULL,
    provenance_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    classification text NOT NULL,
    visibility_policy_ref text NOT NULL,
    notes_ref text,
    version integer NOT NULL DEFAULT 1 CHECK (version > 0),
    CHECK (subject_a_id <> subject_b_id),
    CHECK (effective_to IS NULL OR effective_to > effective_from)
);

CREATE INDEX IF NOT EXISTS resident_relationship_subject_idx
    ON resident_relationships (subject_a_type, subject_a_id, status);
CREATE INDEX IF NOT EXISTS resident_relationship_target_idx
    ON resident_relationships (subject_b_type, subject_b_id, status);

CREATE TABLE IF NOT EXISTS resident_state_records (
    state_id uuid PRIMARY KEY,
    state_key text NOT NULL UNIQUE,
    subject_occupant_id uuid REFERENCES resident_occupants(occupant_id),
    subject_office_id uuid REFERENCES resident_offices(office_id),
    state_class text NOT NULL CHECK (state_class IN (
        'canonical_identity', 'office_role_knowledge', 'professional_doctrine',
        'professional_methods', 'accepted_resident_canon', 'relationship_state',
        'working_memory_current_assignment', 'episodic_institutional_history',
        'reflection_renewal', 'implementation_transition_history', 'preferences',
        'lessons_learned', 'artifact_references', 'source_references',
        'uncertain_claims', 'private_protected_references', 'temporary_context',
        'derived_summaries'
    )),
    value_kind text NOT NULL CHECK (value_kind IN ('reference', 'bounded_metadata', 'protected_reference')),
    value_ref text NOT NULL,
    bounded_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    provenance_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    classification text NOT NULL,
    retrieval_policy_ref text,
    status text NOT NULL CHECK (status IN ('active', 'superseded', 'expired', 'archived')),
    effective_from timestamptz NOT NULL DEFAULT now(),
    effective_to timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    version integer NOT NULL DEFAULT 1 CHECK (version > 0),
    CHECK (subject_occupant_id IS NOT NULL OR subject_office_id IS NOT NULL),
    CHECK (jsonb_typeof(bounded_metadata) = 'object')
);

CREATE INDEX IF NOT EXISTS resident_state_subject_class_idx
    ON resident_state_records (subject_occupant_id, state_class, status);

CREATE TABLE IF NOT EXISTS resident_change_proposals (
    proposal_id uuid PRIMARY KEY,
    proposal_key text NOT NULL UNIQUE,
    proposer_ref text NOT NULL,
    subject_type text NOT NULL,
    subject_id uuid NOT NULL,
    change_class text NOT NULL,
    target_ref text NOT NULL,
    proposal_ref text NOT NULL,
    status text NOT NULL CHECK (status IN ('draft', 'recorded', 'under_review', 'accepted', 'rejected', 'superseded', 'withdrawn')),
    provenance_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    classification text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    reviewed_at timestamptz
);

CREATE TABLE IF NOT EXISTS resident_change_reviews (
    review_id uuid PRIMARY KEY,
    proposal_id uuid NOT NULL REFERENCES resident_change_proposals(proposal_id),
    reviewer_ref text NOT NULL,
    reviewer_capability_ref text NOT NULL,
    decision text NOT NULL CHECK (decision IN ('accepted', 'rejected', 'unresolved')),
    authority_ref text NOT NULL,
    evidence_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    reason_ref text NOT NULL,
    reviewed_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS resident_canonical_mutations (
    mutation_id uuid PRIMARY KEY,
    proposal_id uuid NOT NULL REFERENCES resident_change_proposals(proposal_id),
    review_id uuid NOT NULL REFERENCES resident_change_reviews(review_id),
    target_type text NOT NULL,
    target_id uuid NOT NULL,
    predecessor_version integer,
    successor_version integer NOT NULL CHECK (successor_version > 0),
    authority_ref text NOT NULL,
    evidence_id uuid NOT NULL REFERENCES resident_evidence(evidence_id),
    status text NOT NULL CHECK (status IN ('accepted', 'reconciled', 'revoked')),
    accepted_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (proposal_id, review_id, successor_version)
);

CREATE TABLE IF NOT EXISTS resident_retrieval_metadata (
    retrieval_id uuid PRIMARY KEY,
    target_type text NOT NULL,
    target_id uuid NOT NULL,
    purpose text NOT NULL,
    classification text NOT NULL,
    policy_ref text,
    policy_version text,
    eligibility text NOT NULL CHECK (eligibility IN ('eligible', 'blocked', 'review_required', 'expired')),
    decision_reason text NOT NULL,
    freshness timestamptz,
    availability text NOT NULL CHECK (availability IN ('available', 'unavailable', 'superseded')),
    selected_at timestamptz,
    expired_at timestamptz,
    evidence_id uuid REFERENCES resident_evidence(evidence_id),
    UNIQUE (target_type, target_id, purpose, policy_version)
);

COMMIT;
