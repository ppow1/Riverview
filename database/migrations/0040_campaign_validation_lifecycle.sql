-- Campaign Runner writer/validator lifecycle persistence and gates.
-- Version: 0.1.0
-- Migration: 0040

BEGIN;

ALTER TABLE objectives
    ADD COLUMN attention_required boolean NOT NULL DEFAULT false,
    ADD COLUMN acceptance_state text NOT NULL DEFAULT 'pending'
        CHECK (acceptance_state IN ('pending','awaiting_validation','accepted','rejected'));

CREATE TABLE campaign_validation_bases (
    basis_id uuid PRIMARY KEY,
    objective_id uuid NOT NULL REFERENCES objectives(objective_id),
    stage_id uuid NOT NULL REFERENCES objective_stages(stage_id),
    specification_ref text,
    specification_content text,
    specification_hash text NOT NULL CHECK (length(specification_hash) BETWEEN 1 AND 128),
    acceptance_criteria jsonb NOT NULL DEFAULT '[]'::jsonb,
    evidence_requirements jsonb NOT NULL DEFAULT '[]'::jsonb,
    original_base_sha text NOT NULL CHECK (length(original_base_sha) BETWEEN 1 AND 128),
    allowed_paths jsonb NOT NULL DEFAULT '[]'::jsonb,
    validation_commands jsonb NOT NULL DEFAULT '[]'::jsonb,
    expected_outputs jsonb NOT NULL DEFAULT '[]'::jsonb,
    basis_revision integer NOT NULL DEFAULT 1 CHECK (basis_revision > 0),
    supersedes_basis_id uuid REFERENCES campaign_validation_bases(basis_id),
    created_by text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(stage_id, basis_revision),
    CHECK (specification_ref IS NOT NULL OR specification_content IS NOT NULL)
);

CREATE INDEX campaign_validation_bases_stage_idx
    ON campaign_validation_bases(stage_id, basis_revision DESC);

ALTER TABLE objective_stages
    ADD COLUMN phase_key text NOT NULL DEFAULT 'default',
    ADD COLUMN phase_title text NOT NULL DEFAULT 'Default',
    ADD COLUMN eligible_seats jsonb NOT NULL DEFAULT '["C1","C2","C3"]'::jsonb,
    ADD COLUMN estimated_progress_units integer NOT NULL DEFAULT 15
        CHECK (estimated_progress_units > 0),
    ADD COLUMN blocked_reason text,
    ADD COLUMN last_progress_at timestamptz,
    ADD COLUMN progress_count integer NOT NULL DEFAULT 0
        CHECK (progress_count >= 0),
    ADD COLUMN runner_state text NOT NULL DEFAULT 'queued'
        CHECK (runner_state IN (
            'queued','claimed','running','validation_pending','validation_running',
            'defects_found','repair_pending','repair_running','revalidation_pending',
            'revalidation_running','accepted','blocked','failed','timed_out'
        )),
    ADD COLUMN validation_basis_id uuid REFERENCES campaign_validation_bases(basis_id),
    ADD COLUMN writer_attempt_id uuid REFERENCES work_order_attempts(attempt_id),
    ADD COLUMN validator_attempt_id uuid REFERENCES work_order_attempts(attempt_id),
    ADD COLUMN repair_attempt_id uuid REFERENCES work_order_attempts(attempt_id),
    ADD COLUMN revalidation_attempt_id uuid REFERENCES work_order_attempts(attempt_id),
    ADD COLUMN last_state_transition_at timestamptz;

CREATE INDEX objective_stage_runner_state_idx
    ON objective_stages(objective_id, runner_state, sort_order);

ALTER TABLE work_orders
    ADD COLUMN objective_id uuid REFERENCES objectives(objective_id),
    ADD COLUMN stage_id uuid REFERENCES objective_stages(stage_id),
    ADD COLUMN validation_basis_id uuid REFERENCES campaign_validation_bases(basis_id),
    ADD COLUMN source_work_order_id uuid REFERENCES work_orders(work_order_id),
    ADD COLUMN source_attempt_id uuid REFERENCES work_order_attempts(attempt_id);

ALTER TABLE execution_envelopes
    ADD COLUMN validation_basis_id uuid REFERENCES campaign_validation_bases(basis_id);

ALTER TABLE execution_results
    ADD COLUMN validation_basis_id uuid REFERENCES campaign_validation_bases(basis_id),
    ADD COLUMN validation_verdict text
        CHECK (validation_verdict IS NULL OR validation_verdict IN ('PASS','FAIL','BLOCKED'));

CREATE INDEX work_orders_campaign_dispatch_idx
    ON work_orders(objective_id, stage_id, role, status, created_at)
    WHERE objective_id IS NOT NULL;

CREATE INDEX work_orders_source_attempt_idx
    ON work_orders(source_attempt_id) WHERE source_attempt_id IS NOT NULL;

CREATE TABLE campaign_validation_results (
    validation_result_id uuid PRIMARY KEY,
    work_order_id uuid NOT NULL REFERENCES work_orders(work_order_id),
    validation_attempt_id uuid NOT NULL UNIQUE REFERENCES work_order_attempts(attempt_id),
    writer_attempt_id uuid NOT NULL REFERENCES work_order_attempts(attempt_id),
    repair_attempt_id uuid REFERENCES work_order_attempts(attempt_id),
    basis_id uuid NOT NULL REFERENCES campaign_validation_bases(basis_id),
    basis_hash text NOT NULL CHECK (length(basis_hash) BETWEEN 1 AND 128),
    verdict text NOT NULL CHECK (verdict IN ('PASS','FAIL','BLOCKED')),
    result_version_hash text NOT NULL CHECK (length(result_version_hash) BETWEEN 1 AND 128),
    implementation_ref text,
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    findings_summary jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    idempotency_key text NOT NULL UNIQUE
);

CREATE INDEX campaign_validation_results_writer_idx
    ON campaign_validation_results(writer_attempt_id, created_at);

CREATE TABLE campaign_validation_defects (
    defect_id uuid PRIMARY KEY,
    objective_id uuid NOT NULL REFERENCES objectives(objective_id),
    stage_id uuid NOT NULL REFERENCES objective_stages(stage_id),
    validation_result_id uuid NOT NULL REFERENCES campaign_validation_results(validation_result_id),
    validation_attempt_id uuid NOT NULL REFERENCES work_order_attempts(attempt_id),
    writer_attempt_id uuid NOT NULL REFERENCES work_order_attempts(attempt_id),
    acceptance_criterion_ref text NOT NULL,
    severity text NOT NULL CHECK (severity IN ('blocking','non_blocking')),
    expected_behavior text NOT NULL,
    observed_behavior text NOT NULL,
    evidence_ref text NOT NULL,
    required_repair text NOT NULL,
    state text NOT NULL DEFAULT 'unresolved'
        CHECK (state IN ('unresolved','resolved','superseded')),
    repair_attempt_id uuid REFERENCES work_order_attempts(attempt_id),
    resolution_attempt_id uuid REFERENCES work_order_attempts(attempt_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz
);

CREATE INDEX campaign_validation_defects_open_idx
    ON campaign_validation_defects(stage_id, state, severity);

COMMIT;
