-- Campaign Runner package-level self-repair and final acceptance projection.
-- Version: 0.1.0
-- Migration: 0042

BEGIN;

CREATE TABLE campaign_package_runs (
    package_run_id uuid PRIMARY KEY,
    objective_id uuid NOT NULL REFERENCES objectives(objective_id),
    stage_id uuid NOT NULL REFERENCES objective_stages(stage_id),
    state text NOT NULL CHECK (state IN (
        'executing','repairing','verifying','awaiting_independent_acceptance',
        'acceptance_failed','accepted','escalated'
    )),
    repair_generation integer NOT NULL DEFAULT 0 CHECK (repair_generation >= 0),
    discovery_sequence integer NOT NULL DEFAULT 0 CHECK (discovery_sequence >= 0),
    worktree_ref text NOT NULL CHECK (length(worktree_ref) BETWEEN 1 AND 2048),
    candidate_ref text,
    candidate_version_hash text,
    internal_verification jsonb NOT NULL DEFAULT '{}'::jsonb,
    acceptance_dispatch_count integer NOT NULL DEFAULT 0 CHECK (acceptance_dispatch_count >= 0),
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(stage_id)
);

CREATE INDEX campaign_package_runs_objective_idx
    ON campaign_package_runs(objective_id, state, updated_at);

CREATE TABLE campaign_repair_ledger (
    ledger_id uuid PRIMARY KEY,
    package_run_id uuid NOT NULL REFERENCES campaign_package_runs(package_run_id),
    objective_id uuid NOT NULL REFERENCES objectives(objective_id),
    stage_id uuid NOT NULL REFERENCES objective_stages(stage_id),
    defect_id uuid REFERENCES campaign_validation_defects(defect_id),
    root_cause_key text NOT NULL CHECK (length(root_cause_key) BETWEEN 1 AND 256),
    discovery_sequence integer NOT NULL CHECK (discovery_sequence > 0),
    checkpoint text NOT NULL CHECK (length(checkpoint) BETWEEN 1 AND 256),
    failing_command text,
    observed_behavior text NOT NULL,
    expected_behavior text NOT NULL,
    stdout_ref text,
    stderr_ref text,
    evidence_ref text NOT NULL,
    root_cause text NOT NULL,
    repair_description text,
    changed_paths jsonb NOT NULL DEFAULT '[]'::jsonb,
    repair_verification text,
    verification_result text NOT NULL CHECK (verification_result IN ('pending','passed','failed')),
    repair_generation integer NOT NULL CHECK (repair_generation >= 0),
    status text NOT NULL CHECK (status IN ('observed','repairing','repaired','escalated')),
    first_observed_at timestamptz NOT NULL DEFAULT now(),
    repaired_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(package_run_id, discovery_sequence)
);

CREATE INDEX campaign_repair_ledger_stage_idx
    ON campaign_repair_ledger(stage_id, discovery_sequence);

COMMIT;
