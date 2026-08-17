-- Operator derived-room lineage and bounded context transfer.
-- Migration: 0030
BEGIN;
ALTER TABLE operator_conversations
    ADD COLUMN IF NOT EXISTS source_conversation_id uuid REFERENCES operator_conversations(conversation_id),
    ADD COLUMN IF NOT EXISTS inherited_context_window text,
    ADD COLUMN IF NOT EXISTS inherited_message_count integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS participants_added jsonb NOT NULL DEFAULT '[]'::jsonb;
CREATE INDEX IF NOT EXISTS operator_conversations_source_idx ON operator_conversations(source_conversation_id);
COMMIT;
