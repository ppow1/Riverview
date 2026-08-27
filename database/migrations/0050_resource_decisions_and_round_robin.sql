-- Durable planner decisions and round-robin cursor.
-- Migration: 0050

BEGIN;

ALTER TABLE resource_policy
    ADD COLUMN IF NOT EXISTS round_robin_cursor bigint NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS resource_planner_decisions (
    decision_id uuid PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    policy_id text NOT NULL REFERENCES resource_policy(policy_id),
    policy_revision bigint NOT NULL,
    policy_mode text NOT NULL,
    policy_parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    work_id text NOT NULL,
    owner_id text NOT NULL,
    candidates jsonb NOT NULL,
    ranking jsonb NOT NULL,
    claim_attempts jsonb NOT NULL,
    selected_seat text CHECK (selected_seat IN ('C1','C2','C3')),
    selected_fingerprint text,
    claim_id uuid REFERENCES resource_seat_claims(claim_id),
    execution_correlation_id text,
    fallback_used boolean NOT NULL DEFAULT false,
    decision_reason text NOT NULL
);

CREATE INDEX IF NOT EXISTS resource_planner_decisions_created_idx
    ON resource_planner_decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS resource_planner_decisions_work_idx
    ON resource_planner_decisions(work_id,created_at DESC);

COMMIT;
