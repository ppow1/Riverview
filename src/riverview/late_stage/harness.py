"""Small evidence harnesses for migration, shadow operation, and maturity audit."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MigrationRecord:
    source_id: str
    destination_id: str
    source_hash: str
    destination_hash: str
    classification: str
    rollback_reference: str

    @property
    def verified(self) -> bool:
        return self.source_hash == self.destination_hash and bool(self.rollback_reference)


@dataclass(frozen=True, slots=True)
class ShadowDrill:
    scenario: str
    destructive_action_count: int
    checkpoint: str
    recovery: str

    @property
    def safe(self) -> bool:
        return self.destructive_action_count == 0 and bool(self.checkpoint and self.recovery)


@dataclass(frozen=True, slots=True)
class AuditLink:
    checkpoint: str
    cookbook_entry: str
    failure_evidence: str
    recovery_evidence: str
    verification_evidence: str

    @property
    def executable(self) -> bool:
        return all(
            value.strip()
            for value in (
                self.checkpoint,
                self.cookbook_entry,
                self.failure_evidence,
                self.recovery_evidence,
                self.verification_evidence,
            )
        )
