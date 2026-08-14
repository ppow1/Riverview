-- Riverview Read-Only MCP Relay
-- Version: 0.9.1
-- Migration: 0008

BEGIN;
CREATE TABLE IF NOT EXISTS cookbook_entries (
    checkpoint_id text PRIMARY KEY,
    title text NOT NULL,
    summary text NOT NULL,
    failure_classes jsonb NOT NULL DEFAULT '[]'::jsonb,
    distinguishing_probes jsonb NOT NULL DEFAULT '[]'::jsonb,
    smallest_safe_repair text NOT NULL,
    recovery_verification text NOT NULL,
    source_path text NOT NULL,
    implementation_revision text,
    validation_state text NOT NULL DEFAULT 'candidate',
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mcp_read_surfaces (
    surface_id text PRIMARY KEY,
    authority text NOT NULL CHECK (authority='read_only'),
    bind_scope text NOT NULL CHECK (bind_scope='local'),
    enabled boolean NOT NULL DEFAULT true,
    updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO mcp_read_surfaces(surface_id,authority,bind_scope)
VALUES('riverview-readonly-relay','read_only','local')
ON CONFLICT(surface_id) DO UPDATE SET authority=EXCLUDED.authority,bind_scope=EXCLUDED.bind_scope,enabled=true,updated_at=now();
COMMIT;