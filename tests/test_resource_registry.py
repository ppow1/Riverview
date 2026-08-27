from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from riverview.resources.registry import (
    ResourcePlanner,
    ResourcePolicy,
    ResourceRegistry,
    ResourceSelection,
    ResourceSelectionError,
    reset_refill_observed,
)


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


def test_codex_projection_preserves_seat_identity_and_current_execution_state(tmp_path: Path) -> None:
    path = telemetry(tmp_path)
    payload = json.loads(path.read_text())
    payload["seats"][0].update({
        "account": {"identity_fingerprint": "fingerprint-c1"},
        "current_execution_state": "busy",
        "reset_refill_observed": True,
    })
    path.write_text(json.dumps(payload))
    resource = ResourceRegistry.from_codex_telemetry(path).resources[0]
    assert resource.seat_id == "C1"
    assert resource.identity_fingerprint == "fingerprint-c1"
    assert resource.current_execution_state == "busy"
    assert resource.reset_refill_observed is True


def test_busy_codex_resource_is_excluded_from_automatic_selection(tmp_path: Path) -> None:
    path = telemetry(tmp_path)
    payload = json.loads(path.read_text())
    payload["seats"][0]["current_execution_state"] = "busy"
    path.write_text(json.dumps(payload))
    selected = ResourceRegistry.from_codex_telemetry(path).select_codex_seat(
        now=datetime(2026, 8, 26, 14, 5, tzinfo=UTC),
    )
    assert selected.resource is not None
    assert selected.resource.seat_id == "C2"


def test_reset_refill_requires_observed_capacity_jump() -> None:
    assert reset_refill_observed(35, 82, minimum_jump=20) is True
    assert reset_refill_observed(35, 48, minimum_jump=20) is False
    assert reset_refill_observed(None, 82, minimum_jump=20) is False


def test_mapping_records_observed_reset_refill_evidence() -> None:
    resource = ResourceRegistry.from_mappings([{
        "resource_id": "codex.seat.C1", "provider_id": "codex-cli",
        "capabilities": ["bounded-engineering"], "classification_eligibility": ["river"],
        "health": "healthy", "available": True, "observed_capacity": 82,
        "previous_observed_capacity": 35, "observed_at": "2026-08-26T14:00:00Z",
        "roles": ["writer"],
    }]).resources[0]
    assert resource.reset_refill_observed is True


def test_unknown_telemetry_is_excluded_from_automatic_selection() -> None:
    registry = ResourceRegistry.from_mappings([{
        "resource_id": "codex.seat.unknown", "provider_id": "codex-cli",
        "capabilities": ["bounded-engineering"], "classification_eligibility": ["river"],
        "health": "healthy", "available": True, "observed_capacity": None,
        "observed_at": None, "roles": ["writer"],
    }])
    selected = registry.select_codex_seat(now=datetime(2026, 8, 26, 14, 5, tzinfo=UTC))
    assert selected.resource is None
    assert "fresh" in selected.reason


def test_native_windows_are_retained_and_soonest_rollover_can_win() -> None:
    registry = ResourceRegistry.from_mappings([
        {"resource_id": "codex.seat.C1", "provider_id": "codex-cli", "capabilities": ["bounded-engineering"], "classification_eligibility": ["river"], "health": "healthy", "available": True, "observed_capacity": 60, "observed_at": "2026-08-27T00:00:00Z", "reset_at": "2026-08-28T00:00:00Z", "roles": ["writer"], "seat_id": "C1", "quota_windows": [{"native_name": "5-hour", "remaining_percent": 60, "resets_at": "2026-08-28T00:00:00Z"}, {"native_name": "7-day", "remaining_percent": 80, "resets_at": "2026-09-01T00:00:00Z"}]},
        {"resource_id": "codex.seat.C2", "provider_id": "codex-cli", "capabilities": ["bounded-engineering"], "classification_eligibility": ["river"], "health": "healthy", "available": True, "observed_capacity": 80, "observed_at": "2026-08-27T00:00:00Z", "reset_at": "2026-09-01T00:00:00Z", "roles": ["writer"], "seat_id": "C2", "quota_windows": [{"native_name": "5-hour", "remaining_percent": 80, "resets_at": "2026-09-01T00:00:00Z"}, {"native_name": "7-day", "remaining_percent": 80, "resets_at": "2026-09-01T00:00:00Z"}]},
    ])
    assert len(registry.resources[0].quota_windows) == 2
    selection = ResourcePlanner(registry).select(ResourcePolicy(mode="SOONEST_ROLLOVER"), now=datetime(2026, 8, 27, tzinfo=UTC))
    assert selection.resource.seat_id == "C1"


def test_policy_modes_support_drain_preserve_priority_and_round_robin() -> None:
    registry = ResourceRegistry.from_mappings([
        {"resource_id": f"codex.seat.{seat}", "provider_id": "codex-cli", "capabilities": ["bounded-engineering"], "classification_eligibility": ["river"], "health": "healthy", "available": True, "observed_capacity": 50, "observed_at": "2026-08-27T00:00:00Z", "reset_at": "2026-09-01T00:00:00Z", "roles": ["writer"], "seat_id": seat}
        for seat in ("C1", "C2", "C3")
    ])
    planner = ResourcePlanner(registry)
    now = datetime(2026, 8, 27, tzinfo=UTC)
    assert planner.select(ResourcePolicy(mode="DRAIN", target_seat="C3"), now=now).resource.seat_id == "C3"
    assert planner.select(ResourcePolicy(mode="PRESERVE", target_seat="C1"), now=now).resource.seat_id != "C1"
    assert planner.select(ResourcePolicy(mode="PRIORITY", priority_order=("C3", "C2", "C1")), now=now).resource.seat_id == "C3"
    assert [planner.select(ResourcePolicy(mode="ROUND_ROBIN"), now=now).resource.seat_id for _ in range(3)] == ["C1", "C2", "C3"]


def test_planner_can_exclude_a_seat_after_a_claim_race() -> None:
    now = datetime(2026, 8, 27, 0, 15, tzinfo=UTC)
    registry = ResourceRegistry.from_mappings([
        {"resource_id": f"codex.seat.{seat}", "provider_id": "codex-cli", "capabilities": ["bounded-engineering"], "classification_eligibility": ["river"], "health": "healthy", "available": True, "observed_capacity": 50, "observed_at": "2026-08-27T00:00:00Z", "reset_at": "2026-09-01T00:00:00Z", "roles": ["writer"], "seat_id": seat}
        for seat in ("C1", "C2", "C3")
    ])
    planner = ResourcePlanner(registry)
    first = planner.select(ResourcePolicy(mode="HIGHEST_CAPACITY"), now=now)
    second = planner.select(ResourcePolicy(mode="HIGHEST_CAPACITY"), now=now, excluded_seats={first.resource.seat_id})
    assert first.resource.seat_id == "C3"
    assert second.resource.seat_id != "C3"
def test_codex_selection_tie_break_is_deterministic(tmp_path: Path) -> None:
    path = telemetry(tmp_path)
    payload = json.loads(path.read_text())
    payload["seats"][0]["weekly_limit_percent_left"] = 82
    path.write_text(json.dumps(payload))
    selected = ResourceRegistry.from_codex_telemetry(path).select_codex_seat(
        now=datetime(2026, 8, 26, 14, 5, tzinfo=UTC),
    )
    assert selected.resource is not None
    assert selected.resource.seat_id == "C2"
