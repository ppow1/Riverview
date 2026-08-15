"""Reference-only backup/restore state harness; no secret material is stored."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BackupRestoreFixture:
    object_reference: str
    classification: str
    content_hash: str
    credential_reference: str
    state: str = "prepared"

    def transition(self, state: str) -> BackupRestoreFixture:
        if state not in {"encrypted", "backed_up", "restored", "decrypted", "verified"}:
            raise ValueError("RIV-SEC-0006: backup/restore state is closed.")
        return BackupRestoreFixture(self.object_reference, self.classification, self.content_hash, self.credential_reference, state)
