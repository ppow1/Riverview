"""Comms5 external transport configuration and boundary tests."""

import json
from pathlib import Path

from riverview.mcp import comms5_http_server


def test_comms5_http_transport_is_distinct_and_loopback_only() -> None:
    assert comms5_http_server.DEFAULT_PORT == 11826
    assert comms5_http_server.APPLICATION_NAME == "Riverview Comms5"


def test_comms5_deployment_template_separates_stdio_and_external() -> None:
    config = json.loads(Path("config/riverview-comms5.example.json").read_text(encoding="utf-8"))
    assert config["local_stdio"]["args"][-1] == "riverview.mcp.comms5_server"
    assert config["external_transport"]["loopback_endpoint"] == "http://127.0.0.1:11826/mcp"
    assert config["external_transport"]["public_endpoint"] == "https://riverview-comms.ionoge.com/comms5/mcp"
    assert config["external_transport"]["deployment_state"] != "live"


def test_comms5_proxy_template_does_not_change_comms4_route() -> None:
    template = Path("config/riverview-comms5-ingress.Caddyfile.example").read_text(encoding="utf-8")
    assert "path /comms5/mcp" in template
    assert "uri replace /comms5/mcp /mcp" in template
    assert "127.0.0.1:11826" in template
    assert "127.0.0.1:11827" in template
    assert "RIVERVIEW_COMMS5_CLIENT_SECRET" in template
    assert "forward_auth 127.0.0.1:11827" in template
    assert "uri /oauth/verify" in template
    assert "/oauth/verify" not in template.split("@comms5_oauth_public path", 1)[1].split("handle @comms5_oauth_public", 1)[0]
    assert "path /mcp" not in template
