-- Riverview Persistent Relay Worker
-- Version: 0.6.0
-- Migration: 0005

BEGIN;
CREATE TABLE relay_workers (
    worker_id text PRIMARY KEY,
    state text NOT NULL CHECK (state IN ('starting','idle','running','stopping','stopped','failed')),
    process_id integer NOT NULL,
    host_name text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    last_notification_at timestamptz,
    last_work_order_id uuid REFERENCES work_orders(work_order_id),
    completed_orders bigint NOT NULL DEFAULT 0 CHECK (completed_orders >= 0),
    failed_orders bigint NOT NULL DEFAULT 0 CHECK (failed_orders >= 0),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX relay_workers_last_seen_idx ON relay_workers(last_seen_at);

UPDATE roadmap_items SET status='completed',completed_at=now(),updated_at=now()
WHERE waypoint_id IN ('RV-004.1','RV-004.2');
INSERT INTO roadmap_transitions(waypoint_id,from_status,to_status,reason,evidence_refs)
VALUES
('RV-004.1','active','completed','Relay lifecycle and persistent worker acceptance passed.','["migration:0005"]'::jsonb),
('RV-004.2','pending','completed','Restricted execution and notification-driven dispatch passed.','["runner:v0.5.2","worker:v0.6.0"]'::jsonb);
COMMIT;