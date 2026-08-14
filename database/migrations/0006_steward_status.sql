-- Riverview Steward Status View
-- Version: 0.7.0
-- Migration: 0006

BEGIN;
CREATE TABLE service_endpoints (
    service_id text PRIMARY KEY,
    service_name text NOT NULL,
    bind_host text NOT NULL,
    port integer NOT NULL CHECK (port BETWEEN 1 AND 65535),
    health_path text NOT NULL,
    authority text NOT NULL CHECK (authority IN ('read_only','restricted_action','authoritative')),
    enabled boolean NOT NULL DEFAULT true,
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(bind_host,port)
);
INSERT INTO service_endpoints(service_id,service_name,bind_host,port,health_path,authority)
VALUES('steward-status','Riverview Steward Status','127.0.0.1',8770,'/healthz','read_only')
ON CONFLICT(service_id) DO UPDATE SET service_name=EXCLUDED.service_name,bind_host=EXCLUDED.bind_host,port=EXCLUDED.port,health_path=EXCLUDED.health_path,authority=EXCLUDED.authority,enabled=true,updated_at=now();
UPDATE roadmap_items SET status='completed',completed_at=now(),updated_at=now() WHERE waypoint_id='RV-004.3';
INSERT INTO roadmap_transitions(waypoint_id,from_status,to_status,reason,evidence_refs)
VALUES('RV-004.3','pending','completed','Local read-only Steward status acceptance passed.','["migration:0006","service:steward-status"]'::jsonb);
COMMIT;