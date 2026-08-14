"""Read-only MCP Relay contract tests.

Version: 0.9.3
"""

from riverview.mcp import ReadOnlyRelay


def test_public_read_model_surface_is_read_only() -> None:
    relay = ReadOnlyRelay()
    methods = {
        name
        for name in dir(relay)
        if not name.startswith("_") and callable(getattr(relay, name))
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