-- Riverview Comms5 governed provenance and specification references.
-- Migration: 0026

BEGIN;

ALTER TABLE steward_seed_drafts
    ADD COLUMN IF NOT EXISTS client_id text,
    ADD COLUMN IF NOT EXISTS client_type text,
    ADD COLUMN IF NOT EXISTS client_name text,
    ADD COLUMN IF NOT EXISTS client_version text,
    ADD COLUMN IF NOT EXISTS protocol_version text,
    ADD COLUMN IF NOT EXISTS authenticated_principal text,
    ADD COLUMN IF NOT EXISTS specification_id uuid,
    ADD COLUMN IF NOT EXISTS specification_version integer;

CREATE TABLE IF NOT EXISTS comms5_specifications (
    specification_id uuid PRIMARY KEY,
    version integer NOT NULL CHECK (version > 0),
    summary text NOT NULL CHECK (length(btrim(summary)) BETWEEN 1 AND 2000),
    content text NOT NULL,
    content_bytes integer NOT NULL CHECK (content_bytes > 0),
    content_sha256 text NOT NULL,
    classification text NOT NULL CHECK (classification IN ('river','internal')),
    lifecycle_state text NOT NULL CHECK (lifecycle_state IN ('stored','referenced','superseded','rejected')),
    client_id text NOT NULL,
    client_type text NOT NULL,
    client_name text NOT NULL,
    client_version text,
    protocol_version text NOT NULL,
    authenticated_principal text NOT NULL,
    correlation_id uuid NOT NULL,
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS comms5_specifications_hash_idx
    ON comms5_specifications(content_sha256);

COMMIT;
