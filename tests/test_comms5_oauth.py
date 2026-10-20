# Riverview~ controlled test source
# File: tests/test_comms5_oauth.py
# Component: COMMS5-OAUTH
# Revision: 1.0.1 (predecessor 1.0.0 bytes in task backup manifest revision-1.0.0)
# Purpose: OAuth protocol, identity mapping, and additive provider profile qualification
# Execution Model: Disposable request-driven tests
# Observability: Pytest assertions and sanitized test runner output
# Dependencies: OAuth issuer modules, pytest, PyJWT/cryptography
# Authority: Synthetic identities and keys only; no production registration or grants
# Changed: 2026-10-19 UTC | RV-C3-PROVIDER-AUTH-PROOF-20261019 | Cover provider refresh rotation
# Backup: /home/admin1/.local/share/riverview/backups/RV-C3-PROVIDER-AUTH-PROOF-20261019/manifest.json

"""OAuth protocol and credential-to-Comms5 identity mapping tests."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import re
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

import pytest

from riverview.mcp.comms5_oauth import SCOPE, OAuthConfig, OAuthError, OAuthService
from riverview.mcp.comms5_oauth_server import COOKIE_NAME, create_handler
from riverview.mcp.comms5_server import _list_tools_with_oauth_security_schemes

STABLE_REDIRECT = "https://chatgpt.com/connector_platform_oauth_redirect"
STEWARD_CREDENTIAL = "test-existing-steward-connector-credential"
ISSUER = "https://riverview-comms.ionoge.com"
RESOURCE = "https://riverview-comms.ionoge.com/comms5/mcp"


def test_every_comms5_tool_advertises_oauth_scope() -> None:
    tools = asyncio.run(_list_tools_with_oauth_security_schemes())
    assert tools
    assert all(tool.securitySchemes == [{"type": "oauth2", "scopes": [SCOPE]}] for tool in tools)


def _challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def _flow(service: OAuthService) -> tuple[str, str, str, str]:
    client = service.register_client({
        "client_name": "ChatGPT Comms5",
        "redirect_uris": [STABLE_REDIRECT],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    })
    verifier = "m6FjZYXBh2kA3-4.wSTed8h0EgzXfK9rR1tYUQwP6Dc"
    state = "opaque-state-value"
    transaction, csrf, _ = service.begin_authorization({
        "client_id": client["client_id"],
        "redirect_uri": STABLE_REDIRECT,
        "response_type": "code",
        "state": state,
        "code_challenge": _challenge(verifier),
        "code_challenge_method": "S256",
        "scope": SCOPE,
        "resource": RESOURCE,
    })
    location, _ = service.complete_authorization(transaction, csrf, STEWARD_CREDENTIAL, STEWARD_CREDENTIAL)
    code = parse_qs(urlsplit(location).query)["code"][0]
    assert parse_qs(urlsplit(location).query)["state"] == [state]
    assert parse_qs(urlsplit(location).query)["iss"] == [ISSUER]
    return client["client_id"], verifier, code, STABLE_REDIRECT


def test_metadata_advertises_chatgpt_pkce_resource_and_issuer_contract(tmp_path) -> None:
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "oauth.sqlite3")))
    resource = service.resource_metadata()
    metadata = service.authorization_metadata()

    assert resource["resource"] == RESOURCE
    assert resource["authorization_servers"] == [ISSUER]
    assert metadata["issuer"] == ISSUER
    assert metadata["authorization_response_iss_parameter_supported"] is True
    assert metadata["code_challenge_methods_supported"] == ["S256"]
    assert metadata["token_endpoint_auth_methods_supported"] == ["none"]
    assert metadata["client_id_metadata_document_supported"] is False
    assert metadata["scopes_supported"] == [SCOPE]
    assert "jwks_uri" not in metadata


def test_dcr_rejects_non_chatgpt_redirects(tmp_path) -> None:
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "oauth.sqlite3")))
    with pytest.raises(OAuthError, match="ChatGPT OAuth callback"):
        service.register_client({"redirect_uris": ["https://attacker.example/callback"]})


def test_dcr_reports_requested_public_client_grants(tmp_path) -> None:
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "oauth.sqlite3")))
    client = service.register_client({
        "redirect_uris": [STABLE_REDIRECT],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    })
    assert client["grant_types"] == ["authorization_code"]
    client_id = client["client_id"]
    verifier = "m6FjZYXBh2kA3-4.wSTed8h0EgzXfK9rR1tYUQwP6Dc"
    transaction, csrf, _ = service.begin_authorization({
        "client_id": client_id, "redirect_uri": STABLE_REDIRECT, "response_type": "code",
        "state": "one", "code_challenge": _challenge(verifier), "code_challenge_method": "S256",
        "scope": SCOPE, "resource": RESOURCE,
    })
    location, _ = service.complete_authorization(transaction, csrf, STEWARD_CREDENTIAL, STEWARD_CREDENTIAL)
    code = parse_qs(urlsplit(location).query)["code"][0]
    token = service.exchange_token({
        "grant_type": "authorization_code", "client_id": client_id, "code": code,
        "redirect_uri": STABLE_REDIRECT, "code_verifier": verifier, "resource": RESOURCE,
    })
    assert "refresh_token" not in token


def test_authorization_error_redirect_includes_issuer_identification(tmp_path) -> None:
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "oauth.sqlite3")))
    client = service.register_client({"redirect_uris": [STABLE_REDIRECT]})
    params = {
        "client_id": client["client_id"], "redirect_uri": STABLE_REDIRECT,
        "response_type": "code", "state": "retry-state", "code_challenge": "invalid",
        "code_challenge_method": "plain", "scope": SCOPE, "resource": RESOURCE,
    }
    with pytest.raises(OAuthError) as failure:
        service.begin_authorization(params)
    assert failure.value.redirect_url is not None
    query = parse_qs(urlsplit(failure.value.redirect_url).query)
    assert query["error"] == ["invalid_request"]
    assert query["state"] == ["retry-state"]
    assert query["iss"] == [ISSUER]


def test_pkce_code_is_one_time_and_issues_resource_bound_steward_token(tmp_path) -> None:
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "oauth.sqlite3")))
    client_id, verifier, code, redirect = _flow(service)
    form = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": code,
        "redirect_uri": redirect,
        "code_verifier": verifier,
        "resource": RESOURCE,
    }
    issued = service.exchange_token(form)
    assert issued["scope"] == SCOPE
    assert issued["token_type"] == "Bearer"
    assert service.validate_access_token(issued["access_token"]) == "steward"
    assert service.validate_access_token(issued["access_token"], resource="https://wrong.example/mcp") is None
    with pytest.raises(OAuthError, match="Authorization code"):
        service.exchange_token(form)


def test_pkce_wrong_verifier_and_wrong_resource_are_rejected(tmp_path) -> None:
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "oauth.sqlite3")))
    client_id, verifier, code, redirect = _flow(service)
    base = {
        "grant_type": "authorization_code", "client_id": client_id, "code": code,
        "redirect_uri": redirect, "code_verifier": verifier + "x", "resource": RESOURCE,
    }
    with pytest.raises(OAuthError, match="PKCE verifier"):
        service.exchange_token(base)
    base["code_verifier"] = verifier
    base["resource"] = "https://wrong.example/mcp"
    with pytest.raises(OAuthError, match="resource"):
        service.exchange_token(base)


def test_login_requires_existing_steward_credential_and_valid_csrf(tmp_path) -> None:
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "oauth.sqlite3")))
    service.register_client({"redirect_uris": [STABLE_REDIRECT]})
    verifier = "m6FjZYXBh2kA3-4.wSTed8h0EgzXfK9rR1tYUQwP6Dc"
    params = {
        "client_id": "", "redirect_uri": STABLE_REDIRECT, "response_type": "code", "state": "state",
        "code_challenge": _challenge(verifier), "code_challenge_method": "S256", "scope": SCOPE, "resource": RESOURCE,
    }
    with service._connect() as db:
        params["client_id"] = db.execute("SELECT client_id FROM oauth_clients LIMIT 1").fetchone()[0]
    transaction, csrf, _ = service.begin_authorization(params)
    with pytest.raises(OAuthError, match="credential was not accepted"):
        service.complete_authorization(transaction, csrf, "wrong-credential", STEWARD_CREDENTIAL)
    with pytest.raises(OAuthError, match="form validation failed"):
        service.complete_authorization(transaction, "wrong-csrf", STEWARD_CREDENTIAL, STEWARD_CREDENTIAL)
    with pytest.raises(OAuthError, match="not configured"):
        service.complete_authorization(transaction, csrf, STEWARD_CREDENTIAL, "")


def test_refresh_rotates_token_and_revocation_disables_access(tmp_path) -> None:
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "oauth.sqlite3")))
    client_id, verifier, code, redirect = _flow(service)
    issued = service.exchange_token({
        "grant_type": "authorization_code", "client_id": client_id, "code": code,
        "redirect_uri": redirect, "code_verifier": verifier, "resource": RESOURCE,
    })
    refreshed = service.exchange_token({
        "grant_type": "refresh_token", "client_id": client_id,
        "refresh_token": issued["refresh_token"], "resource": RESOURCE,
    })
    assert service.validate_access_token(issued["access_token"]) == "steward"
    assert service.validate_access_token(refreshed["access_token"]) == "steward"
    service.revoke(refreshed["access_token"], client_id)
    assert service.validate_access_token(refreshed["access_token"]) is None
    with pytest.raises(OAuthError, match="Refresh token"):
        service.exchange_token({
            "grant_type": "refresh_token", "client_id": client_id,
            "refresh_token": issued["refresh_token"], "resource": RESOURCE,
        })


def test_additive_provider_profile_issues_separate_signed_audience_and_subject(tmp_path) -> None:
    import jwt
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key_path = tmp_path / "provider-signing-key.pem"
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    key_path.chmod(0o600)
    db_path = str(tmp_path / "provider.sqlite3")
    base = OAuthConfig(ISSUER, RESOURCE, db_path)
    bootstrap = OAuthService(base)
    client = bootstrap.register_client({"client_name": "ChatGPT reasoning test",
        "redirect_uris": [STABLE_REDIRECT], "grant_types": ["authorization_code", "refresh_token"]})
    client_id = client["client_id"]
    provider_resource = "https://reasoning.example.test/mcp"
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, db_path,
        provider_resource=provider_resource, provider_subject="provider:synthetic-chatgpt",
        provider_client_ids=(client_id,), provider_signing_key_path=str(key_path)))
    verifier = "m6FjZYXBh2kA3-4.wSTed8h0EgzXfK9rR1tYUQwP6Dc"
    transaction, csrf, page = service.begin_authorization({
        "client_id": client_id, "redirect_uri": STABLE_REDIRECT,
        "response_type": "code", "state": "provider-state",
        "code_challenge": _challenge(verifier), "code_challenge_method": "S256",
        "scope": "reasoning:exchange", "resource": provider_resource,
    })
    assert "Authorize provider" in page
    location, _ = service.complete_authorization(transaction, csrf,
        STEWARD_CREDENTIAL, STEWARD_CREDENTIAL)
    code = parse_qs(urlsplit(location).query)["code"][0]
    issued = service.exchange_token({"grant_type": "authorization_code", "client_id": client_id,
        "code": code, "redirect_uri": STABLE_REDIRECT, "code_verifier": verifier,
        "resource": provider_resource})
    assert issued["scope"] == "reasoning:exchange"
    assert issued["refresh_token"]
    published_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(service.provider_jwks()["keys"][0]))
    claims = jwt.decode(issued["access_token"], published_key, algorithms=["RS256"],
        audience=provider_resource, issuer=ISSUER)
    assert claims["sub"] == "provider:synthetic-chatgpt"
    assert claims["client_id"] == client_id
    assert claims["scope"] == "reasoning:exchange"
    assert service.provider_jwks()["keys"][0]["kid"] == "rv-comms5-provider-rs256-v1"
    assert issued["expires_in"] == 300
    metadata = service.authorization_metadata()
    assert metadata["jwks_uri"] == ISSUER + "/oauth/jwks"
    assert "reasoning:exchange" in metadata["scopes_supported"]
    assert service.validate_access_token(issued["access_token"], resource=RESOURCE) is None
    for invalid_refresh in (
        {"client_id": "other-client", "resource": provider_resource, "scope": "reasoning:exchange"},
        {"client_id": client_id, "resource": RESOURCE, "scope": "reasoning:exchange"},
        {"client_id": client_id, "resource": provider_resource, "scope": SCOPE},
    ):
        with pytest.raises(OAuthError, match="Refresh token"):
            service.exchange_token({"grant_type": "refresh_token",
                "refresh_token": issued["refresh_token"], **invalid_refresh})
    refreshed = service.exchange_token({"grant_type": "refresh_token", "client_id": client_id,
        "refresh_token": issued["refresh_token"], "resource": provider_resource,
        "scope": "reasoning:exchange"})
    refreshed_claims = jwt.decode(refreshed["access_token"], published_key, algorithms=["RS256"],
        audience=provider_resource, issuer=ISSUER)
    assert refreshed_claims["sub"] == "provider:synthetic-chatgpt"
    assert refreshed["scope"] == "reasoning:exchange"
    assert refreshed["refresh_token"] != issued["refresh_token"]
    with pytest.raises(OAuthError, match="Refresh token"):
        service.exchange_token({"grant_type": "refresh_token", "client_id": client_id,
            "refresh_token": issued["refresh_token"], "resource": provider_resource,
            "scope": "reasoning:exchange"})


def test_provider_profile_rejects_unregistered_client_wrong_resource_and_steward_subject(tmp_path) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key_path = tmp_path / "provider-signing-key.pem"
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    key_path.chmod(0o600)
    db_path = str(tmp_path / "provider-deny.sqlite3")
    bootstrap = OAuthService(OAuthConfig(ISSUER, RESOURCE, db_path))
    approved_client = bootstrap.register_client({"redirect_uris": [STABLE_REDIRECT]})["client_id"]
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, db_path,
        provider_resource="https://reasoning.example.test/mcp",
        provider_subject="provider:synthetic-chatgpt", provider_client_ids=(approved_client,),
        provider_signing_key_path=str(key_path)))
    client = service.register_client({"redirect_uris": [STABLE_REDIRECT]})
    args = {"client_id": client["client_id"], "redirect_uri": STABLE_REDIRECT,
        "response_type": "code", "state": "denied-state",
        "code_challenge": _challenge("m6FjZYXBh2kA3-4.wSTed8h0EgzXfK9rR1tYUQwP6Dc"),
        "code_challenge_method": "S256", "scope": "reasoning:exchange",
        "resource": "https://reasoning.example.test/mcp"}
    with pytest.raises(OAuthError, match="scope"):
        service.begin_authorization(args)
    args["client_id"] = approved_client
    args["resource"] = "https://wrong.example/mcp"
    with pytest.raises(OAuthError, match="scope"):
        service.begin_authorization(args)
    args["resource"] = "https://reasoning.example.test/mcp"
    args["scope"] = SCOPE
    with pytest.raises(OAuthError, match="scope"):
        service.begin_authorization(args)
    with pytest.raises(ValueError, match="non-Steward"):
        OAuthConfig(ISSUER, RESOURCE, db_path, provider_resource="https://reasoning.example.test/mcp",
            provider_subject="steward", provider_client_ids=("approved-test-client",),
            provider_signing_key_path=str(key_path))
    with pytest.raises(ValueError, match="distinct HTTPS"):
        OAuthConfig(ISSUER, RESOURCE, db_path, provider_resource=RESOURCE,
            provider_subject="provider:test", provider_client_ids=("approved-test-client",),
            provider_signing_key_path=str(key_path))


def test_provider_discovery_and_jwks_are_exposed_only_with_profile_enabled(tmp_path) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key_path = tmp_path / "provider-signing-key.pem"
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    key_path.chmod(0o600)
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "provider-http.sqlite3"),
        provider_resource="https://reasoning.example.test/mcp", provider_subject="provider:test",
        provider_client_ids=("registered-test-client",), provider_signing_key_path=str(key_path)))
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(service))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        root = f"http://127.0.0.1:{server.server_port}"
        with urlopen(root + "/.well-known/oauth-authorization-server") as response:
            metadata = json.load(response)
        with urlopen(root + "/oauth/jwks") as response:
            jwks = json.load(response)
        assert metadata["jwks_uri"] == ISSUER + "/oauth/jwks"
        assert jwks["keys"][0]["kid"] == "rv-comms5-provider-rs256-v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_real_http_metadata_registration_and_forward_auth_boundary(tmp_path) -> None:
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "oauth.sqlite3")))
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(service))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        root = f"http://127.0.0.1:{server.server_port}"
        with urlopen(root + "/.well-known/oauth-protected-resource") as response:
            assert json.load(response)["resource"] == RESOURCE
        with urlopen(root + "/.well-known/oauth-authorization-server") as response:
            metadata = json.load(response)
            assert metadata["code_challenge_methods_supported"] == ["S256"]
            assert "jwks_uri" not in metadata
        with pytest.raises(HTTPError) as disabled_jwks:
            urlopen(root + "/oauth/jwks")
        assert disabled_jwks.value.code == 503
        request = Request(root + "/oauth/register", data=json.dumps({"redirect_uris": [STABLE_REDIRECT]}).encode(), headers={"Content-Type": "application/json"})
        with urlopen(request) as response:
            client_id = json.load(response)["client_id"]
        denied = Request(root + "/oauth/verify", data=b"", method="POST")
        with pytest.raises(HTTPError) as failure:
            urlopen(denied)
        assert failure.value.code == 401
        assert "oauth-protected-resource" in failure.value.headers["WWW-Authenticate"]
        with pytest.raises(HTTPError) as get_failure:
            urlopen(root + "/oauth/verify")
        assert get_failure.value.code == 401
        code_client, verifier, code, redirect = _flow(service)
        assert code_client != client_id
        token_request = Request(
            root + "/oauth/token",
            data=urlencode({
                "grant_type": "authorization_code", "client_id": code_client,
                "code": code, "redirect_uri": redirect, "code_verifier": verifier,
                "resource": RESOURCE,
            }).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(token_request) as response:
            access_token = json.load(response)["access_token"]
        verify_request = Request(
            root + "/oauth/verify", data=b"", method="POST",
            headers={"Authorization": "Bearer " + access_token},
        )
        with urlopen(verify_request) as response:
            assert response.status == 200
            assert response.headers["X-Riverview-Comms5-Principal"] == "steward"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_real_http_chatgpt_oauth_pkce_browser_exchange(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("RIVERVIEW_COMMS5_CLIENT_SECRET", STEWARD_CREDENTIAL)
    monkeypatch.setenv("RIVERVIEW_COMMS5_OAUTH_PROXY_KEY", "test-caddy-proxy-key")
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "oauth.sqlite3")))
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(service))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    class CaptureRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    try:
        root = f"http://127.0.0.1:{server.server_port}"
        opener = build_opener(CaptureRedirect)
        registration = Request(
            root + "/oauth/register",
            data=json.dumps({"redirect_uris": [STABLE_REDIRECT], "grant_types": ["authorization_code", "refresh_token"]}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(registration) as response:
            client_id = json.load(response)["client_id"]
        verifier = "m6FjZYXBh2kA3-4.wSTed8h0EgzXfK9rR1tYUQwP6Dc"
        state = "chatgpt-oauth-state"
        authorize_url = root + "/oauth/authorize?" + urlencode({
            "client_id": client_id, "redirect_uri": STABLE_REDIRECT, "response_type": "code",
            "state": state, "code_challenge": _challenge(verifier), "code_challenge_method": "S256",
            "scope": SCOPE, "resource": RESOURCE,
        })
        authorize = Request(authorize_url, headers={"X-Riverview-OAuth-Proxy-Key": "test-caddy-proxy-key"})
        with urlopen(authorize) as response:
            page = response.read().decode()
            cookie_header_value = response.headers["Set-Cookie"]
            transaction_cookie = response.headers["Set-Cookie"].split(";", 1)[0]
            csp = response.headers["Content-Security-Policy"]
        assert f'action="{ISSUER}/oauth/authorize"' in page
        assert csp == (
            "default-src 'none'; form-action https://riverview-comms.ionoge.com https://chatgpt.com; "
            "base-uri 'none'; frame-ancestors 'none'"
        )
        assert "*" not in csp
        assert "Path=/oauth/authorize" in cookie_header_value
        assert "Max-Age=600" in cookie_header_value
        assert "Secure" in cookie_header_value
        assert "HttpOnly" in cookie_header_value
        assert "SameSite=None" in cookie_header_value
        csrf_match = re.search(r'name="csrf" value="([A-Za-z0-9_-]+)"', page)
        assert csrf_match is not None
        login = Request(
            root + "/oauth/authorize",
            data=urlencode({"csrf": csrf_match.group(1), "credential": STEWARD_CREDENTIAL}).encode(),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": transaction_cookie,
                "X-Riverview-OAuth-Proxy-Key": "test-caddy-proxy-key",
                "Origin": "https://chatgpt.com",
            },
        )
        with pytest.raises(HTTPError) as redirect:
            opener.open(login)
        assert redirect.value.code == 302
        assert redirect.value.headers["Location"].startswith(
            "https://chatgpt.com/connector_platform_oauth_redirect?"
        )
        callback = parse_qs(urlsplit(redirect.value.headers["Location"]).query)
        assert urlsplit(redirect.value.headers["Location"]).netloc == "chatgpt.com"
        assert urlsplit(redirect.value.headers["Location"]).path == "/connector_platform_oauth_redirect"
        assert callback["state"] == [state]
        assert callback["iss"] == [ISSUER]
        token_request = Request(
            root + "/oauth/token",
            data=urlencode({
                "grant_type": "authorization_code", "client_id": client_id,
                "code": callback["code"][0], "redirect_uri": STABLE_REDIRECT,
                "code_verifier": verifier, "resource": RESOURCE,
            }).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(token_request) as response:
            access_token = json.load(response)["access_token"]
        verified = Request(root + "/oauth/verify", data=b"", headers={"Authorization": "Bearer " + access_token})
        with urlopen(verified) as response:
            assert response.headers["X-Riverview-Comms5-Principal"] == "steward"

        captured = capsys.readouterr().out
        diagnostic = next(line for line in captured.splitlines() if "authorization_fields" in line)
        assert diagnostic == (
            "comms5-oauth authorization_fields transaction_present=True csrf_present=True "
            "expected_credential_present=True transaction_cookie_parsed=True"
        )
        assert STEWARD_CREDENTIAL not in captured
        assert transaction_cookie.split("=", 1)[1] not in captured
        assert csrf_match.group(1) not in captured

        direct_authorize = Request(authorize_url)
        with pytest.raises(HTTPError) as denied:
            urlopen(direct_authorize)
        assert denied.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_authorization_missing_transaction_and_csrf_are_diagnosed_without_values(
    tmp_path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("RIVERVIEW_COMMS5_CLIENT_SECRET", STEWARD_CREDENTIAL)
    monkeypatch.setenv("RIVERVIEW_COMMS5_OAUTH_PROXY_KEY", "test-caddy-proxy-key")
    service = OAuthService(OAuthConfig(ISSUER, RESOURCE, str(tmp_path / "oauth.sqlite3")))
    client = service.register_client({"redirect_uris": [STABLE_REDIRECT]})
    verifier = "m6FjZYXBh2kA3-4.wSTed8h0EgzXfK9rR1tYUQwP6Dc"
    transaction, csrf, _ = service.begin_authorization({
        "client_id": client["client_id"], "redirect_uri": STABLE_REDIRECT,
        "response_type": "code", "state": "diagnostic-state",
        "code_challenge": _challenge(verifier), "code_challenge_method": "S256",
        "scope": SCOPE, "resource": RESOURCE,
    })
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(service))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    class CaptureRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    try:
        root = f"http://127.0.0.1:{server.server_port}"
        opener = build_opener(CaptureRedirect)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Riverview-OAuth-Proxy-Key": "test-caddy-proxy-key",
        }
        missing_transaction = Request(
            root + "/oauth/authorize", data=urlencode({"csrf": csrf}).encode(), headers=headers
        )
        with pytest.raises(HTTPError) as no_cookie:
            urlopen(missing_transaction)
        assert no_cookie.value.code == 503

        cookie_header = {**headers, "Cookie": f"{COOKIE_NAME}={transaction}"}
        missing_csrf = Request(
            root + "/oauth/authorize", data=urlencode({}).encode(), headers=cookie_header
        )
        with pytest.raises(HTTPError) as no_csrf:
            urlopen(missing_csrf)
        assert no_csrf.value.code == 503

        successful = Request(
            root + "/oauth/authorize",
            data=urlencode({"csrf": csrf, "credential": STEWARD_CREDENTIAL}).encode(),
            headers=cookie_header,
        )
        with pytest.raises(HTTPError) as completed:
            opener.open(successful)
        assert completed.value.code == 302

        lines = [line for line in capsys.readouterr().out.splitlines() if "authorization_fields" in line]
        assert lines == [
            (
                "comms5-oauth authorization_fields transaction_present=False csrf_present=True "
                "expected_credential_present=True transaction_cookie_parsed=False"
            ),
            (
                "comms5-oauth authorization_fields transaction_present=True csrf_present=False "
                "expected_credential_present=True transaction_cookie_parsed=True"
            ),
            (
                "comms5-oauth authorization_fields transaction_present=True csrf_present=True "
                "expected_credential_present=True transaction_cookie_parsed=True"
            ),
        ]
        output = "\n".join(lines)
        assert transaction not in output
        assert csrf not in output
        assert STEWARD_CREDENTIAL not in output
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
