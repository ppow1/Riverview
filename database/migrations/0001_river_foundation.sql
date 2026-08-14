-- Riverview River Foundation Migration
-- Version: 0.1.0
-- Migration: 0001

BEGIN;

CREATE TABLE schema_migrations (
    migration_id text PRIMARY KEY,
    version text NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now(),
    checksum_sha256 text NOT NULL
);

CREATE TABLE river_events (
    sequence_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id uuid NOT NULL UNIQUE,
    event_type text NOT NULL,
    aggregate_type text NOT NULL,
    aggregate_id uuid NOT NULL,
    correlation_id uuid NOT NULL,
    causation_id uuid,
    idempotency_key text NOT NULL UNIQUE,
    classification text NOT NULL,
    payload jsonb NOT NULL,
    occurred_at timestamptz NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX river_events_aggregate_sequence_idx
    ON river_events (aggregate_type, aggregate_id, sequence_id);

CREATE INDEX river_events_correlation_idx
    ON river_events (correlation_id, sequence_id);

CREATE TABLE cookbook_entries (
    cookbook_entry text PRIMARY KEY,
    checkpoint_id text NOT NULL UNIQUE,
    component text NOT NULL,
    failure_classes jsonb NOT NULL,
    diagnostic_procedure jsonb NOT NULL,
    repair_procedure jsonb NOT NULL,
    verification_procedure jsonb NOT NULL,
    applicability jsonb NOT NULL,
    validation_state text NOT NULL,
    validated_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE diagnostic_events (
    event_id uuid PRIMARY KEY,
    checkpoint_id text NOT NULL,
    component text NOT NULL,
    operation text NOT NULL,
    workflow_id uuid,
    attempt integer NOT NULL CHECK (attempt >= 1),
    severity text NOT NULL,
    failure_class text NOT NULL,
    summary text NOT NULL,
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    dependency_state jsonb NOT NULL DEFAULT '{}'::jsonb,
    cookbook_entry text NOT NULL REFERENCES cookbook_entries(cookbook_entry),
    recovery_state text NOT NULL,
    occurred_at timestamptz NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX diagnostic_events_checkpoint_time_idx
    ON diagnostic_events (checkpoint_id, occurred_at DESC);

COMMIT;
