-- Riverview MCP mailbox and resource model
-- Version: 0.10.0
-- Migration: 0011

BEGIN;

CREATE TABLE mailbox_messages (
    request_id uuid PRIMARY KEY,
    sender_id text NOT NULL,
    requester_id text NOT NULL,
    correlation_id uuid NOT NULL,
    causation_id uuid,
    message_type text NOT NULL,
    payload jsonb,
    payload_ref text,
    classification text NOT NULL CHECK (classification IN ('river','internal')),
    acknowledgement_state text NOT NULL DEFAULT 'unacknowledged'
        CHECK (acknowledgement_state IN ('unacknowledged','acknowledged')),
    claim_state text NOT NULL DEFAULT 'unclaimed'
        CHECK (claim_state IN ('unclaimed','claimed','released','expired')),
    claim_owner text,
    claim_expires_at timestamptz,
    response_id uuid,
    response_payload jsonb,
    response_payload_ref text,
    completion_state text NOT NULL DEFAULT 'pending'
        CHECK (completion_state IN ('pending','completed','expired','rejected')),
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    acknowledged_at timestamptz,
    claimed_at timestamptz,
    completed_at timestamptz,
    expires_at timestamptz NOT NULL,
    CHECK ((payload IS NULL) <> (payload_ref IS NULL)),
    CHECK (jsonb_typeof(payload) IN ('object','array','string','number','boolean','null') OR payload IS NULL),
    CHECK ((response_payload IS NULL) OR (response_payload_ref IS NULL)),
    CHECK (completion_state <> 'completed' OR response_id IS NOT NULL),
    CHECK (claim_state <> 'claimed' OR (claim_owner IS NOT NULL AND claim_expires_at IS NOT NULL))
);

CREATE INDEX mailbox_messages_correlation_idx ON mailbox_messages(correlation_id, created_at);
CREATE INDEX mailbox_messages_claim_idx ON mailbox_messages(completion_state, claim_state, expires_at);
CREATE INDEX mailbox_messages_classification_idx ON mailbox_messages(classification, created_at);

CREATE TABLE mailbox_responses (
    response_id uuid PRIMARY KEY,
    request_id uuid NOT NULL UNIQUE REFERENCES mailbox_messages(request_id) ON DELETE CASCADE,
    correlation_id uuid NOT NULL,
    causation_id uuid NOT NULL,
    responder_id text NOT NULL,
    response_type text NOT NULL,
    payload jsonb,
    payload_ref text,
    classification text NOT NULL CHECK (classification IN ('river','internal')),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((payload IS NULL) <> (payload_ref IS NULL))
);

COMMIT;
