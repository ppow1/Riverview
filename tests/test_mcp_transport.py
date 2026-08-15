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
    assert {"mailbox_acknowledge", "mailbox_claim", "mailbox_submit_advisory_response"} <= {
        name for name in dir(server) if name.startswith("mailbox_")
    }
    assert not hasattr(server, "mailbox_submit_response")
    assert not any(name in {"mailbox_update", "execute_sql", "enqueue_anything"} for name in dir(server))


def test_advisory_response_has_fixed_safe_semantics(monkeypatch) -> None:
    captured = {}

    def fake_respond(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return {"status": "accepted"}

    monkeypatch.setattr(server.mailbox, "respond_reasoning", fake_respond)
    result = server.mailbox_submit_advisory_response(
        "00000000-0000-4000-8000-000000000000",
        "00000000-0000-4000-8000-000000000001",
        "bounded advisory",
        ["riverview://evidence/1"],
    )

    assert result == {"status": "accepted"}
    assert captured["response_type"] == "advice"
    assert captured["escalation_required"] is False
    assert captured["summary"] == "bounded advisory"
    assert captured["evidence_refs"] == ["riverview://evidence/1"]


def test_comms_manifest_is_named_and_read_only() -> None:
    from tools.riverview_comms_manifest import APPLICATION, PROHIBITED, TOOLS, VERSION

    assert APPLICATION == "Riverview Comms"
    assert VERSION == "0.14.0"
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
