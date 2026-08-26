-- Durable single-owner fencing for independent acceptance invocation.
-- Version: 0.1.0
-- Migration: 0046

BEGIN;

ALTER TABLE campaign_package_runs
    ADD COLUMN acceptance_owner_id uuid,
    ADD COLUMN acceptance_lease_generation integer NOT NULL DEFAULT 0
        CHECK (acceptance_lease_generation >= 0),
    ADD COLUMN acceptance_lease_expires_at timestamptz,
    ADD COLUMN acceptance_invocation_started_at timestamptz;

COMMIT;
