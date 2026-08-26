-- Migration: 0047
-- Purpose: bounded Campaign Runner/Hermes engineering execution budget.

BEGIN;

INSERT INTO approved_actions (
    action_type, action_version, command_path, parameter_schema,
    expected_duration_seconds, hard_timeout_seconds, retry_safe, enabled
)
VALUES (
    'campaign.hermes.engineering',
    '1.0.0',
    'internal:hermes-campaign-role-adapter',
    '{
      "type":"object",
      "required":["hermes_request"],
      "properties":{
        "hermes_request":{"type":"object"},
        "candidate_identity":{"type":"string"},
        "implementation_ref":{"type":"string"},
        "validator_parameters":{"type":"object"},
        "repair_parameters":{"type":"object"},
        "revalidation_parameters":{"type":"object"}
      },
      "additionalProperties":false
    }'::jsonb,
    1200,
    1800,
    false,
    true
)
ON CONFLICT (action_type) DO UPDATE SET
    action_version=EXCLUDED.action_version,
    command_path=EXCLUDED.command_path,
    parameter_schema=EXCLUDED.parameter_schema,
    expected_duration_seconds=EXCLUDED.expected_duration_seconds,
    hard_timeout_seconds=EXCLUDED.hard_timeout_seconds,
    retry_safe=EXCLUDED.retry_safe,
    enabled=EXCLUDED.enabled,
    updated_at=now();

COMMIT;
