-- Immutable successor attempts for retry-safe Relay work.

BEGIN;

CREATE TABLE work_order_successor_lineage (
    lineage_id uuid PRIMARY KEY,
    failed_work_order_id uuid NOT NULL UNIQUE REFERENCES work_orders(work_order_id),
    successor_work_order_id uuid NOT NULL UNIQUE REFERENCES work_orders(work_order_id),
    attempt integer NOT NULL CHECK (attempt > 1),
    failure_class text NOT NULL,
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

COMMIT;
