-- Riverview autonomous control plane
-- Migration: 0014

BEGIN;

CREATE TABLE capabilities (
    capability_id uuid PRIMARY KEY,
    capability_name text NOT NULL UNIQUE,
    provider_id text NOT NULL,
    version text NOT NULL,
    supported_tasks jsonb NOT NULL,
    restrictions jsonb NOT NULL,
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    health_status text NOT NULL CHECK (health_status IN ('unknown','healthy','unhealthy','disabled')),
    measured_at timestamptz,
    enabled boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE capability_capacity (
    capability_id uuid PRIMARY KEY REFERENCES capabilities(capability_id),
    available boolean NOT NULL,
    concurrency_limit integer NOT NULL CHECK (concurrency_limit > 0),
    current_load integer NOT NULL CHECK (current_load >= 0),
    fuel jsonb NOT NULL DEFAULT '{}'::jsonb,
    backoff_until timestamptz,
    observed_at timestamptz NOT NULL DEFAULT now(),
    CHECK (current_load <= concurrency_limit)
);

CREATE TABLE execution_envelopes (
    execution_id uuid PRIMARY KEY,
    work_order_id uuid REFERENCES work_orders(work_order_id),
    objective_id uuid REFERENCES objectives(objective_id),
    stage_id uuid REFERENCES objective_stages(stage_id),
    correlation_id uuid NOT NULL,
    causation_id uuid,
    capability_name text NOT NULL REFERENCES capabilities(capability_name),
    repository_identity text NOT NULL,
    repository_root text NOT NULL,
    expected_base_sha text NOT NULL,
    bounded_instruction text NOT NULL CHECK (length(btrim(bounded_instruction)) BETWEEN 1 AND 16000),
    allowed_paths jsonb NOT NULL,
    acceptance_criteria jsonb NOT NULL,
    evidence_requirements jsonb NOT NULL,
    timeout_seconds integer NOT NULL CHECK (timeout_seconds BETWEEN 1 AND 86400),
    retry_key text NOT NULL UNIQUE,
    classification text NOT NULL CHECK (classification IN ('river','internal')),
    status text NOT NULL CHECK (status IN ('queued','running','succeeded','failed','timed_out','reconciled','escalated')),
    created_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz,
    finished_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX execution_envelopes_status_idx ON execution_envelopes(status, created_at);

CREATE TABLE execution_results (
    result_id uuid PRIMARY KEY,
    execution_id uuid NOT NULL UNIQUE REFERENCES execution_envelopes(execution_id),
    correlation_id uuid NOT NULL,
    provider_id text NOT NULL,
    result_category text NOT NULL CHECK (result_category IN ('succeeded','failed','timed_out','interrupted','rejected')),
    exit_state text NOT NULL,
    changed_paths jsonb NOT NULL DEFAULT '[]'::jsonb,
    validation_evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    commit_sha text,
    remote_verified_sha text,
    checkpoint_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    artifact_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    bounded_summary text NOT NULL CHECK (length(btrim(bounded_summary)) BETWEEN 1 AND 4000),
    started_at timestamptz NOT NULL,
    finished_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE grace_transition_evaluations (
    evaluation_id uuid PRIMARY KEY,
    objective_id uuid NOT NULL REFERENCES objectives(objective_id),
    stage_id uuid REFERENCES objective_stages(stage_id),
    correlation_id uuid NOT NULL,
    decision text NOT NULL CHECK (decision IN ('ready','blocked','stale','running','completed','checkpoint')),
    reason text NOT NULL,
    next_action text,
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE grace_checkpoints (
    checkpoint_id uuid PRIMARY KEY,
    checkpoint_code text NOT NULL,
    subject_type text NOT NULL,
    subject_id uuid,
    correlation_id uuid NOT NULL,
    reason text NOT NULL,
    required_action text NOT NULL,
    state text NOT NULL CHECK (state IN ('open','acknowledged','resolved')),
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz
);

COMMIT;
