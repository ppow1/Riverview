-- Provider-neutral reasoning registration and bounded project intake.
-- Migration: 0020

BEGIN;

CREATE TABLE reasoning_providers (
    participant_id text PRIMARY KEY,
    provider_id text NOT NULL,
    provider_type text NOT NULL,
    role text NOT NULL,
    capabilities jsonb NOT NULL,
    eligible_classifications jsonb NOT NULL,
    contract_version text NOT NULL,
    health text NOT NULL CHECK (health IN ('unknown','healthy','unhealthy','disabled')),
    capacity integer NOT NULL CHECK (capacity >= 0),
    provenance jsonb NOT NULL DEFAULT '{}'::jsonb,
    enabled boolean NOT NULL DEFAULT true,
    observed_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE project_intakes (
    intake_id uuid PRIMARY KEY,
    project_id text NOT NULL,
    mission text NOT NULL,
    repositories jsonb NOT NULL,
    requested_outcome text NOT NULL,
    acceptance_criteria jsonb NOT NULL,
    constraints_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    artifact_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    urgency text NOT NULL CHECK (urgency IN ('low','normal','high','critical')),
    classification text NOT NULL,
    steward_checkpoints jsonb NOT NULL DEFAULT '[]'::jsonb,
    required_reading jsonb NOT NULL DEFAULT '[]'::jsonb,
    external_dependencies jsonb NOT NULL DEFAULT '[]'::jsonb,
    status text NOT NULL CHECK (status IN ('draft','accepted','rejected')),
    correlation_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (project_id, correlation_id)
);

CREATE INDEX reasoning_providers_health_idx ON reasoning_providers(enabled, health, capacity);
CREATE INDEX project_intakes_status_idx ON project_intakes(status, classification);

COMMIT;
