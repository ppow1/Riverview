"""Synthetic credential lifecycle metadata; secret values never enter Riverview."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class CredentialRecord:
    credential_id: UUID
    owner: str
    classification: str
    reference: str
    fingerprint: str
    status: str
    expires_at: datetime | None
    version: int = 1
    def usable(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(UTC)
        return self.status == "active" and (self.expires_at is None or self.expires_at > now)

class CredentialLifecycle:
    def issue(self, owner: str, *, reference: str, classification: str = "credential", expires_at: datetime | None = None, secret_for_test_only: str | None = None) -> CredentialRecord:
        if classification != "credential" or not owner.strip() or not reference.strip(): raise ValueError("RIV-SEC-0003: credential metadata is invalid.")
        fingerprint = sha256(secret_for_test_only.encode()).hexdigest() if secret_for_test_only is not None else "external-reference-only"
        return CredentialRecord(uuid4(), owner, classification, reference, fingerprint, "active", expires_at)
    def rotate(self, record: CredentialRecord, *, reference: str, secret_for_test_only: str | None = None) -> CredentialRecord:
        replacement = self.issue(record.owner, reference=reference, expires_at=record.expires_at, secret_for_test_only=secret_for_test_only)
        return replace(replacement, version=record.version + 1)
    def revoke(self, record: CredentialRecord) -> CredentialRecord: return replace(record, status="revoked")
