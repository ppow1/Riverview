-- Immutable export/source inventory for bounded knowledge ingestion.
-- Migration: 0021

BEGIN;

CREATE TABLE knowledge_exports (
    export_id uuid PRIMARY KEY,
    source_path text NOT NULL,
    content_sha256 text NOT NULL,
    byte_size bigint NOT NULL CHECK (byte_size >= 0),
    source_kind text NOT NULL,
    classification text NOT NULL,
    provenance jsonb NOT NULL,
    status text NOT NULL CHECK (status IN ('inventoried','ingested','rejected')),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_path, content_sha256)
);

CREATE INDEX knowledge_exports_classification_idx ON knowledge_exports(classification,status);

COMMIT;
