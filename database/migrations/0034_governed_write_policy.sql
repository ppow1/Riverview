-- Governed engineering execution policy vocabulary.
-- Migration: 0034

BEGIN;

ALTER TABLE engineering_intents
    DROP CONSTRAINT IF EXISTS engineering_intents_write_policy_check;
ALTER TABLE engineering_intents
    ADD CONSTRAINT engineering_intents_write_policy_bound
    CHECK (write_policy IN ('read_only','bounded_write'));

ALTER TABLE execution_envelopes
    ADD COLUMN IF NOT EXISTS action_type text NOT NULL DEFAULT 'codex.engineering.v1';
ALTER TABLE execution_envelopes
    ADD COLUMN IF NOT EXISTS write_policy text NOT NULL DEFAULT 'read_only';
ALTER TABLE execution_envelopes
    ADD CONSTRAINT execution_envelopes_action_policy_bound
    CHECK (action_type='codex.engineering.v1' AND write_policy IN ('read_only','bounded_write'));

COMMIT;
