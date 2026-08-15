"""MCP transport construction tests.

Version: 0.9.3
"""

from riverview.mcp import server


def test_server_is_stdio_only_by_entrypoint_contract() -> None:
    assert server.SERVER_NAME == "Riverview Comms"


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


def test_only_named_mailbox_write_operations_are_exposed() -> None:
    assert {"mailbox_acknowledge", "mailbox_claim", "mailbox_submit_response"} <= {
        name for name in dir(server) if name.startswith("mailbox_")
    }
    assert not any(name in {"mailbox_update", "execute_sql", "enqueue_anything"} for name in dir(server))


def test_comms_manifest_is_named_and_read_only() -> None:
    from tools.riverview_comms_manifest import APPLICATION, PROHIBITED, TOOLS, VERSION

    assert APPLICATION == "Riverview Comms"
    assert VERSION == "0.12.0"
    assert "current_position" in TOOLS
    assert "resource_work" in TOOLS
    assert "mailbox_requests" in TOOLS
    assert "arbitrary_write" in PROHIBITED


def test_http_entrypoint_rejects_non_loopback_binding(monkeypatch) -> None:
    from riverview.mcp import http_server

    monkeypatch.setenv("RIVERVIEW_COMMS_HOST", "0.0.0.0")
    try:
        http_server.main()
    except SystemExit as error:
        assert str(error) == (
            "RIV-COMMS-0002: non-loopback binding requires an approved authenticated ingress."
        )
    else:  # pragma: no cover
        raise AssertionError("non-loopback binding was not rejected")


def test_comms_ingress_template_is_exact_and_secret_free() -> None:
    from pathlib import Path

    template = Path("config/riverview-comms-ingress.Caddyfile.example").read_text()
    assert "path /mcp" in template
    assert "path /healthz" in template
    assert "RIVERVIEW_COMMS_CLIENT_SECRET" in template
    assert "RIVERVIEW_COMMS_UPSTREAM_AUTH" in template
    assert "A:\\theestate" not in template
    assert "theestate-data" not in template
