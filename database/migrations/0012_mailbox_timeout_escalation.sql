-- RV-004.5 mailbox timeout escalation identity
-- Version: 0.12.0
-- Migration: 0012

BEGIN;

ALTER TABLE steward_escalations
    ADD COLUMN mailbox_request_id uuid REFERENCES mailbox_messages(request_id);

CREATE UNIQUE INDEX steward_escalations_mailbox_timeout_idx
    ON steward_escalations(mailbox_request_id)
    WHERE mailbox_request_id IS NOT NULL;

COMMIT;
