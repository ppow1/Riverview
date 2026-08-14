-- Riverview Master Roadmap Schema
-- Version: 0.8.0
-- Migration: 0007

BEGIN;
ALTER TABLE roadmap_items ADD COLUMN IF NOT EXISTS depends_on jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE roadmap_items ADD COLUMN IF NOT EXISTS governing_refs jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE roadmap_items ADD COLUMN IF NOT EXISTS scope_boundary text NOT NULL DEFAULT 'Bounded by the governing Riverview architecture.';
ALTER TABLE roadmap_items ADD COLUMN IF NOT EXISTS roadmap_revision text NOT NULL DEFAULT 'legacy';
CREATE TABLE roadmap_revisions (
 revision_id text PRIMARY KEY,
 content_sha256 text NOT NULL,
 waypoint_count integer NOT NULL CHECK(waypoint_count > 0),
 source_path text NOT NULL,
 applied_at timestamptz NOT NULL DEFAULT now()
);
COMMIT;