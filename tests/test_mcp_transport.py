"""MCP transport construction tests.

Version: 0.9.3
"""

from riverview.mcp import server


def test_server_is_stdio_only_by_entrypoint_contract() -> None:
    assert server.SERVER_NAME == "Riverview Read-Only Relay"


def test_no_action_adapter_is_exposed_by_server_module() -> None:
    prohibited = {
        "enqueue",
        "execute_sql",
        "filesystem",
        "shell",
        "secret",
        "credential",
        "undercurrent",
        "write",
    }
    public = {name.lower() for name in dir(server) if not name.startswith("_")}
    assert not (public & prohibited)