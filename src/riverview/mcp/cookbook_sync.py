"""Synchronize bounded RV-004.4/RV-008 Cookbook projections into PostgreSQL.

Version: 0.10.0
"""

from __future__ import annotations

import json

from riverview.database import connect

ENTRIES = [
    (
        "RIV-MCP-0001",
        "Missing read surface",
        "Required bounded read surface is unavailable.",
        ["missing-method", "missing-projection"],
        ["Run python -m riverview.mcp_health."],
        "Restore only the missing fixed read adapter.",
        "Run MCP health and live protocol acceptance.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0001_READ_SURFACE.md",
    ),
    (
        "RIV-MCP-0002",
        "Prohibited authority exposed",
        "Read-only MCP surface exposes prohibited authority.",
        ["write-authority", "arbitrary-sql", "filesystem", "shell", "secret", "undercurrent"],
        ["List MCP tools and compare them with the exact read-only allowlist."],
        "Remove the prohibited tool or capability.",
        "Run live MCP tool-list and protocol acceptance.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0002_AUTHORITY_BOUNDARY.md",
    ),
    (
        "RIV-MCP-0003",
        "PostgreSQL read failure",
        "A fixed MCP read cannot reach authoritative PostgreSQL state.",
        ["database-connectivity", "schema-missing", "role-permission"],
        ["Run database health, then python -m riverview.mcp_health."],
        "Repair the smallest database connectivity or schema seam; do not add file fallback authority.",
        "Run database health and live MCP read acceptance.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0003_DATABASE_READ.md",
    ),
    (
        "RIV-MCP-0004",
        "Cookbook projection unavailable",
        "Bounded Cookbook projection is missing or unreadable.",
        ["table-missing", "projection-empty", "unsafe-content"],
        ["Query the fixed cookbook read through the MCP client."],
        "Restore bounded operational Cookbook projections only.",
        "Run cookbook sync and live MCP cookbook read.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0004_COOKBOOK_READ.md",
    ),
    (
        "RIV-MCP-0005",
        "Unbounded query request",
        "A requested retrieval limit exceeds the declared bound.",
        ["limit-overflow", "caller-controlled-unbounded-read"],
        ["Request limits above each maximum and verify clamping."],
        "Clamp to the declared maximum.",
        "Run bounded-limit unit tests and live MCP acceptance.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0005_BOUND_LIMIT.md",
    ),
    (
        "RIV-MCP-0006",
        "MCP transport acceptance failure",
        "The local stdio MCP protocol boundary does not initialize, enumerate, or execute allowed reads.",
        ["stdio-startup", "protocol-initialize", "tool-list", "tool-call", "authority-boundary"],
        ["Run python -m riverview.mcp.live_acceptance."],
        "Repair only the failing local MCP transport seam.",
        "Run the complete live MCP acceptance again.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0006_ACCEPTANCE.md",
    ),
    (
        "RIV-MCP-0007",
        "Mailbox payload rejected",
        "A mailbox request or response is missing a bounded payload/reference or exceeds its safe limit.",
        ["oversized-payload", "missing-payload", "unsafe-reference"],
        ["Run mailbox contract tests and inspect only bounded request metadata."],
        "Reject the message; keep large or protected content in classified local storage and retain only a safe reference.",
        "Run mailbox invalid-payload acceptance and verify no request lineage was created.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0007_MAILBOX_PAYLOAD.md",
    ),
    (
        "RIV-MCP-0008",
        "Mailbox correlation or lifecycle failure",
        "A duplicate delivery, claim, acknowledgement, response, or expiry does not preserve one request/response lineage.",
        [
            "duplicate-delivery",
            "duplicate-response",
            "claim-conflict",
            "expiry",
            "correlation-loss",
        ],
        [
            "Run python -m riverview.mailbox.live_acceptance and inspect mailbox_messages plus River events by correlation_id."
        ],
        "Repair the single mailbox transaction or idempotency seam; never replay work by inserting a second request.",
        "Repeat duplicate delivery and response acceptance, then verify one request, one response, and correlated River events.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0008_MAILBOX_CORRELATION.md",
    ),
    (
        "RIV-PLY-0001",
        "Doorbell boundary is not live-accepted",
        "The bounded Playwright adapter is prepared but no real browser conversation has been opened or accepted.",
        [
            "invalid-selector",
            "bounded-timeout",
            "authentication",
            "wrong-conversation",
            "live-checkpoint",
        ],
        ["Run tests/test_doorbell_contract.py and inspect the typed request/result correlation."],
        "Repair only the deterministic contract or harness; escalate any real browser, authentication, or conversation choice.",
        "Deterministic harness passes; Steward separately performs the RV-008.3 live checkpoint when authorized.",
        "docs/operations/troubleshooting/checkpoints/RIV-PLY-0001_DOORBELL_BOUNDARY.md",
    ),
    (
        "RIV-GRC-0004",
        "Momentum evaluation or checkpoint routing failure",
        "Grace cannot distinguish a ready declared stage from a blocked, stale, or Steward-gated stage.",
        ["dependency-failure", "stale-state", "authority-failure", "checkpoint-routing"],
        ["Run GraceMomentum.evaluate against PostgreSQL objective/stage state; inspect grace_transition_evaluations and grace_checkpoints."],
        "Repair only the declared dependency, lease, or authority seam; route unresolved intent to the durable checkpoint.",
        "Repeat evaluation and verify one idempotent decision with a stable checkpoint when required.",
        "docs/operations/troubleshooting/checkpoints/RIV-GRC-0004_MOMENTUM_CONTROL.md",
    ),
    (
        "RIV-CAP-0001",
        "Capability or dispatch evidence unavailable",
        "No measured healthy capability with current capacity can be selected for a bounded task.",
        ["provider-failure", "stale-capacity", "backoff", "dispatch-no-match"],
        ["Inspect capabilities and capability_capacity; compare supported task, health_status, observed_at, load, and backoff_until."],
        "Register or refresh only measured capability evidence; do not route to a descriptive or stale provider label.",
        "Deterministic selection returns the named capability and an auditable capacity reason, or a checkpoint is durable.",
        "docs/operations/troubleshooting/checkpoints/RIV-CAP-0001_CAPABILITY_DISPATCH.md",
    ),
    (
        "RIV-EXE-0001",
        "Autonomous envelope or Codex adapter failure",
        "A bounded execution envelope cannot start, times out, exits unsuccessfully, or fails independent reconciliation.",
        ["configuration", "base-sha", "path-scope", "transport", "provider-failure", "timeout", "reconciliation"],
        ["Inspect execution_envelopes and execution_results; verify the fixed local codex.cmd entry point, base SHA, allowed paths, and deadline."],
        "Use the smallest bounded executable, repository, or evidence repair; retry only registered retry-safe failures once.",
        "Re-run the bounded acceptance and verify typed result, changed paths, validation evidence, and reconciled status.",
        "docs/operations/troubleshooting/checkpoints/RIV-EXE-0001_AUTONOMOUS_CONTROL_PLANE.md",
    ),
    (
        "RIV-MCP-0010",
        "Steward seed draft or schema-boundary failure",
        "A seed is rejected, duplicated, promoted without explicit confirmation, or the new tool is absent from a bound ChatGPT schema.",
        ["payload-bound", "duplicate-seed", "authority-failure", "schema-stale", "external-platform"],
        ["Inspect steward_seed_drafts, the local MCP tool list, the manifest version, and the application/conversation schema separately."],
        "Keep the seed as a draft, refresh only the supported application binding, and require the fixed Steward confirmer for promotion.",
        "Verify one draft by idempotency key, no work order creation, explicit confirmation, and the expected schema at the actual boundary.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0010_STEWARD_SEED_SCHEMA.md",
    ),
    (
        "RIV-CAP-0002",
        "Lane ownership or result reconciliation failure",
        "A path is already owned or a typed provider result does not match an execution envelope.",
        ["path-conflict", "wrong-owner", "correlation-mismatch", "foreign-result", "conflicting-result"],
        ["Inspect execution_lanes, lane_path_owners, execution_envelopes, execution_results, and reconciliation_records."],
        "Release only the verified lane owner or reject the foreign/conflicting result; preserve all historical evidence.",
        "Repeat the bounded conflict/release or reconciliation probe and verify one owner and one typed decision.",
        "docs/operations/troubleshooting/checkpoints/RIV-CAP-0002_LANE_RECONCILIATION.md",
    ),
    (
        "RIV-MCP-0011",
        "Bounded bridge replay and recovery",
        "A bridge wake or MCP transport failure needs correlation-preserving retry or exactly-once escalation.",
        ["transport-failure", "duplicate-replay", "retry-exhaustion", "correlation-loss"],
        ["Inspect bridge_recovery_attempts and River events by recovery_id and correlation_id."],
        "Retry only the same recovery identity within its bounded budget; escalate once when exhausted.",
        "Run the induced failure/recovery acceptance and verify one recovery identity, preserved lineage, and at most one escalation.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0011_BRIDGE_REPLAY_RECOVERY.md",
    ),
]


def sync() -> dict[str, object]:
    component = "riverview.mcp.readonly.mailbox"
    applicability = {
        "kernel": ">=0.10.0",
        "waypoint": "RV-008.1/RV-008.2",
        "authority": "read_only",
    }

    with connect() as connection, connection.cursor() as cursor:
        for checkpoint_id, title, summary, classes, probes, repair, verify, source in ENTRIES:
            cookbook_entry = f"CB-{checkpoint_id}"
            entry_applicability = dict(applicability)
            if checkpoint_id in {"RIV-GRC-0004", "RIV-CAP-0001", "RIV-CAP-0002", "RIV-EXE-0001", "RIV-MCP-0010", "RIV-MCP-0011"}:
                entry_applicability.update({"kernel": ">=0.14.0", "waypoint": "RV-005.3/RV-006.1/RV-006.4/RV-006.5/RV-008.5/RV-008.6", "authority": "bounded_control_plane"})
            entry_applicability["source_path"] = source
            entry_applicability["title"] = title
            entry_applicability["summary"] = summary
            cursor.execute(
                """
                INSERT INTO cookbook_entries(
                    cookbook_entry, checkpoint_id, component, failure_classes,
                    diagnostic_procedure, repair_procedure, verification_procedure,
                    applicability, validation_state, validated_at, updated_at
                )
                VALUES(%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,'validated',now(),now())
                ON CONFLICT(checkpoint_id) DO UPDATE SET
                    cookbook_entry=EXCLUDED.cookbook_entry,
                    component=EXCLUDED.component,
                    failure_classes=EXCLUDED.failure_classes,
                    diagnostic_procedure=EXCLUDED.diagnostic_procedure,
                    repair_procedure=EXCLUDED.repair_procedure,
                    verification_procedure=EXCLUDED.verification_procedure,
                    applicability=EXCLUDED.applicability,
                    validation_state=EXCLUDED.validation_state,
                    validated_at=EXCLUDED.validated_at,
                    updated_at=EXCLUDED.updated_at
                """,
                (
                    cookbook_entry,
                    checkpoint_id,
                    component,
                    json.dumps(classes),
                    json.dumps(list(probes)),
                    json.dumps([repair]),
                    json.dumps([verify]),
                    json.dumps(entry_applicability),
                ),
            )
    return {
        "status": "healthy",
        "entries": len(ENTRIES),
        "version": "0.10.0",
        "schema": "authoritative-existing",
    }


if __name__ == "__main__":
    print(json.dumps(sync(), indent=2, sort_keys=True))
