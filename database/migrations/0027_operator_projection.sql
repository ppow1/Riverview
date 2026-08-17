-- Durable Operator conversation/room projection. UI history is separate from resident continuity/canon.
BEGIN;
CREATE TABLE operator_conversations (
    conversation_id uuid PRIMARY KEY,
    resident_id text,
    room_id uuid,
    kind text NOT NULL CHECK (kind IN ('conversation','room')),
    title text NOT NULL,
    classification text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz
);
CREATE INDEX operator_conversations_updated_idx ON operator_conversations (updated_at DESC);
CREATE TABLE operator_messages (
    message_id uuid PRIMARY KEY,
    conversation_id uuid NOT NULL REFERENCES operator_conversations(conversation_id),
    turn_order integer NOT NULL CHECK (turn_order >= 0),
    role text NOT NULL,
    speaker_id text,
    speaker_name text,
    body text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (conversation_id, turn_order)
);
CREATE INDEX operator_messages_search_idx ON operator_messages USING gin (to_tsvector('simple', body));
COMMIT;
