-- Campaign Runner persistence foundation and exact attempt fencing.
-- Version: 0.1.0
-- Migration: 0039

BEGIN;

-- Preserve the original relay sequence number as historical data while
-- promoting attempt_id to the UUID identity required by the campaign runner.
ALTER TABLE work_order_attempts RENAME COLUMN attempt_id TO legacy_attempt_id;
ALTER TABLE work_order_attempts ADD COLUMN attempt_id uuid;
ALTER TABLE work_order_attempts ADD COLUMN lease_generation bigint;
ALTER TABLE work_order_attempts ADD COLUMN fencing_token uuid;
ALTER TABLE work_order_attempts ADD COLUMN worker_instance_id uuid;
ALTER TABLE work_order_attempts ADD COLUMN seat_id text;
ALTER TABLE work_order_attempts ADD COLUMN role text;
ALTER TABLE work_order_attempts ADD COLUMN last_heartbeat_at timestamptz;
ALTER TABLE work_order_attempts ADD COLUMN last_progress_at timestamptz;
ALTER TABLE work_order_attempts ADD COLUMN progress_count integer NOT NULL DEFAULT 0;
ALTER TABLE work_order_attempts ADD COLUMN terminal_state text;
ALTER TABLE work_order_attempts ADD COLUMN late_or_stale boolean NOT NULL DEFAULT false;
ALTER TABLE work_order_attempts ADD COLUMN late_result_ref text;

UPDATE work_order_attempts
   SET attempt_id = (
       substr(md5(work_order_id::text || ':attempt:' || legacy_attempt_id::text), 1, 8)
       || '-' || substr(md5(work_order_id::text || ':attempt:' || legacy_attempt_id::text), 9, 4)
       || '-' || substr(md5(work_order_id::text || ':attempt:' || legacy_attempt_id::text), 13, 4)
       || '-' || substr(md5(work_order_id::text || ':attempt:' || legacy_attempt_id::text), 17, 4)
       || '-' || substr(md5(work_order_id::text || ':attempt:' || legacy_attempt_id::text), 21, 12)
   )::uuid,
       lease_generation = legacy_attempt_id,
       fencing_token = (
       substr(md5(work_order_id::text || ':fence:' || legacy_attempt_id::text), 1, 8)
       || '-' || substr(md5(work_order_id::text || ':fence:' || legacy_attempt_id::text), 9, 4)
       || '-' || substr(md5(work_order_id::text || ':fence:' || legacy_attempt_id::text), 13, 4)
       || '-' || substr(md5(work_order_id::text || ':fence:' || legacy_attempt_id::text), 17, 4)
       || '-' || substr(md5(work_order_id::text || ':fence:' || legacy_attempt_id::text), 21, 12)
   )::uuid,
       worker_instance_id = (
       substr(md5(worker_id || ':worker-instance'), 1, 8)
       || '-' || substr(md5(worker_id || ':worker-instance'), 9, 4)
       || '-' || substr(md5(worker_id || ':worker-instance'), 13, 4)
       || '-' || substr(md5(worker_id || ':worker-instance'), 17, 4)
       || '-' || substr(md5(worker_id || ':worker-instance'), 21, 12)
   )::uuid,
       last_heartbeat_at = started_at,
       last_progress_at = NULL
 WHERE attempt_id IS NULL;

ALTER TABLE work_order_attempts ALTER COLUMN attempt_id SET NOT NULL;
ALTER TABLE work_order_attempts ALTER COLUMN lease_generation SET NOT NULL;
ALTER TABLE work_order_attempts ALTER COLUMN fencing_token SET NOT NULL;
ALTER TABLE work_order_attempts ALTER COLUMN worker_instance_id SET NOT NULL;
ALTER TABLE work_order_attempts ADD CONSTRAINT work_order_attempts_attempt_id_key UNIQUE (attempt_id);
ALTER TABLE work_order_attempts ADD CONSTRAINT work_order_attempts_progress_count_check CHECK (progress_count >= 0);

ALTER TABLE work_orders ADD COLUMN active_attempt_id uuid;
ALTER TABLE work_orders ADD COLUMN lease_generation bigint;
ALTER TABLE work_orders ADD COLUMN fencing_token uuid;
ALTER TABLE work_orders ADD COLUMN worker_instance_id uuid;
ALTER TABLE work_orders ADD COLUMN seat_id text;
ALTER TABLE work_orders ADD COLUMN role text;
ALTER TABLE work_orders ADD COLUMN last_progress_at timestamptz;
ALTER TABLE work_orders ADD COLUMN progress_count integer NOT NULL DEFAULT 0;
ALTER TABLE work_orders ADD COLUMN blocked_reason text;

ALTER TABLE work_orders
    ADD CONSTRAINT work_orders_active_attempt_fk
    FOREIGN KEY (active_attempt_id) REFERENCES work_order_attempts(attempt_id);
ALTER TABLE work_orders
    ADD CONSTRAINT work_orders_active_fence_tuple_check CHECK (
        (active_attempt_id IS NULL AND lease_generation IS NULL AND fencing_token IS NULL AND worker_instance_id IS NULL)
        OR
        (active_attempt_id IS NOT NULL AND lease_generation IS NOT NULL AND fencing_token IS NOT NULL AND worker_instance_id IS NOT NULL)
    );
ALTER TABLE work_orders ADD CONSTRAINT work_orders_progress_count_check CHECK (progress_count >= 0);

CREATE INDEX work_orders_active_attempt_idx ON work_orders (active_attempt_id) WHERE active_attempt_id IS NOT NULL;
CREATE INDEX work_orders_fenced_lease_idx ON work_orders (status, lease_expires_at)
    WHERE active_attempt_id IS NOT NULL;
CREATE INDEX work_order_attempts_worker_heartbeat_idx
    ON work_order_attempts (worker_instance_id, last_heartbeat_at);

ALTER TABLE relay_workers ADD COLUMN worker_instance_id uuid;
ALTER TABLE relay_workers ADD COLUMN seat_id text;
ALTER TABLE relay_workers ADD COLUMN supported_roles jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE relay_workers ADD COLUMN current_work_order_id uuid REFERENCES work_orders(work_order_id);
ALTER TABLE relay_workers ADD COLUMN stale boolean NOT NULL DEFAULT false;
CREATE UNIQUE INDEX relay_workers_worker_instance_idx
    ON relay_workers(worker_instance_id) WHERE worker_instance_id IS NOT NULL;

ALTER TABLE execution_envelopes ADD COLUMN attempt_id uuid REFERENCES work_order_attempts(attempt_id);
ALTER TABLE execution_envelopes ADD COLUMN lease_generation bigint;
ALTER TABLE execution_envelopes ADD COLUMN fencing_token uuid;
ALTER TABLE execution_envelopes ADD COLUMN worker_instance_id uuid;
ALTER TABLE execution_envelopes ADD COLUMN role text;
ALTER TABLE execution_envelopes ADD COLUMN validation_basis_hash text;

ALTER TABLE execution_results ADD COLUMN attempt_id uuid REFERENCES work_order_attempts(attempt_id);
ALTER TABLE execution_results ADD COLUMN lease_generation bigint;
ALTER TABLE execution_results ADD COLUMN fencing_token uuid;
ALTER TABLE execution_results ADD COLUMN worker_instance_id uuid;
ALTER TABLE execution_results ADD COLUMN late_or_stale boolean NOT NULL DEFAULT false;
ALTER TABLE execution_results ADD COLUMN authoritative_result boolean NOT NULL DEFAULT false;
CREATE INDEX execution_results_attempt_idx ON execution_results (attempt_id, late_or_stale);

COMMIT;
