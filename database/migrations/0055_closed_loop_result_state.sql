BEGIN;

ALTER TABLE autonomous_root_tasks
    DROP CONSTRAINT IF EXISTS autonomous_root_tasks_state_check;

ALTER TABLE autonomous_root_tasks
    ADD CONSTRAINT autonomous_root_tasks_state_check
    CHECK (state IN ('queued','active','waiting','result_available','completed','blocked','archived'));

COMMIT;
