-- Riverview Relay Foundation
-- Version: 0.4.0
-- Migration: 0003

BEGIN;

CREATE TABLE roadmap_items (
    waypoint_id text PRIMARY KEY,
    parent_waypoint_id text REFERENCES roadmap_items(waypoint_id),
    sort_order integer NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    status text NOT NULL CHECK (status IN ('pending','active','blocked','completed','cancelled')),
    steward_checkpoint boolean NOT NULL DEFAULT false,
    acceptance_criteria jsonb NOT NULL DEFAULT '[]'::jsonb,
    completed_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (parent_waypoint_id, sort_order)
);

CREATE TABLE roadmap_transitions (
    transition_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    waypoint_id text NOT NULL REFERENCES roadmap_items(waypoint_id),
    from_status text,
    to_status text NOT NULL,
    reason text NOT NULL,
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    correlation_id uuid,
    occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE approved_actions (
    action_type text PRIMARY KEY,
    action_version text NOT NULL,
    command_path text NOT NULL,
    parameter_schema jsonb NOT NULL,
    expected_duration_seconds integer NOT NULL CHECK (expected_duration_seconds > 0),
    hard_timeout_seconds integer NOT NULL CHECK (hard_timeout_seconds >= expected_duration_seconds),
    retry_safe boolean NOT NULL DEFAULT false,
    enabled boolean NOT NULL DEFAULT false,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE work_orders (
    work_order_id uuid PRIMARY KEY,
    action_type text NOT NULL REFERENCES approved_actions(action_type),
    action_version text NOT NULL,
    status text NOT NULL CHECK (status IN ('queued','claimed','running','succeeded','failed','timed_out','blocked','cancelled')),
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    requested_by text NOT NULL,
    idempotency_key text NOT NULL UNIQUE,
    correlation_id uuid NOT NULL,
    causation_id uuid,
    expected_duration_seconds integer NOT NULL CHECK (expected_duration_seconds > 0),
    hard_timeout_seconds integer NOT NULL CHECK (hard_timeout_seconds >= expected_duration_seconds),
    lease_owner text,
    lease_expires_at timestamptz,
    last_heartbeat_at timestamptz,
    started_at timestamptz,
    finished_at timestamptz,
    result_report jsonb,
    error_checkpoint text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX work_orders_dispatch_idx ON work_orders (status, created_at);
CREATE INDEX work_orders_lease_idx ON work_orders (lease_expires_at) WHERE status IN ('claimed','running');

CREATE TABLE work_order_attempts (
    attempt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    work_order_id uuid NOT NULL REFERENCES work_orders(work_order_id),
    attempt integer NOT NULL CHECK (attempt > 0),
    worker_id text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    exit_code integer,
    report_ref text,
    UNIQUE (work_order_id, attempt)
);

CREATE TABLE steward_escalations (
    escalation_id uuid PRIMARY KEY,
    work_order_id uuid REFERENCES work_orders(work_order_id),
    checkpoint_id text NOT NULL,
    reason text NOT NULL,
    state text NOT NULL CHECK (state IN ('open','acknowledged','resolved')),
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    acknowledged_at timestamptz,
    resolved_at timestamptz
);

INSERT INTO roadmap_items (waypoint_id, parent_waypoint_id, sort_order, title, description, status, acceptance_criteria, completed_at) VALUES
('RV-001', NULL, 10, 'Foundation', 'Repository, governing constraints, and PostgreSQL authority.', 'completed', '["foundation commit verified"]', now()),
('RV-002', NULL, 20, 'River event runtime', 'Transactional append, replay, and aggregate reading.', 'completed', '["live idempotency acceptance"]', now()),
('RV-003', NULL, 30, 'Diagnostic persistence', 'Database diagnostics plus non-authoritative emergency evidence.', 'completed', '["normal and induced fallback acceptance"]', now()),
('RV-004', NULL, 40, 'Riverview Relay', 'Waypoint, work-order, runner, dashboard, and MCP communication loop.', 'active', '["full loop acceptance"]', NULL),
('RV-004.1', 'RV-004', 10, 'Relay data foundation', 'Durable waypoints, actions, work orders, leases, and escalations.', 'active', '["claim heartbeat completion timeout acceptance"]', NULL),
('RV-004.2', 'RV-004', 20, 'Local runner', 'Execute only registered actions under bounded policy.', 'pending', '["no-op and induced timeout acceptance"]', NULL),
('RV-004.3', 'RV-004', 30, 'Steward status view', 'Auto-refreshing waypoint and run visibility.', 'pending', '["latest waypoint automatically visible"]', NULL),
('RV-004.4', 'RV-004', 40, 'Read-only MCP relay', 'Retrieve waypoints, reports, diagnostics, and Cookbook entries.', 'pending', '["conversation reads latest run"]', NULL),
('RV-004.5', 'RV-004', 50, 'Full-loop mailbox', 'Enqueue approved work and return its report with escalation.', 'pending', '["doorbell to completion loop"]', NULL)
ON CONFLICT (waypoint_id) DO NOTHING;

INSERT INTO approved_actions (action_type, action_version, command_path, parameter_schema, expected_duration_seconds, hard_timeout_seconds, retry_safe, enabled)
VALUES ('relay.noop', '0.4.0', 'tools/powershell/relay/Invoke-RiverviewNoOp.ps1', '{"type":"object","additionalProperties":false}'::jsonb, 5, 30, true, true)
ON CONFLICT (action_type) DO UPDATE SET action_version=EXCLUDED.action_version, parameter_schema=EXCLUDED.parameter_schema, updated_at=now();

COMMIT;