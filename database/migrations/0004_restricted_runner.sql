-- Riverview Restricted Runner
-- Version: 0.5.0
-- Migration: 0004

BEGIN;
ALTER TABLE approved_actions ADD COLUMN command_sha256 text;

INSERT INTO approved_actions (action_type,action_version,command_path,parameter_schema,expected_duration_seconds,hard_timeout_seconds,retry_safe,enabled)
VALUES ('relay.timeout_probe','0.5.0','tools/powershell/relay/Invoke-RiverviewNoOp.ps1','{"type":"object","properties":{"delay_seconds":{"type":"integer","minimum":2,"maximum":5}},"required":["delay_seconds"],"additionalProperties":false}'::jsonb,1,1,true,true)
ON CONFLICT(action_type)DO UPDATE SET action_version=EXCLUDED.action_version,command_path=EXCLUDED.command_path,parameter_schema=EXCLUDED.parameter_schema,expected_duration_seconds=EXCLUDED.expected_duration_seconds,hard_timeout_seconds=EXCLUDED.hard_timeout_seconds,retry_safe=EXCLUDED.retry_safe,enabled=EXCLUDED.enabled,updated_at=now();

UPDATE approved_actions SET action_version='0.5.0',parameter_schema='{"type":"object","properties":{"delay_seconds":{"type":"integer","minimum":1,"maximum":5}},"required":["delay_seconds"],"additionalProperties":false}'::jsonb,expected_duration_seconds=3,hard_timeout_seconds=10,enabled=true,updated_at=now() WHERE action_type='relay.noop';

CREATE OR REPLACE FUNCTION notify_riverview_work_order() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN PERFORM pg_notify('riverview_work_orders',NEW.work_order_id::text);RETURN NEW;END;$$;
CREATE TRIGGER work_orders_notify_after_insert AFTER INSERT ON work_orders FOR EACH ROW WHEN(NEW.status='queued') EXECUTE FUNCTION notify_riverview_work_order();
COMMIT;