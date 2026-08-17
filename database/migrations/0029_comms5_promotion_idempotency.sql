-- Comms5 promotion idempotency and conflict protection.
-- Migration: 0029

BEGIN;

CREATE TABLE IF NOT EXISTS steward_seed_promotion_requests (
    request_id uuid PRIMARY KEY,
    seed_id uuid NOT NULL REFERENCES steward_seed_drafts(seed_id),
    objective_id uuid NOT NULL REFERENCES objectives(objective_id),
    actor text NOT NULL,
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS steward_seed_promotion_seed_idx
    ON steward_seed_promotion_requests(seed_id, created_at);

COMMIT;
