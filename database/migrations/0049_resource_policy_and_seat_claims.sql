-- Durable strategic Codex resource policy and exclusive seat leases.
-- Migration: 0049

BEGIN;

CREATE TABLE IF NOT EXISTS resource_policy (
    policy_id text PRIMARY KEY,
    revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
    mode text NOT NULL CHECK (mode IN ('HIGHEST_CAPACITY','BALANCED','ROUND_ROBIN','DRAIN','PRESERVE','SOONEST_ROLLOVER','MAXIMIZE_RUNWAY','PRIORITY')),
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    changed_by text NOT NULL,
    authority text NOT NULL,
    rationale text,
    steward_lock boolean NOT NULL DEFAULT false,
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS resource_policy_audit (
    audit_id uuid PRIMARY KEY,
    policy_id text NOT NULL REFERENCES resource_policy(policy_id),
    previous_revision bigint,
    new_revision bigint NOT NULL,
    previous_mode text,
    new_mode text NOT NULL,
    previous_parameters jsonb,
    new_parameters jsonb NOT NULL,
    actor text NOT NULL,
    authority text NOT NULL,
    rationale text,
    source_request_id text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS resource_seat_claims (
    claim_id uuid PRIMARY KEY,
    seat_id text NOT NULL CHECK (seat_id IN ('C1','C2','C3')),
    work_id text NOT NULL,
    owner_id text NOT NULL,
    state text NOT NULL CHECK (state IN ('claimed','starting','running','released','failed','expired')),
    safe_fingerprint text,
    claimed_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz,
    last_heartbeat_at timestamptz NOT NULL DEFAULT now(),
    lease_expires_at timestamptz NOT NULL,
    released_at timestamptz,
    release_reason text
);

CREATE UNIQUE INDEX IF NOT EXISTS resource_seat_claim_active_idx
    ON resource_seat_claims(seat_id) WHERE state IN ('claimed','starting','running');
CREATE INDEX IF NOT EXISTS resource_seat_claim_lease_idx
    ON resource_seat_claims(lease_expires_at) WHERE state IN ('claimed','starting','running');

INSERT INTO resource_policy(policy_id,mode,parameters,changed_by,authority,rationale)
VALUES ('codex-fleet','HIGHEST_CAPACITY','{}'::jsonb,'system','system','initial durable default')
ON CONFLICT (policy_id) DO NOTHING;

COMMIT;