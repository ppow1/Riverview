"""Small OAuth authorization server for the existing Comms5 Steward identity.

The browser login proves possession of the existing Caddy-held Comms5
connector credential. The OAuth service never stores or logs that credential;
Caddy supplies it only as a loopback request header. Issued opaque tokens are
scoped to the existing Comms5 surface and are checked by Caddy before the
existing Comms5 Steward attestation is injected.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import os
import re
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit

SCOPE = "comms5"
AUTHORIZATION_CODE_TTL = 180
AUTH_TRANSACTION_TTL = 600
ACCESS_TOKEN_TTL = 3600
REFRESH_TOKEN_TTL = 30 * 24 * 3600
MAX_REQUEST_BYTES = 65536
_B64URL_SHA256 = re.compile(r"^[A-Za-z0-9_-]{43}$")
_PKCE_VERIFIER = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")
_CHATGPT_REDIRECT = re.compile(r"^https://chatgpt\.com/connector/oauth/[A-Za-z0-9_-]+$")


class OAuthError(ValueError):
    """Bounded OAuth protocol error safe to return to the client."""

    def __init__(self, error: str, description: str = "OAuth request rejected.", status: int = 400, *, redirect_url: str | None = None):
        super().__init__(description)
        self.error = error
        self.description = description
        self.status = status
        self.redirect_url = redirect_url


@dataclass(frozen=True)
class OAuthConfig:
    issuer: str
    resource: str
    database_path: str
    stable_redirect_uri: str = "https://chatgpt.com/connector_platform_oauth_redirect"

    def __post_init__(self) -> None:
        for label, value in (("issuer", self.issuer), ("resource", self.resource)):
            parsed = urlsplit(value)
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
                raise ValueError(f"RIV-COMMS5-OAUTH-0001: {label} must be an absolute HTTPS URL.")
            if parsed.fragment:
                raise ValueError(f"RIV-COMMS5-OAUTH-0001: {label} cannot contain a fragment.")
        if self.issuer.endswith("/"):
            raise ValueError("RIV-COMMS5-OAUTH-0001: issuer must use its canonical no-trailing-slash form.")
        if self.stable_redirect_uri != "https://chatgpt.com/connector_platform_oauth_redirect":
            raise ValueError("RIV-COMMS5-OAUTH-0001: unsupported ChatGPT redirect URI.")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _random_token(nbytes: int = 32) -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(nbytes)).rstrip(b"=").decode("ascii")


def _pkce_s256(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")


def _valid_redirect(uri: str, stable_uri: str) -> bool:
    parsed = urlsplit(uri)
    if uri == stable_uri:
        return True
    return bool(
        _CHATGPT_REDIRECT.fullmatch(uri)
        and parsed.query == ""
        and parsed.fragment == ""
        and parsed.username is None
        and parsed.password is None
    )


class OAuthService:
    """Provider-neutral OAuth 2.1 subset needed by the ChatGPT MCP client."""

    def __init__(self, config: OAuthConfig):
        self.config = config
        if config.database_path != ":memory:":
            path = Path(config.database_path)
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            try:
                os.chmod(path.parent, 0o700)
            except OSError:
                pass
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.config.database_path, timeout=5, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS oauth_clients (
                    client_id TEXT PRIMARY KEY,
                    client_name TEXT NOT NULL,
                    redirect_uris_json TEXT NOT NULL,
                    grant_types_json TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS oauth_transactions (
                    transaction_hash TEXT PRIMARY KEY,
                    csrf_hash TEXT NOT NULL,
                    client_id TEXT NOT NULL REFERENCES oauth_clients(client_id),
                    redirect_uri TEXT NOT NULL,
                    response_state TEXT NOT NULL,
                    code_challenge TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS oauth_codes (
                    code_hash TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL REFERENCES oauth_clients(client_id),
                    redirect_uri TEXT NOT NULL,
                    code_challenge TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    consumed_at INTEGER
                );
                CREATE TABLE IF NOT EXISTS oauth_tokens (
                    token_hash TEXT PRIMARY KEY,
                    token_type TEXT NOT NULL CHECK(token_type IN ('access', 'refresh')),
                    family_id TEXT NOT NULL,
                    client_id TEXT NOT NULL REFERENCES oauth_clients(client_id),
                    subject TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    revoked_at INTEGER
                );
                CREATE INDEX IF NOT EXISTS oauth_tokens_family_idx ON oauth_tokens(family_id);
                """
            )
            columns = {row["name"] for row in db.execute("PRAGMA table_info(oauth_clients)")}
            if "grant_types_json" not in columns:
                db.execute("ALTER TABLE oauth_clients ADD COLUMN grant_types_json TEXT NOT NULL DEFAULT '[\"authorization_code\",\"refresh_token\"]'")
            now = int(time.time())
            db.execute("DELETE FROM oauth_transactions WHERE expires_at < ?", (now,))
            db.execute("DELETE FROM oauth_codes WHERE expires_at < ?", (now,))
            db.execute("DELETE FROM oauth_tokens WHERE expires_at < ?", (now,))

    def resource_metadata(self) -> dict[str, Any]:
        return {
            "resource": self.config.resource,
            "authorization_servers": [self.config.issuer],
            "scopes_supported": [SCOPE],
        }

    def authorization_metadata(self) -> dict[str, Any]:
        return {
            "issuer": self.config.issuer,
            "authorization_response_iss_parameter_supported": True,
            "authorization_endpoint": f"{self.config.issuer}/oauth/authorize",
            "token_endpoint": f"{self.config.issuer}/oauth/token",
            "registration_endpoint": f"{self.config.issuer}/oauth/register",
            "revocation_endpoint": f"{self.config.issuer}/oauth/revoke",
            "token_endpoint_auth_methods_supported": ["none"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "response_types_supported": ["code"],
            "code_challenge_methods_supported": ["S256"],
            "scopes_supported": [SCOPE],
            "client_id_metadata_document_supported": False,
        }

    def register_client(self, metadata: dict[str, Any]) -> dict[str, Any]:
        redirect_uris = metadata.get("redirect_uris")
        if not isinstance(redirect_uris, list) or not redirect_uris or len(redirect_uris) > 4:
            raise OAuthError("invalid_client_metadata", "At least one supported redirect URI is required.")
        if any(not isinstance(uri, str) or not _valid_redirect(uri, self.config.stable_redirect_uri) for uri in redirect_uris):
            raise OAuthError("invalid_redirect_uri", "Only the documented ChatGPT OAuth callback is accepted.")
        if metadata.get("token_endpoint_auth_method", "none") != "none":
            raise OAuthError("invalid_client_metadata", "Comms5 supports public clients using PKCE.")
        if metadata.get("response_types", ["code"]) != ["code"]:
            raise OAuthError("invalid_client_metadata", "Only the authorization-code response is supported.")
        requested_grants = metadata.get("grant_types", ["authorization_code", "refresh_token"])
        if not isinstance(requested_grants, list) or any(
            item not in {"authorization_code", "refresh_token"} for item in requested_grants
        ) or "authorization_code" not in requested_grants:
            raise OAuthError("invalid_client_metadata", "Unsupported OAuth grant type.")
        name = metadata.get("client_name") or "ChatGPT MCP connector"
        if not isinstance(name, str) or not name.strip() or len(name) > 160:
            raise OAuthError("invalid_client_metadata", "Client name is invalid.")
        client_id = f"rvcc_{_random_token(24)}"
        with self._connect() as db:
            db.execute(
                "INSERT INTO oauth_clients(client_id, client_name, redirect_uris_json, grant_types_json, created_at) VALUES(?,?,?,?,?)",
                (client_id, name.strip(), json.dumps(redirect_uris), json.dumps(requested_grants), int(time.time())),
            )
        return {
            "client_id": client_id,
            "client_id_issued_at": int(time.time()),
            "client_name": name.strip(),
            "redirect_uris": redirect_uris,
            "grant_types": requested_grants,
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        }

    def _authorization_error(self, params: dict[str, str], error: OAuthError) -> OAuthError:
        client_id = params.get("client_id", "")
        redirect_uri = params.get("redirect_uri", "")
        with self._connect() as db:
            client = db.execute("SELECT redirect_uris_json FROM oauth_clients WHERE client_id=?", (client_id,)).fetchone()
        if client and redirect_uri in json.loads(client["redirect_uris_json"]):
            values = {"error": error.error, "error_description": error.description, "iss": self.config.issuer}
            state = params.get("state", "")
            if state and len(state) <= 512:
                values["state"] = state
            error.redirect_url = redirect_uri + "?" + urlencode(values)
        return error

    def begin_authorization(self, params: dict[str, str]) -> tuple[str, str, str]:
        client_id = params.get("client_id", "")
        redirect_uri = params.get("redirect_uri", "")
        response_state = params.get("state", "")
        challenge = params.get("code_challenge", "")
        scope = params.get("scope", SCOPE)
        resource = params.get("resource", "")
        with self._connect() as db:
            client = db.execute("SELECT redirect_uris_json FROM oauth_clients WHERE client_id=?", (client_id,)).fetchone()
        if client is None or redirect_uri not in json.loads(client["redirect_uris_json"]):
            raise OAuthError("invalid_client", "Client or redirect URI is not registered.")
        if params.get("response_type") != "code" or params.get("code_challenge_method") != "S256":
            raise self._authorization_error(params, OAuthError("invalid_request", "Authorization code with PKCE S256 is required."))
        if not response_state or len(response_state) > 512 or not _B64URL_SHA256.fullmatch(challenge):
            raise self._authorization_error(params, OAuthError("invalid_request", "OAuth state or PKCE challenge is invalid."))
        if scope != SCOPE or resource != self.config.resource:
            raise self._authorization_error(params, OAuthError("invalid_scope", "The Comms5 resource and scope must be requested exactly."))
        transaction = _random_token(32)
        csrf = _random_token(24)
        with self._connect() as db:
            db.execute(
                "INSERT INTO oauth_transactions(transaction_hash,csrf_hash,client_id,redirect_uri,response_state,code_challenge,scope,resource,expires_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (_digest(transaction), _digest(csrf), client_id, redirect_uri, response_state, challenge, scope, resource, int(time.time()) + AUTH_TRANSACTION_TTL),
            )
        form = (
            "<!doctype html><html><head><meta charset=\"utf-8\"><title>Riverview Comms5 authorization</title></head>"
            "<body><main><h1>Connect Riverview Comms5</h1>"
            "<p>Enter the existing Steward-controlled Comms5 connector credential to authorize this connection.</p>"
            "<form method=\"post\" action=\"/oauth/authorize\">"
            f"<input type=\"hidden\" name=\"csrf\" value=\"{html.escape(csrf, quote=True)}\">"
            "<label for=\"credential\">Steward credential</label>"
            "<input id=\"credential\" name=\"credential\" type=\"password\" autocomplete=\"current-password\" required>"
            "<button type=\"submit\">Authorize ChatGPT for Comms5</button></form></main></body></html>"
        )
        return transaction, csrf, form

    def complete_authorization(
        self,
        transaction: str,
        csrf: str,
        credential: str,
        expected_credential: str,
    ) -> tuple[str, dict[str, str]]:
        if not transaction or not csrf or not expected_credential:
            raise OAuthError("server_error", "OAuth login is not configured.", 503)
        now = int(time.time())
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM oauth_transactions WHERE transaction_hash=?", (_digest(transaction),)).fetchone()
            if row is None or row["expires_at"] < now:
                db.rollback()
                raise OAuthError("invalid_request", "Authorization form expired; restart the connection.")
            if not hmac.compare_digest(row["csrf_hash"], _digest(csrf)):
                db.rollback()
                raise OAuthError("invalid_request", "Authorization form validation failed.")
            if not hmac.compare_digest(expected_credential, credential):
                attempts = int(row["attempts"]) + 1
                if attempts >= 5:
                    db.execute("DELETE FROM oauth_transactions WHERE transaction_hash=?", (_digest(transaction),))
                else:
                    db.execute("UPDATE oauth_transactions SET attempts=? WHERE transaction_hash=?", (attempts, _digest(transaction)))
                db.commit()
                raise OAuthError("access_denied", "Steward credential was not accepted.", 401)
            db.execute("DELETE FROM oauth_transactions WHERE transaction_hash=?", (_digest(transaction),))
            code = _random_token(32)
            db.execute(
                "INSERT INTO oauth_codes(code_hash,client_id,redirect_uri,code_challenge,scope,resource,expires_at) VALUES(?,?,?,?,?,?,?)",
                (_digest(code), row["client_id"], row["redirect_uri"], row["code_challenge"], row["scope"], row["resource"], now + AUTHORIZATION_CODE_TTL),
            )
            db.commit()
        redirect = row["redirect_uri"] + "?" + urlencode({"code": code, "state": row["response_state"], "iss": self.config.issuer})
        headers = {"Location": redirect}
        return redirect, headers

    def exchange_token(self, form: dict[str, str]) -> dict[str, Any]:
        if form.get("client_secret") or form.get("client_assertion"):
            raise OAuthError("invalid_client", "Comms5 uses a public PKCE client.", 401)
        grant_type = form.get("grant_type", "")
        now = int(time.time())
        if grant_type == "authorization_code":
            code = form.get("code", "")
            client_id = form.get("client_id", "")
            redirect_uri = form.get("redirect_uri", "")
            verifier = form.get("code_verifier", "")
            resource = form.get("resource", "")
            if not _PKCE_VERIFIER.fullmatch(verifier):
                raise OAuthError("invalid_grant", "PKCE verifier is invalid.")
            with self._connect() as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    "SELECT c.*, p.grant_types_json FROM oauth_codes c JOIN oauth_clients p USING(client_id) WHERE c.code_hash=?",
                    (_digest(code),),
                ).fetchone()
                valid = bool(
                    row
                    and row["consumed_at"] is None
                    and row["expires_at"] >= now
                    and row["client_id"] == client_id
                    and row["redirect_uri"] == redirect_uri
                    and row["resource"] == resource == self.config.resource
                    and row["scope"] == SCOPE
                    and hmac.compare_digest(row["code_challenge"], _pkce_s256(verifier))
                )
                if not valid:
                    db.rollback()
                    raise OAuthError("invalid_grant", "Authorization code, redirect, resource, or PKCE verifier is invalid.")
                db.execute("UPDATE oauth_codes SET consumed_at=? WHERE code_hash=? AND consumed_at IS NULL", (now, _digest(code)))
                family = _random_token(18)
                access = _random_token(32)
                refresh = _random_token(48)
                grant_types = json.loads(row["grant_types_json"])
                db.execute(
                    "INSERT INTO oauth_tokens(token_hash,token_type,family_id,client_id,subject,scope,resource,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                    (_digest(access), "access", family, client_id, "steward", SCOPE, resource, now + ACCESS_TOKEN_TTL),
                )
                if "refresh_token" in grant_types:
                    db.execute(
                        "INSERT INTO oauth_tokens(token_hash,token_type,family_id,client_id,subject,scope,resource,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                        (_digest(refresh), "refresh", family, client_id, "steward", SCOPE, resource, now + REFRESH_TOKEN_TTL),
                    )
                db.commit()
            result = {"access_token": access, "token_type": "Bearer", "expires_in": ACCESS_TOKEN_TTL, "scope": SCOPE}
            if "refresh_token" in grant_types:
                result["refresh_token"] = refresh
            return result
        if grant_type == "refresh_token":
            refresh = form.get("refresh_token", "")
            client_id = form.get("client_id", "")
            resource = form.get("resource", "")
            with self._connect() as db:
                db.execute("BEGIN IMMEDIATE")
                old = db.execute("SELECT * FROM oauth_tokens WHERE token_hash=?", (_digest(refresh),)).fetchone()
                requested_scope = form.get("scope", old["scope"] if old else "")
                if not (
                    old and old["token_type"] == "refresh" and old["revoked_at"] is None and old["expires_at"] >= now
                    and old["client_id"] == client_id and old["resource"] == resource == self.config.resource
                    and requested_scope == old["scope"] == SCOPE
                    and "refresh_token" in json.loads(db.execute("SELECT grant_types_json FROM oauth_clients WHERE client_id=?", (client_id,)).fetchone()["grant_types_json"])
                ):
                    db.rollback()
                    raise OAuthError("invalid_grant", "Refresh token is invalid, expired, revoked, or out of scope.")
                db.execute("UPDATE oauth_tokens SET revoked_at=? WHERE token_hash=?", (now, _digest(refresh)))
                access, replacement = _random_token(32), _random_token(48)
                db.execute(
                    "INSERT INTO oauth_tokens(token_hash,token_type,family_id,client_id,subject,scope,resource,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                    (_digest(access), "access", old["family_id"], client_id, old["subject"], SCOPE, resource, now + ACCESS_TOKEN_TTL),
                )
                db.execute(
                    "INSERT INTO oauth_tokens(token_hash,token_type,family_id,client_id,subject,scope,resource,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                    (_digest(replacement), "refresh", old["family_id"], client_id, old["subject"], SCOPE, resource, now + REFRESH_TOKEN_TTL),
                )
                db.commit()
            return {"access_token": access, "token_type": "Bearer", "expires_in": ACCESS_TOKEN_TTL, "refresh_token": replacement, "scope": SCOPE}
        raise OAuthError("unsupported_grant_type", "Only authorization_code and refresh_token are supported.")

    def validate_access_token(self, token: str, *, resource: str | None = None) -> str | None:
        if not token or len(token) > 256:
            return None
        with self._connect() as db:
            row = db.execute("SELECT * FROM oauth_tokens WHERE token_hash=?", (_digest(token),)).fetchone()
        if not (
            row and row["token_type"] == "access" and row["revoked_at"] is None
            and row["expires_at"] > int(time.time()) and row["resource"] == (resource or self.config.resource)
            and row["scope"] == SCOPE and row["subject"] == "steward"
        ):
            return None
        return row["subject"]

    def revoke(self, token: str, client_id: str) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT family_id FROM oauth_tokens WHERE token_hash=? AND client_id=?", (_digest(token), client_id)).fetchone()
            if row is not None:
                db.execute("UPDATE oauth_tokens SET revoked_at=? WHERE family_id=? AND revoked_at IS NULL", (int(time.time()), row["family_id"]))
            db.commit()


def parse_oauth_form(raw: bytes, content_type: str) -> dict[str, str]:
    from urllib.parse import parse_qs

    if len(raw) > MAX_REQUEST_BYTES:
        raise OAuthError("invalid_request", "Request body exceeds the configured limit.", 413)
    if content_type.split(";", 1)[0].strip() == "application/json":
        try:
            value = json.loads(raw or b"{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OAuthError("invalid_request", "Invalid JSON request.") from exc
        if not isinstance(value, dict) or any(not isinstance(item, (str, int, float, bool)) for item in value.values()):
            raise OAuthError("invalid_request", "Request must contain scalar fields.")
        return {str(key): str(item) for key, item in value.items()}
    if content_type.split(";", 1)[0].strip() != "application/x-www-form-urlencoded":
        raise OAuthError("invalid_request", "Expected JSON or form-encoded input.", 415)
    try:
        values = parse_qs(raw.decode("utf-8"), keep_blank_values=True, strict_parsing=True)
    except (UnicodeDecodeError, ValueError) as exc:
        raise OAuthError("invalid_request", "Invalid form-encoded request.") from exc
    if any(len(items) != 1 for items in values.values()):
        raise OAuthError("invalid_request", "Duplicate form fields are not accepted.")
    return {key: values[0] for key, values in values.items()}
