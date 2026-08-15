from datetime import UTC, datetime, timedelta

from riverview.security.credentials import CredentialLifecycle


def test_credential_lifecycle_is_reference_only_and_expiry_safe() -> None:
    c=CredentialLifecycle(); record=c.issue("test",reference="dpapi://fixture",expires_at=datetime.now(UTC)+timedelta(minutes=1),secret_for_test_only="synthetic")
    assert record.usable() and record.fingerprint != "synthetic"
    assert not c.revoke(record).usable()
    expired=c.issue("test",reference="dpapi://fixture",expires_at=datetime.now(UTC)-timedelta(seconds=1))
    assert not expired.usable()
