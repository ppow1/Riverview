from __future__ import annotations

import pytest

from riverview.late_stage.backup import BackupRestoreFixture
from riverview.security.declassification import DeclassificationRequest, authorize_declassification


def test_backup_restore_fixture_preserves_reference_metadata() -> None:
    fixture = BackupRestoreFixture("ref://synthetic", "sensitive", "hash", "credential://synthetic")
    for state in ("encrypted", "backed_up", "restored", "decrypted", "verified"):
        fixture = fixture.transition(state)
    assert fixture.state == "verified"
    assert fixture.classification == "sensitive"
    assert fixture.credential_reference == "credential://synthetic"


def test_declassification_requires_complete_explicit_approval() -> None:
    request = DeclassificationRequest("ref://synthetic", "sensitive", "private", "steward", "test", "audit://1")
    assert authorize_declassification(request, approved=True) == request.object_reference
    with pytest.raises(PermissionError):
        authorize_declassification(request, approved=False)
