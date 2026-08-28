BEGIN;

ALTER TABLE work_order_attempts
    ADD COLUMN IF NOT EXISTS run_id uuid;

UPDATE work_order_attempts
   SET run_id = attempt_id
 WHERE run_id IS NULL;

ALTER TABLE work_order_attempts
    ALTER COLUMN run_id SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS work_order_attempts_run_id_key
    ON work_order_attempts (run_id);

COMMIT;
