-- Riverview Diagnostic Runtime Seed
-- Version: 0.3.0
-- Migration: 0002

BEGIN;

INSERT INTO cookbook_entries (
    cookbook_entry, checkpoint_id, component, failure_classes,
    diagnostic_procedure, repair_procedure, verification_procedure,
    applicability, validation_state
) VALUES
(
    'CB-RIV-DIA-0001', 'RIV-DIA-0001', 'riverview.diagnostics.store',
    '["database_unavailable", "transaction_failed", "invalid_record"]'::jsonb,
    '["Inspect the checkpoint and database health", "Inspect the emergency evidence spool"]'::jsonb,
    '["Restore PostgreSQL first", "Replay only verified spooled evidence"]'::jsonb,
    '["Run diagnostic health acceptance", "Confirm one database record"]'::jsonb,
    '{"kernel": ">=0.3.0"}'::jsonb, 'validated'
),
(
    'CB-RIV-DIA-0002', 'RIV-DIA-0002', 'riverview.diagnostics.spool',
    '["directory_unavailable", "permission_denied", "serialization_failed"]'::jsonb,
    '["Inspect the reported spool path", "Check the Windows runtime identity and ACL"]'::jsonb,
    '["Restore the local runtime directory ACL", "Do not discard the original failure"]'::jsonb,
    '["Induce database failure", "Confirm one append-only fallback record"]'::jsonb,
    '{"kernel": ">=0.3.0"}'::jsonb, 'validated'
)
ON CONFLICT (cookbook_entry) DO UPDATE SET
    failure_classes = EXCLUDED.failure_classes,
    diagnostic_procedure = EXCLUDED.diagnostic_procedure,
    repair_procedure = EXCLUDED.repair_procedure,
    verification_procedure = EXCLUDED.verification_procedure,
    applicability = EXCLUDED.applicability,
    validation_state = EXCLUDED.validation_state,
    updated_at = now();

COMMIT;