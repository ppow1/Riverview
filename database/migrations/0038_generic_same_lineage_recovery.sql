-- Generic same-lineage recovery after a recoverable execution failure.
-- Migration: 0038

BEGIN;

ALTER TABLE execution_base_revalidations
    DROP CONSTRAINT IF EXISTS execution_base_revalidations_decision_check;
ALTER TABLE execution_base_revalidations
    ADD CONSTRAINT execution_base_revalidations_decision_check
    CHECK (decision IN (
        'safe_revalidation',
        'narrow_steward_confirmation',
        'infrastructure_repair_revalidation',
        'material_drift',
        'invalid_repository'
    ));

COMMENT ON TABLE execution_base_revalidations IS
    'Append-only recovery evidence. Original failure cause and successor base drift are independent facts.';

COMMIT;
