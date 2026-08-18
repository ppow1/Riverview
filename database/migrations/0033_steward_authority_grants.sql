-- Durable Steward authority for specification-backed Grace formation.
-- Migration: 0033

BEGIN;

ALTER TABLE comms5_specifications
    ADD COLUMN IF NOT EXISTS formation_contract jsonb;

ALTER TABLE engineering_intents
    ADD COLUMN IF NOT EXISTS authority_id uuid;

CREATE TABLE IF NOT EXISTS steward_authority_grants (
    authority_id uuid PRIMARY KEY,
    specification_id uuid NOT NULL REFERENCES comms5_specifications(specification_id),
    specification_version integer NOT NULL CHECK (specification_version > 0),
    specification_sha256 text NOT NULL CHECK (length(specification_sha256)=64),
    seed_id uuid NOT NULL REFERENCES steward_seed_drafts(seed_id),
    objective_id uuid NOT NULL REFERENCES objectives(objective_id),
    stage_id uuid NOT NULL REFERENCES objective_stages(stage_id),
    approving_principal text NOT NULL CHECK (approving_principal='steward'),
    approved_at timestamptz NOT NULL DEFAULT now(),
    classification text NOT NULL CHECK (classification IN ('river','internal')),
    correlation_id uuid NOT NULL,
    causation_id uuid,
    approval_operation_id uuid,
    idempotency_key text NOT NULL UNIQUE,
    scope jsonb NOT NULL,
    permitted_capabilities jsonb NOT NULL,
    status text NOT NULL CHECK (status IN ('active','consumed','superseded','revoked','exhausted')),
    consumed_at timestamptz,
    superseded_by uuid REFERENCES steward_authority_grants(authority_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (specification_id, specification_version, specification_sha256, seed_id, objective_id)
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='engineering_intents_authority_fk') THEN
        ALTER TABLE engineering_intents ADD CONSTRAINT engineering_intents_authority_fk
            FOREIGN KEY (authority_id) REFERENCES steward_authority_grants(authority_id);
    END IF;
END $$;

CREATE INDEX steward_authority_stage_idx ON steward_authority_grants(objective_id, stage_id, status);
CREATE INDEX steward_authority_seed_idx ON steward_authority_grants(seed_id, created_at);

COMMIT;
