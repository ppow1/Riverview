from __future__ import annotations

from riverview.late_stage.harness import AuditLink, MigrationRecord, ShadowDrill


def test_migration_and_shadow_harnesses_are_non_destructive() -> None:
    migration = MigrationRecord("estate:1", "river:1", "hash", "hash", "operational", "rollback:1")
    drill = ShadowDrill("provider-failure", 0, "RIV-REASON-0002", "recovery:1")
    audit = AuditLink("RIV-REASON-0002", "CB-RIV-REASON-0002", "failure:1", "recovery:1", "verify:1")
    assert migration.verified
    assert drill.safe
    assert audit.executable
