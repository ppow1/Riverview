"""Read-only MCP Relay contract tests.

Version: 0.9.3
"""

from riverview.mcp import ReadOnlyRelay


def test_public_read_model_surface_is_read_only() -> None:
    relay = ReadOnlyRelay()
    methods = {
        name for name in dir(relay) if not name.startswith("_") and callable(getattr(relay, name))
    }
    for prohibited in (
        "enqueue",
        "execute_sql",
        "filesystem",
        "shell",
        "secret",
        "credential",
        "undercurrent",
        "write",
    ):
        assert prohibited not in methods


def test_limits_are_bounded() -> None:
    relay = ReadOnlyRelay()
    assert relay.waypoints.__defaults__ == (200,)
    assert relay.workers.__defaults__ == (50,)
    assert relay.work_orders.__defaults__ == (50,)
    assert relay.completed_reports.__defaults__ == (50,)
    assert relay.escalations.__defaults__ == (50,)
    assert relay.diagnostics.__defaults__ == (100,)
    assert relay.cookbook.__defaults__ == (100,)


def test_resource_model_rejects_protected_classification() -> None:
    relay = ReadOnlyRelay()
    import pytest

    with pytest.raises(ValueError, match="classification"):
        relay.resource_roadmap(classification="undercurrent")


def test_resource_model_is_paginated_and_named() -> None:
    relay = ReadOnlyRelay()
    assert relay._resource_args(999, -2, "river") == (200, 0, "river")
    assert all(
        hasattr(relay, name)
        for name in (
            "resource_roadmap",
            "resource_work",
            "resource_reports",
            "resource_diagnostics",
            "resource_cookbook",
            "resource_capacity",
        )
    )
