-- Riverview Comms binding and rollover registry
-- Version: 0.19.0
-- Migration: 0019

BEGIN;

CREATE TABLE comms_bindings (
    binding_id uuid PRIMARY KEY,
    role text NOT NULL CHECK (role IN ('designated_reasoning','steward_intake','notification_reporting')),
    application_ref text NOT NULL,
    contract_version text NOT NULL,
    conversation_id uuid NOT NULL,
    conversation_ref text NOT NULL,
    consumer_id text NOT NULL,
    status text NOT NULL CHECK (status IN ('candidate','initialized','active','retired')),
    verification_state text NOT NULL CHECK (verification_state IN ('unverified','verified','rejected')),
    verification_evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    reason text NOT NULL,
    activated_at timestamptz,
    retired_at timestamptz,
    replaced_binding_id uuid REFERENCES comms_bindings(binding_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (role, conversation_id, contract_version)
);

CREATE UNIQUE INDEX comms_bindings_active_role_idx
    ON comms_bindings(role) WHERE status='active';

CREATE INDEX comms_bindings_consumer_idx
    ON comms_bindings(consumer_id, role, status);

COMMIT;
