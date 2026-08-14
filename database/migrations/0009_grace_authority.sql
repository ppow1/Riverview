-- Riverview Grace Identity and Authority Contract
-- Version: 0.1.0
-- Migration: 0009

BEGIN;

CREATE TABLE grace_identities (
    grace_id text PRIMARY KEY,
    display_name text NOT NULL,
    role text NOT NULL,
    authority_version text NOT NULL,
    enabled boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE grace_authority_rules (
    grace_id text NOT NULL REFERENCES grace_identities(grace_id),
    capability text NOT NULL,
    effect text NOT NULL CHECK(effect IN ('allow','deny','escalate')),
    scope text NOT NULL,
    requires_steward boolean NOT NULL DEFAULT false,
    reason text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(grace_id,capability)
);

CREATE TABLE grace_authority_decisions (
    decision_id uuid PRIMARY KEY,
    grace_id text NOT NULL REFERENCES grace_identities(grace_id),
    capability text NOT NULL,
    requested_scope text NOT NULL,
    decision text NOT NULL CHECK(decision IN ('allow','deny','escalate')),
    reason text NOT NULL,
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    correlation_id uuid,
    decided_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO grace_identities(grace_id,display_name,role,authority_version)
VALUES('grace','Grace','operational_coordinator','0.1.0')
ON CONFLICT(grace_id) DO UPDATE SET
    display_name=EXCLUDED.display_name,
    role=EXCLUDED.role,
    authority_version=EXCLUDED.authority_version,
    enabled=true,
    updated_at=now();

INSERT INTO grace_authority_rules(grace_id,capability,effect,scope,requires_steward,reason) VALUES
('grace','read_authoritative_state','allow','bounded_river_metadata',false,'Grace may read bounded authoritative operational metadata required for coordination.'),
('grace','evaluate_progression','allow','declared_dependencies_and_evidence',false,'Grace may evaluate whether accepted work is ready to progress.'),
('grace','record_coordination_evidence','allow','grace_authority_decisions',false,'Grace may record its own bounded coordination decisions and evidence.'),
('grace','change_mission','deny','all',true,'Mission changes belong to the Steward.'),
('grace','change_authority_model','deny','all',true,'Authority-model changes belong to the Steward.'),
('grace','bypass_steward_checkpoint','deny','all',true,'Required Steward checkpoints cannot be bypassed.'),
('grace','arbitrary_sql','deny','all',true,'Grace receives named capabilities, never arbitrary SQL authority.'),
('grace','arbitrary_shell','deny','all',true,'Grace receives named capabilities, never arbitrary shell authority.'),
('grace','access_undercurrent','deny','ordinary_river',true,'Undercurrent access is excluded from ordinary Grace coordination.'),
('grace','infer_authority_from_conversation','deny','all',true,'Conversation text never silently grants executable authority.')
ON CONFLICT(grace_id,capability) DO UPDATE SET
    effect=EXCLUDED.effect,
    scope=EXCLUDED.scope,
    requires_steward=EXCLUDED.requires_steward,
    reason=EXCLUDED.reason,
    updated_at=now();

COMMIT;