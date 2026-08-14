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
