-- Riverview bounded lanes and result reconciliation
-- Migration: 0017

BEGIN;

CREATE TABLE execution_lanes (
    lane_id uuid PRIMARY KEY,
    lane_key text NOT NULL UNIQUE,
    correlation_id uuid NOT NULL,
    owner_id text NOT NULL,
    allowed_paths jsonb NOT NULL,
    state text NOT NULL CHECK (state IN ('active','released')),
    created_at timestamptz NOT NULL DEFAULT now(),
    released_at timestamptz
);

CREATE TABLE lane_path_owners (
    relative_path text PRIMARY KEY,
    lane_id uuid NOT NULL REFERENCES execution_lanes(lane_id),
    owner_id text NOT NULL,
    acquired_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE reconciliation_records (
    reconciliation_id uuid PRIMARY KEY,
    execution_id uuid NOT NULL UNIQUE REFERENCES execution_envelopes(execution_id),
    correlation_id uuid NOT NULL,
    decision text NOT NULL CHECK (decision IN ('accepted','rejected','conflict','checkpoint')),
    reason text NOT NULL,
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

COMMIT;
