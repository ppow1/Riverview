from riverview.classification import Classification, StorageReference
from riverview.security import ProtectedAccessBroker


def test_ordinary_caller_is_denied_protected_reference() -> None:
    reference = StorageReference("u1", "protected://fixture/u1", "a" * 64, "fixture", Classification.UNDERCURRENT, 4, "application/octet-stream", "synthetic")
    decision = ProtectedAccessBroker().decide(reference, caller="river", capability="read:bounded", purpose="status")
    assert not decision.allowed
    assert "capability" in decision.reason


def test_broker_only_decides_reference_access() -> None:
    reference = StorageReference("u1", "protected://fixture/u1", "a" * 64, "fixture", Classification.UNDERCURRENT, 4, "application/octet-stream", "synthetic")
    decision = ProtectedAccessBroker().decide(reference, caller="broker-test", capability="undercurrent:bounded-read", purpose="synthetic-acceptance")
    assert decision.allowed
    assert "payload remains outside River" in decision.reason
