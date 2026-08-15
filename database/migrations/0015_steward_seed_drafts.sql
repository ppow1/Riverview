-- Riverview bounded Steward seed drafts
-- Migration: 0015

BEGIN;

CREATE TABLE steward_seed_drafts (
    seed_id uuid PRIMARY KEY,
    correlation_id uuid NOT NULL,
    causation_id uuid,
    consumer_id text NOT NULL CHECK (consumer_id = 'chatgpt:riverview_001'),
    seed_text text NOT NULL CHECK (length(btrim(seed_text)) BETWEEN 1 AND 8000),
    classification text NOT NULL CHECK (classification IN ('river','internal')),
    status text NOT NULL CHECK (status IN ('draft','confirmed','promoted','rejected')),
    objective_id uuid REFERENCES objectives(objective_id),
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    confirmed_at timestamptz,
    promoted_at timestamptz
);

COMMIT;
