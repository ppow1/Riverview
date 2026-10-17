"""Static contract checks for the OAuth-to-existing-Comms5 ingress path."""

from pathlib import Path


def test_oauth_ingress_preserves_comms4_and_the_full_comms5_route() -> None:
    config = Path("config/riverview-comms5-ingress.Caddyfile.example").read_text(encoding="utf-8")
    assert "path /comms5/mcp" in config
    assert "uri replace /comms5/mcp /mcp" in config
    assert "127.0.0.1:11826" in config
    assert "127.0.0.1:11827" in config
    assert "forward_auth 127.0.0.1:11827" in config
    assert "uri /oauth/verify" in config
    assert "X-Riverview-Comms5-Principal steward" in config
    assert "RIVERVIEW_COMMS5_UPSTREAM_AUTH" in config
    assert "RIVERVIEW_COMMS5_CLIENT_SECRET" in config
    assert "RIVERVIEW_COMMS5_OAUTH_PROXY_KEY" in config
    public_oauth = config.split("@comms5_oauth_public path", 1)[1].split("handle @comms5_oauth_public", 1)[0]
    assert "/oauth/verify" not in public_oauth
    assert "path /mcp" not in config


def test_oauth_service_is_loopback_only_and_uses_isolated_state() -> None:
    unit = Path("deploy/systemd/riverview-comms5-oauth.service").read_text(encoding="utf-8")
    assert "DynamicUser=true" in unit
    assert "RIVERVIEW_COMMS5_OAUTH_HOST=127.0.0.1" in unit
    assert "RIVERVIEW_COMMS5_OAUTH_PORT=11827" in unit
    assert "StateDirectory=riverview-comms5-oauth" in unit
    assert "ProtectSystem=strict" in unit
    assert "EnvironmentFile=/etc/riverview/comms5-oauth.env" in unit
