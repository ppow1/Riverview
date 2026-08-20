-- Governed stale-base recovery for already-approved bounded engineering work.

BEGIN;

CREATE TABLE execution_base_revalidations (
    revalidation_id uuid PRIMARY KEY,
    failed_work_order_id uuid NOT NULL UNIQUE REFERENCES work_orders(work_order_id),
    successor_work_order_id uuid UNIQUE REFERENCES work_orders(work_order_id),
    intent_id uuid NOT NULL REFERENCES engineering_intents(intent_id),
    objective_id uuid NOT NULL REFERENCES objectives(objective_id),
    authority_id uuid NOT NULL REFERENCES steward_authority_grants(authority_id),
    approved_base_sha text NOT NULL CHECK (length(approved_base_sha)=40),
    proposed_base_sha text NOT NULL CHECK (length(proposed_base_sha)=40),
    changed_paths jsonb NOT NULL DEFAULT '[]'::jsonb,
    material_paths jsonb NOT NULL DEFAULT '[]'::jsonb,
    review_paths jsonb NOT NULL DEFAULT '[]'::jsonb,
    evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
    decision text NOT NULL CHECK (decision IN ('safe_revalidation','narrow_steward_confirmation','material_drift','invalid_repository')),
    status text NOT NULL CHECK (status IN ('pending','approved','rejected','consumed')),
    explicit_steward_confirmation boolean NOT NULL DEFAULT false,
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    approved_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE work_order_retry_lineage (
    retry_id uuid PRIMARY KEY,
    failed_work_order_id uuid NOT NULL UNIQUE REFERENCES work_orders(work_order_id),
    successor_work_order_id uuid NOT NULL UNIQUE REFERENCES work_orders(work_order_id),
    revalidation_id uuid NOT NULL UNIQUE REFERENCES execution_base_revalidations(revalidation_id),
    attempt integer NOT NULL CHECK (attempt > 1),
    idempotency_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX execution_base_revalidations_status_idx ON execution_base_revalidations(status, updated_at);

COMMIT;
