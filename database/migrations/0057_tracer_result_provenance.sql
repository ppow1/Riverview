BEGIN;

ALTER TABLE autonomous_tracer_results
    ADD COLUMN IF NOT EXISTS provider_id text,
    ADD COLUMN IF NOT EXISTS resource_class_ref text,
    ADD COLUMN IF NOT EXISTS response_id uuid,
    ADD COLUMN IF NOT EXISTS adapter_id text;

COMMIT;
