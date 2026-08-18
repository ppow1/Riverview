-- Riverview typed Steward engineering-intent formation
-- Migration: 0032

BEGIN;

CREATE TABLE engineering_intents (
    intent_id uuid PRIMARY KEY,
    seed_id uuid NOT NULL REFERENCES steward_seed_drafts(seed_id),
    objective_id uuid NOT NULL REFERENCES objectives(objective_id),
    stage_id uuid NOT NULL REFERENCES objective_stages(stage_id),
    request_hash text NOT NULL,
    repository_identity text NOT NULL,
    repository_root text NOT NULL,
    expected_base_sha text NOT NULL CHECK (length(expected_base_sha)=40),
    bounded_instruction text NOT NULL CHECK (length(btrim(bounded_instruction)) BETWEEN 1 AND 16000),
    allowed_paths jsonb NOT NULL,
    acceptance_criteria jsonb NOT NULL,
    evidence_requirements jsonb NOT NULL,
    capability_name text NOT NULL REFERENCES capabilities(capability_name),
    action_type text NOT NULL REFERENCES approved_actions(action_type),
    timeout_seconds integer NOT NULL CHECK (timeout_seconds BETWEEN 1 AND 86400),
    classification text NOT NULL CHECK (classification IN ('river','internal')),
    correlation_id uuid NOT NULL,
    causation_id uuid,
    idempotency_key text NOT NULL UNIQUE,
    approved_by text NOT NULL CHECK (approved_by='steward'),
    write_policy text NOT NULL CHECK (write_policy='read_only'),
    status text NOT NULL CHECK (status IN ('bound','running','succeeded','failed','reconciled','escalated')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(objective_id, stage_id)
);

CREATE INDEX engineering_intents_seed_idx ON engineering_intents(seed_id, created_at);
CREATE INDEX engineering_intents_status_idx ON engineering_intents(status, updated_at);

INSERT INTO approved_actions(action_type,action_version,command_path,command_sha256,parameter_schema,expected_duration_seconds,hard_timeout_seconds,retry_safe,enabled)
VALUES (
    'codex.engineering.v1','1.0.0','internal:codex-cli-adapter','internal:codex-cli-adapter',
    '{"type":"object","properties":{"engineering_intent_id":{"type":"string","format":"uuid"}},"required":["engineering_intent_id"],"additionalProperties":false}'::jsonb,
    300,900,false,true
)
ON CONFLICT(action_type) DO UPDATE SET
    action_version=EXCLUDED.action_version,
    parameter_schema=EXCLUDED.parameter_schema,
    expected_duration_seconds=EXCLUDED.expected_duration_seconds,
    hard_timeout_seconds=EXCLUDED.hard_timeout_seconds,
    enabled=EXCLUDED.enabled,
    updated_at=now();

COMMIT;
