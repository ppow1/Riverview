CREATE TABLE IF NOT EXISTS autonomous_root_tasks (
    root_task_id uuid PRIMARY KEY,
    correlation_id uuid NOT NULL,
    objective text NOT NULL,
    state text NOT NULL CHECK (state IN ('queued','active','waiting','completed','blocked','archived')),
    originating_resident text NOT NULL,
    attention_state text NOT NULL DEFAULT 'none',
    current_checkpoint_id text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (correlation_id)
);

CREATE TABLE IF NOT EXISTS autonomous_checkpoints (
    checkpoint_id text NOT NULL,
    root_task_id uuid NOT NULL REFERENCES autonomous_root_tasks(root_task_id),
    roadmap_version integer NOT NULL,
    sequence integer NOT NULL,
    title text NOT NULL,
    acceptance_condition text NOT NULL,
    status text NOT NULL CHECK (status IN ('PLANNED','ACTIVE','COMPLETED','BLOCKED','REWORK','SUPERSEDED')),
    actor text NOT NULL,
    started_at timestamptz,
    completed_at timestamptz,
    evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    blocker text,
    PRIMARY KEY (root_task_id, checkpoint_id),
    UNIQUE (root_task_id, roadmap_version, sequence)
);

CREATE TABLE IF NOT EXISTS autonomous_tracer_requests (
    request_id uuid PRIMARY KEY,
    root_task_id uuid NOT NULL REFERENCES autonomous_root_tasks(root_task_id),
    correlation_id uuid NOT NULL,
    checkpoint_id text NOT NULL,
    originating_resident text NOT NULL,
    objective text NOT NULL,
    state text NOT NULL CHECK (state IN ('formed','queued','claimed','running','resulted','consumed','blocked')),
    claim_owner text,
    lease_expires_at timestamptz,
    run_id uuid,
    result_id uuid,
    request_digest text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (root_task_id, checkpoint_id)
);

CREATE TABLE IF NOT EXISTS autonomous_tracer_results (
    result_id uuid PRIMARY KEY,
    request_id uuid NOT NULL UNIQUE REFERENCES autonomous_tracer_requests(request_id),
    root_task_id uuid NOT NULL REFERENCES autonomous_root_tasks(root_task_id),
    correlation_id uuid NOT NULL,
    run_id uuid NOT NULL,
    semantic_outcome text NOT NULL,
    summary text NOT NULL,
    evidence jsonb NOT NULL,
    resulting_sha text,
    result_digest text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS autonomous_tracer_events_idx
    ON river_events (aggregate_type, aggregate_id, sequence_id);
