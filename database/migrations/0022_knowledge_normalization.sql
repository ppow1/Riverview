-- Bounded normalized conversation/turn representation for RV-009.2/009.3.
-- Migration: 0022

BEGIN;

CREATE TABLE knowledge_conversations (
    conversation_id uuid PRIMARY KEY,
    source_export_id uuid NOT NULL REFERENCES knowledge_exports(export_id),
    source_ref text NOT NULL,
    classification text NOT NULL,
    provenance jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_export_id)
);

CREATE TABLE knowledge_turns (
    turn_id uuid PRIMARY KEY,
    conversation_id uuid NOT NULL REFERENCES knowledge_conversations(conversation_id),
    source_message_id text NOT NULL,
    speaker text NOT NULL,
    occurred_at timestamptz,
    body text NOT NULL,
    classification text NOT NULL,
    provenance jsonb NOT NULL,
    uncertain_attribution boolean NOT NULL DEFAULT false,
    turn_order integer NOT NULL CHECK (turn_order >= 0),
    UNIQUE (conversation_id, source_message_id),
    UNIQUE (conversation_id, turn_order)
);

CREATE INDEX knowledge_turns_search_idx ON knowledge_turns USING gin (to_tsvector('simple', body));

COMMIT;
