-- Allow durable candidate-ready recovery before acceptance dispatch.
-- Version: 0.1.0
-- Migration: 0045

BEGIN;

ALTER TABLE campaign_package_runs
    DROP CONSTRAINT campaign_package_runs_state_check,
    ADD CONSTRAINT campaign_package_runs_state_check CHECK (state IN (
        'executing','repairing','verifying','candidate_ready',
        'awaiting_independent_acceptance','acceptance_failed','accepted','escalated'
    ));

COMMIT;
