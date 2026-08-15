-- Riverview declared Grace action binding
-- Migration: 0016

BEGIN;

ALTER TABLE objective_stages ADD COLUMN declared_action jsonb;

COMMIT;
