-- Exactly-once initial work-order identity and duplicate reconciliation.
-- Migration: 0051

BEGIN;

ALTER TABLE work_orders
    ADD COLUMN IF NOT EXISTS engineering_intent_id uuid REFERENCES engineering_intents(intent_id),
    ADD COLUMN IF NOT EXISTS work_order_kind text NOT NULL DEFAULT 'initial'
        CHECK (work_order_kind IN ('initial', 'successor'));

UPDATE work_orders
   SET engineering_intent_id = CASE
       WHEN parameters->>'engineering_intent_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
       THEN (parameters->>'engineering_intent_id')::uuid
       ELSE NULL
   END
 WHERE engineering_intent_id IS NULL;

CREATE TABLE IF NOT EXISTS work_order_duplicate_reconciliations (
    reconciliation_id uuid PRIMARY KEY,
    duplicate_work_order_id uuid NOT NULL UNIQUE REFERENCES work_orders(work_order_id),
    canonical_work_order_id uuid NOT NULL REFERENCES work_orders(work_order_id),
    engineering_intent_id uuid NOT NULL REFERENCES engineering_intents(intent_id),
    reason text NOT NULL,
    reconciled_by text NOT NULL,
    idempotency_key text NOT NULL UNIQUE,
    reconciled_at timestamptz NOT NULL DEFAULT now(),
    CHECK (duplicate_work_order_id <> canonical_work_order_id)
);

CREATE INDEX IF NOT EXISTS work_order_duplicate_reconciliations_canonical_idx
    ON work_order_duplicate_reconciliations(canonical_work_order_id);

COMMIT;
