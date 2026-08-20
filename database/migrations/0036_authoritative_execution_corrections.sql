-- Append-only correction evidence for independently disproven execution completion.
-- Migration: 0036

BEGIN;

CREATE TABLE execution_reconciliation_corrections (
    correction_id uuid PRIMARY KEY,
    execution_id uuid NOT NULL REFERENCES execution_envelopes(execution_id),
    correlation_id uuid NOT NULL,
    prior_decision text NOT NULL CHECK (prior_decision='accepted'),
    corrected_decision text NOT NULL CHECK (corrected_decision='checkpoint'),
    reason text NOT NULL,
    evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

COMMIT;
