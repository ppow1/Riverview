-- Preserve the full DefectInput semantics in the package ledger.
-- Version: 0.1.0
-- Migration: 0043

BEGIN;

ALTER TABLE campaign_repair_ledger
    ADD COLUMN acceptance_criterion_ref text NOT NULL DEFAULT 'package-observation',
    ADD COLUMN severity text NOT NULL DEFAULT 'blocking'
        CHECK (severity IN ('blocking','non_blocking')),
    ADD COLUMN required_repair text NOT NULL DEFAULT 'bounded package repair';

COMMIT;
