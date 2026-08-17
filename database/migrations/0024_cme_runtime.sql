CREATE TABLE cme_runtime_status (
    status_id boolean PRIMARY KEY DEFAULT true CHECK (status_id = true),
    consumer_id text NOT NULL UNIQUE,
    runtime_instance_id uuid NOT NULL,
    runtime_started_at timestamptz NOT NULL,
    last_heartbeat_at timestamptz NOT NULL,
    current_state text NOT NULL,
    current_state_since timestamptz NOT NULL,
    last_river_sequence_seen bigint NOT NULL DEFAULT 0,
    last_event_id uuid,
    last_event_type text,
    last_event_observed_at timestamptz,
    current_objective_id uuid,
    current_stage_id uuid,
    current_correlation_id uuid,
    current_action text,
    last_progress_at timestamptz,
    last_successful_progress_summary text,
    waiting_reason text,
    steward_attention_required boolean NOT NULL DEFAULT false,
    last_failure_code text,
    last_failure_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX cme_runtime_status_heartbeat_idx ON cme_runtime_status(last_heartbeat_at);

CREATE OR REPLACE FUNCTION riverview_notify_cme_river_event()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM pg_notify(
        'riverview_river_events',
        json_build_object(
            'sequence_id', NEW.sequence_id,
            'event_id', NEW.event_id,
            'event_type', NEW.event_type,
            'aggregate_type', NEW.aggregate_type,
            'aggregate_id', NEW.aggregate_id,
            'correlation_id', NEW.correlation_id,
            'causation_id', NEW.causation_id
        )::text
    );
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS river_events_cme_notify ON river_events;
CREATE TRIGGER river_events_cme_notify
AFTER INSERT ON river_events
FOR EACH ROW EXECUTE FUNCTION riverview_notify_cme_river_event();
