-- Riverview Objective and Stage Model
-- Version: 0.2.0
-- Migration: 0010

BEGIN;

CREATE TABLE objectives (
    objective_id uuid PRIMARY KEY,
    objective_key text NOT NULL UNIQUE,
    title text NOT NULL,
    description text NOT NULL,
    status text NOT NULL CHECK(status IN ('draft','ready','active','blocked','completed','cancelled')),
    owner_id text NOT NULL,
    requested_by text NOT NULL,
    correlation_id uuid NOT NULL,
    final_output jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE TABLE objective_stages (
    stage_id uuid PRIMARY KEY,
    objective_id uuid NOT NULL REFERENCES objectives(objective_id) ON DELETE CASCADE,
    stage_key text NOT NULL,
    sort_order integer NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    status text NOT NULL CHECK(status IN ('pending','ready','active','blocked','completed','cancelled')),
    readiness text NOT NULL CHECK(readiness IN ('waiting','ready','satisfied','blocked')),
    required_evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    accepted_evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    final_output jsonb,
    steward_checkpoint boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    UNIQUE(objective_id,stage_key),
    UNIQUE(objective_id,sort_order)
);

CREATE TABLE objective_stage_dependencies (
    stage_id uuid NOT NULL REFERENCES objective_stages(stage_id) ON DELETE CASCADE,
    depends_on_stage_id uuid NOT NULL REFERENCES objective_stages(stage_id) ON DELETE CASCADE,
    PRIMARY KEY(stage_id,depends_on_stage_id),
    CHECK(stage_id <> depends_on_stage_id)
);

CREATE INDEX objective_status_idx ON objectives(status,updated_at);
CREATE INDEX objective_stage_readiness_idx ON objective_stages(objective_id,readiness,sort_order);

INSERT INTO cookbook_entries(
    cookbook_entry,checkpoint_id,component,failure_classes,
    diagnostic_procedure,repair_procedure,verification_procedure,
    applicability,validation_state,validated_at,updated_at
)
VALUES(
    'CB-RIV-GRC-0002',
    'RIV-GRC-0002',
    'riverview.grace.objectives',
    '["objective-missing","dependency-unsatisfied","required-evidence-missing","invalid-stage-transition","restart-resume-failure"]'::jsonb,
    '["Run python -m riverview.grace.objective_acceptance read","Inspect objectives/objective_stages/objective_stage_dependencies in PostgreSQL","Read the River aggregate for the objective correlation"]'::jsonb,
    '["Restore only the missing objective/stage state or accepted evidence; do not fabricate evidence or bypass dependencies"]'::jsonb,
    '["Run objective model tests","Run seed and read acceptance in separate Python processes","Verify final outputs and River events"]'::jsonb,
    '{"waypoint":"RV-005.2","authority":"postgresql","json_file_authority":false}'::jsonb,
    'validated',
    now(),
    now()
)
ON CONFLICT(checkpoint_id) DO UPDATE SET
    component=EXCLUDED.component,
    failure_classes=EXCLUDED.failure_classes,
    diagnostic_procedure=EXCLUDED.diagnostic_procedure,
    repair_procedure=EXCLUDED.repair_procedure,
    verification_procedure=EXCLUDED.verification_procedure,
    applicability=EXCLUDED.applicability,
    validation_state=EXCLUDED.validation_state,
    validated_at=EXCLUDED.validated_at,
    updated_at=EXCLUDED.updated_at;

COMMIT;