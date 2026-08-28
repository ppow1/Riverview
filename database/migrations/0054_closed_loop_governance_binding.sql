CREATE TABLE IF NOT EXISTS autonomous_governance_bindings (
    root_task_id uuid PRIMARY KEY REFERENCES autonomous_root_tasks(root_task_id),
    correlation_id uuid NOT NULL,
    specification_id uuid,
    engineering_intent_id uuid,
    objective_id uuid,
    stage_id uuid,
    authority_id uuid,
    work_order_id uuid,
    attempt_id uuid,
    lease_generation bigint,
    fencing_token uuid,
    worker_id text,
    resource_claim_id uuid,
    state text NOT NULL CHECK (state IN ('UNBOUND','PREPARED','AWAITING_AUTHORITY','BOUND','EXECUTABLE','RUNNING','RESULT_AVAILABLE','COMPLETED','STALE','INVALID')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS autonomous_governance_bindings_execution_idx
    ON autonomous_governance_bindings(state, updated_at);

CREATE INDEX IF NOT EXISTS autonomous_governance_bindings_work_idx
    ON autonomous_governance_bindings(work_order_id)
    WHERE work_order_id IS NOT NULL;
