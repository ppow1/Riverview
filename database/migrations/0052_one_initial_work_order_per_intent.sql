-- Classify terminal historical retries, then enforce one admissible initial order.
-- Migration: 0052

BEGIN;

UPDATE work_orders
   SET work_order_kind='successor'
 WHERE work_order_kind='initial'
   AND status IN ('failed','timed_out')
   AND (
       idempotency_key LIKE 'stale-base-retry:%'
       OR idempotency_key LIKE 'grace:%'
   );

CREATE UNIQUE INDEX IF NOT EXISTS work_orders_one_initial_per_intent_idx
    ON work_orders(engineering_intent_id)
    WHERE engineering_intent_id IS NOT NULL
      AND work_order_kind='initial'
      AND source_work_order_id IS NULL
      AND status <> 'cancelled';

COMMIT;
