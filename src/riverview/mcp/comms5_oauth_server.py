"""Loopback HTTP frontend for the Comms5 OAuth service."""

from __future__ import annotations

import hmac
import json
import os
import sqlite3
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from riverview.mcp.comms5_oauth import (
    MAX_REQUEST_BYTES,
    OAuthConfig,
    OAuthError,
    OAuthService,
    parse_oauth_form,
)

DEFAULT_ISSUER = "https://riverview-comms.ionoge.com"
DEFAULT_RESOURCE = "https://riverview-comms.ionoge.com/comms5/mcp"
DEFAULT_BIND = "127.0.0.1"
DEFAULT_PORT = 11827
COOKIE_NAME = "rv_comms5_oauth_txn"
PROXY_KEY_HEADER = "X-Riverview-OAuth-Proxy-Key"


def _json_body(raw: bytes) -> dict[str, object]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise OAuthError("invalid_request", "Request body exceeds the configured limit.", 413)
    try:
        value = json.loads(raw or b"{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OAuthError("invalid_client_metadata", "Invalid JSON request.") from exc
    if not isinstance(value, dict):
        raise OAuthError("invalid_client_metadata", "JSON body must be an object.")
    return value


def create_handler(service: OAuthService) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: object) -> None:
            # BaseHTTPRequestHandler formats include requestline/query values.
            # Do not emit those values or untrusted handler arguments.
            return

        def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
            path = urlsplit(self.path).path[:160]
            print(f"comms5-oauth method={self.command} path={path} status={code}", flush=True)

        def _send(self, status: int, body: bytes, content_type: str, headers: dict[str, str] | None = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Pragma", "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            if headers:
                for name, value in headers.items():
                    self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def _trusted_caddy_authorize(self) -> tuple[str, str] | None:
            """Accept the existing credential only on an authenticated proxy hop.

            The listener is loopback-only, but loopback by itself does not
            authenticate local processes. Caddy and this service therefore
            share a separately provisioned proxy key; the Comms5 credential
            remains the user-entered proof and is never trusted from a header.
            """
            expected_proxy_key = os.environ.get("RIVERVIEW_COMMS5_OAUTH_PROXY_KEY", "")
            received_proxy_key = self.headers.get(PROXY_KEY_HEADER, "")
            expected_credential = os.environ.get("RIVERVIEW_COMMS5_CLIENT_SECRET", "")
            if (
                not expected_proxy_key
                or not expected_credential
                or not received_proxy_key
                or not hmac.compare_digest(received_proxy_key, expected_proxy_key)
            ):
                return None
            return expected_credential, received_proxy_key

        def _json(self, status: int, body: dict[str, object], headers: dict[str, str] | None = None) -> None:
            self._send(status, json.dumps(body, separators=(",", ":")).encode(), "application/json", headers)

        def _body(self) -> bytes:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise OAuthError("invalid_request", "Invalid Content-Length.") from exc
            if length < 0 or length > MAX_REQUEST_BYTES:
                raise OAuthError("invalid_request", "Request body exceeds the configured limit.", 413)
            return self.rfile.read(length)

        def _error(self, error: OAuthError, *, authenticate: bool = False) -> None:
            headers = {}
            if authenticate:
                headers["WWW-Authenticate"] = (
                    'Bearer resource_metadata="' + service.config.issuer
                    + '/.well-known/oauth-protected-resource", error="invalid_token", '
                    'error_description="Authenticate with the Steward OAuth connection."'
                )
            self._json(error.status, {"error": error.error, "error_description": error.description}, headers)

        def do_GET(self) -> None:
            parsed = urlsplit(self.path)
            if parsed.path == "/.well-known/oauth-protected-resource":
                self._json(200, service.resource_metadata())
                return
            if parsed.path == "/.well-known/oauth-authorization-server":
                self._json(200, service.authorization_metadata())
                return
            if parsed.path == "/healthz":
                self._json(200, {"status": "ok", "service": "riverview-comms5-oauth"})
                return
            if parsed.path == "/oauth/verify":
                self._verify_mcp_bearer()
                return
            if parsed.path == "/oauth/authorize":
                if self._trusted_caddy_authorize() is None:
                    self._error(OAuthError("access_denied", "Authorization must be completed through the trusted HTTPS ingress.", 403))
                    return
                params = parse_qs(parsed.query, keep_blank_values=True)
                if any(len(values) != 1 for values in params.values()):
                    self._error(OAuthError("invalid_request", "Duplicate authorization parameters."))
                    return
                try:
                    transaction, _, page = service.begin_authorization({key: values[0] for key, values in params.items()})
                except OAuthError as exc:
                    if exc.redirect_url:
                        self._send(302, b"", "text/plain; charset=utf-8", {"Location": exc.redirect_url})
                        return
                    self._error(exc)
                    return
                headers = {
                    "Set-Cookie": f"{COOKIE_NAME}={transaction}; Path=/oauth/authorize; Max-Age=600; Secure; HttpOnly; SameSite=None",
                    "Content-Security-Policy": (
                        "default-src 'none'; form-action "
                        f"{urlsplit(service.config.issuer).scheme}://{urlsplit(service.config.issuer).netloc}; "
                        "base-uri 'none'; frame-ancestors 'none'"
                    ),
                }
                self._send(200, page.encode(), "text/html; charset=utf-8", headers)
                return
            self._json(404, {"error": "not_found"})

        def _verify_mcp_bearer(self) -> None:
            # Caddy's forward_auth invokes this loopback-only route. The public
            # Caddy matchers intentionally do not expose it.
            authorization = self.headers.get("Authorization", "")
            scheme, _, token = authorization.partition(" ")
            principal = service.validate_access_token(token, resource=service.config.resource) if scheme.lower() == "bearer" else None
            if principal is None:
                self._error(OAuthError("invalid_token", "A valid Comms5 access token is required.", 401), authenticate=True)
                return
            self._send(200, b"", "application/json", {"X-Riverview-Comms5-Principal": principal})

        def do_DELETE(self) -> None:
            if urlsplit(self.path).path == "/oauth/verify":
                self._verify_mcp_bearer()
                return
            self._json(404, {"error": "not_found"})

        def do_OPTIONS(self) -> None:
            if urlsplit(self.path).path == "/oauth/verify":
                self._verify_mcp_bearer()
                return
            self._json(404, {"error": "not_found"})

        def do_POST(self) -> None:
            path = urlsplit(self.path).path
            try:
                raw = self._body()
                content_type = self.headers.get("Content-Type", "")
                if path == "/oauth/register":
                    result = service.register_client(_json_body(raw))
                    self._json(201, result)
                    return
                if path == "/oauth/authorize":
                    trusted = self._trusted_caddy_authorize()
                    if trusted is None:
                        self._error(OAuthError("access_denied", "Authorization must be completed through the trusted HTTPS ingress.", 403))
                        return
                    form = parse_oauth_form(raw, content_type)
                    cookie = SimpleCookie(self.headers.get("Cookie", ""))
                    transaction_cookie = cookie.get(COOKIE_NAME)
                    transaction_cookie_parsed = transaction_cookie is not None
                    transaction = transaction_cookie.value if transaction_cookie_parsed else ""
                    expected, _ = trusted
                    csrf = form.get("csrf", "")
                    print(
                        "comms5-oauth authorization_fields "
                        f"transaction_present={bool(transaction)} "
                        f"csrf_present={bool(csrf)} "
                        f"expected_credential_present={bool(expected)} "
                        f"transaction_cookie_parsed={transaction_cookie_parsed}",
                        flush=True,
                    )
                    try:
                        location, _ = service.complete_authorization(
                            transaction, csrf, form.get("credential", ""), expected
                        )
                    except OAuthError as exc:
                        page = (
                            "<!doctype html><html><head><meta charset=\"utf-8\"><title>Authorization not completed</title></head>"
                            "<body><main><h1>Authorization not completed</h1><p>"
                            + exc.description
                            + "</p><p>Return to ChatGPT and retry the connection.</p></main></body></html>"
                        )
                        self._send(exc.status, page.encode(), "text/html; charset=utf-8", {
                            "Content-Security-Policy": "default-src 'none'; base-uri 'none'; frame-ancestors 'none'",
                            "Set-Cookie": f"{COOKIE_NAME}=; Path=/oauth/authorize; Max-Age=0; Secure; HttpOnly; SameSite=Lax",
                        })
                        return
                    self._send(302, b"", "text/plain; charset=utf-8", {
                        "Location": location,
                        "Set-Cookie": f"{COOKIE_NAME}=; Path=/oauth/authorize; Max-Age=0; Secure; HttpOnly; SameSite=Lax",
                    })
                    return
                if path == "/oauth/token":
                    form = parse_oauth_form(raw, content_type)
                    self._json(200, service.exchange_token(form))
                    return
                if path == "/oauth/revoke":
                    form = parse_oauth_form(raw, content_type)
                    service.revoke(form.get("token", ""), form.get("client_id", ""))
                    self._send(200, b"", "application/json")
                    return
                if path == "/oauth/verify":
                    # Caddy's forward_auth uses this loopback-only route. The
                    # public Caddy matcher intentionally does not expose it.
                    self._verify_mcp_bearer()
                    return
                self._json(404, {"error": "not_found"})
            except OAuthError as exc:
                self._error(exc)
            except sqlite3.Error as exc:  # pragma: no cover - platform database failure
                print(f"comms5-oauth database_error={type(exc).__name__}", flush=True)
                self._error(OAuthError("server_error", "OAuth persistence is unavailable.", 503))
            except (ValueError, TypeError, KeyError, OverflowError, OSError, UnicodeError) as exc:  # pragma: no cover - malformed request boundary
                print(f"comms5-oauth request_error={type(exc).__name__}", flush=True)
                self._error(OAuthError("server_error", "OAuth request failed.", 500))

    return Handler


def main() -> None:
    host = os.environ.get("RIVERVIEW_COMMS5_OAUTH_HOST", DEFAULT_BIND)
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("RIV-COMMS5-OAUTH-0002: OAuth listener must bind exclusively to loopback.")
    try:
        port = int(os.environ.get("RIVERVIEW_COMMS5_OAUTH_PORT", str(DEFAULT_PORT)))
    except ValueError as exc:
        raise SystemExit("RIV-COMMS5-OAUTH-0003: OAuth port must be numeric.") from exc
    if not 1 <= port <= 65535:
        raise SystemExit("RIV-COMMS5-OAUTH-0003: OAuth port is outside the valid range.")
    config = OAuthConfig(
        issuer=os.environ.get("RIVERVIEW_COMMS5_OAUTH_ISSUER", DEFAULT_ISSUER),
        resource=os.environ.get("RIVERVIEW_COMMS5_OAUTH_RESOURCE", DEFAULT_RESOURCE),
        database_path=os.environ.get("RIVERVIEW_COMMS5_OAUTH_DATABASE", "/var/lib/riverview-comms5-oauth/oauth.sqlite3"),
    )
    service = OAuthService(config)
    server = ThreadingHTTPServer((host, port), create_handler(service))
    server.daemon_threads = True
    print(f"comms5-oauth started host={host} port={port} issuer={config.issuer}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
