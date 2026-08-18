-- Durable room membership and room-scoped administration.
-- Resident continuity and global authority remain outside this projection.
BEGIN;
CREATE TABLE operator_room_memberships (
    membership_id uuid PRIMARY KEY,
    room_id uuid NOT NULL,
    resident_id text NOT NULL,
    state text NOT NULL CHECK (state IN ('active','removed','left')),
    added_by text NOT NULL,
    added_at timestamptz NOT NULL DEFAULT now(),
    removed_by text,
    removed_at timestamptz,
    context_window text NOT NULL DEFAULT 'from_this_point',
    source_conversation_id uuid REFERENCES operator_conversations(conversation_id),
    correlation_id uuid NOT NULL
);
CREATE INDEX operator_room_memberships_active_idx ON operator_room_memberships(room_id, resident_id) WHERE state='active';
CREATE INDEX operator_room_memberships_history_idx ON operator_room_memberships(room_id, added_at);
CREATE TABLE operator_room_administrators (
    administration_id uuid PRIMARY KEY,
    room_id uuid NOT NULL,
    administrator_id text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    primary_administrator boolean NOT NULL DEFAULT false,
    granted_by text NOT NULL,
    granted_at timestamptz NOT NULL DEFAULT now(),
    revoked_by text,
    revoked_at timestamptz,
    correlation_id uuid NOT NULL
);
CREATE UNIQUE INDEX operator_room_active_admin_idx ON operator_room_administrators(room_id, administrator_id) WHERE active;
CREATE INDEX operator_room_admin_history_idx ON operator_room_administrators(room_id, granted_at);
COMMIT;
