-- Comms5 governed draft lifecycle history.
-- Migration: 0028

BEGIN;

ALTER TABLE steward_seed_drafts
    DROP CONSTRAINT IF EXISTS steward_seed_drafts_status_check;

ALTER TABLE steward_seed_drafts
    ADD CONSTRAINT steward_seed_drafts_status_check
    CHECK (status IN ('draft','confirmed','promoted','rejected','cancelled','superseded'));

ALTER TABLE steward_seed_drafts
    ADD COLUMN IF NOT EXISTS cancelled_at timestamptz,
    ADD COLUMN IF NOT EXISTS cancellation_reason text,
    ADD COLUMN IF NOT EXISTS cancelled_by text,
    ADD COLUMN IF NOT EXISTS superseded_at timestamptz,
    ADD COLUMN IF NOT EXISTS replacement_seed_id uuid REFERENCES steward_seed_drafts(seed_id),
    ADD COLUMN IF NOT EXISTS supersedes_seed_id uuid REFERENCES steward_seed_drafts(seed_id);

CREATE TABLE IF NOT EXISTS steward_seed_lifecycle_events (
    lifecycle_event_id uuid PRIMARY KEY,
    seed_id uuid NOT NULL REFERENCES steward_seed_drafts(seed_id),
    transition text NOT NULL CHECK (transition IN ('cancelled','superseded')),
    replacement_seed_id uuid REFERENCES steward_seed_drafts(seed_id),
    actor text NOT NULL,
    reason text NOT NULL CHECK (length(btrim(reason)) BETWEEN 1 AND 2000),
    classification text NOT NULL CHECK (classification IN ('river','internal')),
    correlation_id uuid NOT NULL,
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS steward_seed_lifecycle_seed_idx
    ON steward_seed_lifecycle_events(seed_id, created_at);

COMMIT;
