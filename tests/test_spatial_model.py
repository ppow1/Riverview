from __future__ import annotations

import pytest

from riverview.spatial.model import SpatialEntity, SpatialProjection


def test_spatial_projection_preserves_provenance_and_is_read_only() -> None:
    projection = SpatialProjection(
        (
            SpatialEntity("office:administration", "office", "Administration", "KNOWN", "estate://office/administration"),
            SpatialEntity("equipment:usb-unknown", "equipment", "USB endpoint", "UNKNOWN", "rv://physical-manifest"),
        )
    )
    assert len(projection.by_kind("office")) == 1
    assert projection.entities()[1].state == "UNKNOWN"
    assert not hasattr(projection, "execute")


def test_spatial_state_is_closed() -> None:
    with pytest.raises(ValueError, match="state is closed"):
        SpatialEntity("x", "room", "x", "MEASURED", "source")
