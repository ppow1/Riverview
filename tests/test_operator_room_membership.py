from uuid import uuid4

import pytest

from riverview.operator.room_admin import RoomAdministration


def _projection() -> RoomAdministration:
    projection = RoomAdministration.__new__(RoomAdministration)
    projection.available = False
    projection.memberships = {}
    projection.administrators = {}
    return projection


def test_room_membership_expands_removes_and_readds_without_rewriting_history() -> None:
    projection = _projection()
    room_id = uuid4()
    projection.initialize(room_id, ("helen", "marie"))
    added = projection.add(room_id, "grace", actor="steward", context_window="last_20")
    assert projection.snapshot(room_id)["participants"] == ["helen", "marie", "grace"]
    removed = projection.remove(room_id, "marie", actor="steward")
    assert removed["state"] == "removed"
    assert projection.snapshot(room_id)["participants"] == ["helen", "grace"]
    readded = projection.add(room_id, "marie", actor="steward", context_window="from_this_point")
    assert readded["membership_id"] != added["membership_id"]
    assert projection.snapshot(room_id)["participants"] == ["helen", "grace", "marie"]
    assert len(projection.snapshot(room_id)["memberships"]) == 4


def test_room_admin_coadministration_and_last_admin_guard() -> None:
    projection = _projection()
    room_id = uuid4()
    projection.initialize(room_id, ("alfred", "grace"))
    projection.grant_admin(room_id, "alfred", actor="steward")
    projection.leave(room_id, actor="steward")
    assert {row["administrator_id"] for row in projection.snapshot(room_id)["administrators"]} == {"alfred"}
    with pytest.raises(ValueError, match="last room administrator"):
        projection.leave(room_id, actor="alfred")


def test_room_admin_cannot_remove_steward() -> None:
    projection = _projection()
    room_id = uuid4()
    projection.initialize(room_id, ("grace",))
    with pytest.raises(PermissionError):
        projection.remove(room_id, "steward", actor="grace")


def test_projection_marks_duplicate_active_rows_instead_of_hiding_drift() -> None:
    projection = RoomAdministration._projection(
        [{"resident_id": "grace", "state": "active"}, {"resident_id": "grace", "state": "active"}],
        [],
    )
    assert projection["active_participant_count"] == 2
    assert projection["duplicate_active_participant_ids"] == ["grace"]
    assert projection["membership_projection_consistent"] is False


def test_legacy_reconciliation_does_not_revive_removed_history() -> None:
    projection = _projection()
    room_id = uuid4()
    projection.initialize(room_id, ("grace",))
    projection.remove(room_id, "grace", actor="steward")
    repaired = projection.reconcile_legacy(room_id, ("grace", "RES-000001"))
    assert repaired["participants"] == []
    assert len(repaired["memberships"]) == 1


def test_legacy_reconciliation_backfills_only_empty_room() -> None:
    projection = _projection()
    room_id = uuid4()
    repaired = projection.reconcile_legacy(room_id, ("grace", "RES-000001"))
    assert repaired["participants"] == ["grace", "RES-000001"]
    assert repaired["active_participant_count"] == 2
