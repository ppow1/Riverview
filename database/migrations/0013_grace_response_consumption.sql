-- RV-008.4 durable Grace reasoning-response consumption
-- Version: 0.1.0 | Migration: 0013

BEGIN;

CREATE TABLE grace_response_consumptions (
    consumption_id uuid PRIMARY KEY,
    response_id uuid NOT NULL UNIQUE REFERENCES mailbox_responses(response_id),
    request_id uuid NOT NULL REFERENCES mailbox_messages(request_id),
    correlation_id uuid NOT NULL,
    consumer_id text NOT NULL CHECK (consumer_id = 'grace'),
    consumer_version text NOT NULL,
    objective_key text NOT NULL REFERENCES objectives(objective_key),
    outcome text NOT NULL CHECK (outcome IN (
        'advisory_accepted','escalation_required',
        'insufficient_response','no_authorized_transition'
    )),
    evaluation jsonb NOT NULL,
    consumed_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX grace_response_consumptions_correlation_idx
    ON grace_response_consumptions(correlation_id, consumed_at);

COMMIT;
