-- Bounded exactly-once Steward/critical notification records.
-- Migration: 0023

BEGIN;

CREATE TABLE steward_notifications (
    notification_id uuid PRIMARY KEY,
    idempotency_key text NOT NULL UNIQUE,
    notification_type text NOT NULL CHECK (notification_type IN ('steward_checkpoint','critical_failure','important_completion','binding_condition')),
    checkpoint_id text NOT NULL,
    summary text NOT NULL,
    evidence_refs jsonb NOT NULL,
    state text NOT NULL CHECK (state IN ('queued','delivered','acknowledged')),
    created_at timestamptz NOT NULL DEFAULT now(),
    delivered_at timestamptz,
    acknowledged_at timestamptz
);

CREATE INDEX steward_notifications_state_idx ON steward_notifications(state,created_at);

COMMIT;
