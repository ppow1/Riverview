-- Candidate/acceptance correspondence for restart-safe package acceptance.
-- Version: 0.1.0
-- Migration: 0044

BEGIN;

ALTER TABLE campaign_package_runs
    ADD COLUMN acceptance_candidate_ref text,
    ADD COLUMN acceptance_candidate_version_hash text;

UPDATE campaign_package_runs
   SET acceptance_candidate_ref=candidate_ref,
       acceptance_candidate_version_hash=candidate_version_hash
 WHERE acceptance_dispatch_count > 0
   AND acceptance_candidate_ref IS NULL;

COMMIT;
