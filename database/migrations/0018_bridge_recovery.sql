-- Riverview bridge replay and recovery
-- Version: 0.18.0
-- Migration: 0018

BEGIN;

CREATE TABLE bridge_recovery_attempts (
    recovery_id uuid PRIMARY KEY,
    request_id uuid NOT NULL,
    correlation_id uuid NOT NULL,
    operation text NOT NULL CHECK (operation IN ('wake','mcp')),
    attempt_key text NOT NULL UNIQUE,
    state text NOT NULL CHECK (state IN ('pending','retryable','recovered','escalated')),
    failure_class text,
    attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    max_attempts integer NOT NULL CHECK (max_attempts BETWEEN 1 AND 3),
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    escalation_id uuid REFERENCES steward_escalations(escalation_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz
);

CREATE INDEX bridge_recovery_correlation_idx
    ON bridge_recovery_attempts(correlation_id, created_at);

COMMIT;
