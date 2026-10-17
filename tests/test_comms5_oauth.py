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
from riverview.mcp.comms5_oauth_server import create_handler
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


def test_real_http_chatgpt_oauth_pkce_browser_exchange(tmp_path, monkeypatch) -> None:
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
            transaction_cookie = response.headers["Set-Cookie"].split(";", 1)[0]
        csrf_match = re.search(r'name="csrf" value="([A-Za-z0-9_-]+)"', page)
        assert csrf_match is not None
        login = Request(
            root + "/oauth/authorize",
            data=urlencode({"csrf": csrf_match.group(1), "credential": STEWARD_CREDENTIAL}).encode(),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": transaction_cookie,
                "X-Riverview-OAuth-Proxy-Key": "test-caddy-proxy-key",
            },
        )
        with pytest.raises(HTTPError) as redirect:
            opener.open(login)
        assert redirect.value.code == 302
        callback = parse_qs(urlsplit(redirect.value.headers["Location"]).query)
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

        direct_authorize = Request(authorize_url)
        with pytest.raises(HTTPError) as denied:
            urlopen(direct_authorize)
        assert denied.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
