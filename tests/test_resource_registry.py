from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from riverview.resources.registry import ResourceRegistry, ResourceSelection, ResourceSelectionError


def telemetry(tmp_path: Path) -> Path:
    path = tmp_path / "codex.json"
    path.write_text(json.dumps({
        "version": 1,
        "source": "codex app-server account/rateLimits/read",
        "seats": [
            {
                "seat_id": "C1",
                "capacity_identity": "codex.seat.C1",
                "collection_status": "available",
                "weekly_limit_percent_left": 24,
                "weekly_limit_reset_at": "2026-08-30T00:00:00Z",
                "observed_at": "2026-08-26T14:00:00Z",
            },
            {
                "seat_id": "C2",
                "capacity_identity": "codex.seat.C2",
                "collection_status": "available",
                "weekly_limit_percent_left": 82,
                "weekly_limit_reset_at": "2026-08-30T00:00:00Z",
                "observed_at": "2026-08-26T14:00:00Z",
            },
            {
                "seat_id": "C4",
                "capacity_identity": "codex.seat.C4",
                "collection_status": "unavailable",
                "weekly_limit_percent_left": None,
                "weekly_limit_reset_at": None,
                "observed_at": None,
            },
        ],
    }))
    return path


def test_fuel_adapter_discovers_arbitrary_seat_count(tmp_path: Path) -> None:
    registry = ResourceRegistry.from_codex_telemetry(telemetry(tmp_path))
    assert [item.resource_id for item in registry.resources] == [
        "codex.seat.C1", "codex.seat.C2", "codex.seat.C4",
    ]
    assert registry.resources[1].observed_capacity == 82
    assert registry.resources[2].available is False


def test_capacity_selection_prefers_fresh_observed_fuel_and_explains_choice(tmp_path: Path) -> None:
    registry = ResourceRegistry.from_codex_telemetry(telemetry(tmp_path))
    selected = registry.select(
        required_capability="bounded-engineering",
        classification="river",
        role="writer",
        now=datetime(2026, 8, 26, 14, 5, tzinfo=UTC),
    )
    assert isinstance(selected, ResourceSelection)
    assert selected.resource.resource_id == "codex.seat.C2"
    assert "weekly fuel 82" in selected.reason
    assert "fresh" in selected.reason


def test_stale_capacity_and_no_eligible_resource_fail_closed(tmp_path: Path) -> None:
    registry = ResourceRegistry.from_codex_telemetry(telemetry(tmp_path))
    stale = registry.select(
        required_capability="bounded-engineering",
        classification="river",
        role="writer",
        now=datetime(2026, 8, 27, tzinfo=UTC),
        freshness=timedelta(hours=1),
    )
    assert stale.resource is None
    assert "fresh" in stale.reason

    unavailable = ResourceRegistry.from_mappings([{
        "resource_id": "validator-only",
        "provider_id": "local",
        "model": "local-reviewer",
        "capabilities": ["bounded-engineering"],
        "classification_eligibility": ["river"],
        "health": "healthy",
        "available": True,
        "observed_capacity": 99,
        "observed_at": "2026-08-26T14:00:00Z",
        "roles": ["validator"],
        "independent_validation_only": True,
    }])
    result = unavailable.select(
        required_capability="bounded-engineering",
        classification="river",
        role="writer",
        now=datetime(2026, 8, 26, 14, 5, tzinfo=UTC),
    )
    assert result.resource is None
    assert "eligible" in result.reason


def test_writer_does_not_consume_only_independent_validator_resource() -> None:
    registry = ResourceRegistry.from_mappings([{
        "resource_id": "validator-only",
        "provider_id": "local",
        "model": "local-reviewer",
        "capabilities": ["bounded-engineering"],
        "classification_eligibility": ["river"],
        "health": "healthy",
        "available": True,
        "observed_capacity": 99,
        "observed_at": "2026-08-26T14:00:00Z",
        "roles": ["writer", "validator"],
        "independent_validation_only": True,
    }])
    result = registry.select(
        required_capability="bounded-engineering",
        classification="river",
        role="writer",
        now=datetime(2026, 8, 26, 14, 5, tzinfo=UTC),
    )
    assert result.resource is None
    assert "independent" in result.reason


def test_selection_revalidation_rejects_changed_resource_observation() -> None:
    original = ResourceRegistry.from_mappings([{
        "resource_id": "codex.seat.C1", "provider_id": "codex-cli", "model": "codex",
        "capabilities": ["bounded-engineering"], "classification_eligibility": ["river"],
        "health": "healthy", "available": True, "observed_capacity": 80,
        "observed_at": "2026-08-26T14:00:00Z", "roles": ["writer"],
    }])
    selection = original.select(
        required_capability="bounded-engineering", classification="river", role="writer",
        now=datetime(2026, 8, 26, 14, 5, tzinfo=UTC),
    )
    changed = ResourceRegistry.from_mappings([{
        "resource_id": "codex.seat.C1", "provider_id": "codex-cli", "model": "codex",
        "capabilities": ["bounded-engineering"], "classification_eligibility": ["river"],
        "health": "unknown", "available": False, "observed_capacity": None,
        "observed_at": "2026-08-26T14:00:00Z", "roles": ["writer"],
    }])
    with pytest.raises(ResourceSelectionError, match="changed"):
        changed.assert_current(selection)
