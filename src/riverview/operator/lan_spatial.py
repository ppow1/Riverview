"""LAN-only HTTPS read-only spatial prototype listener."""

from __future__ import annotations

import ipaddress
import json
import os
import ssl
import time
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from riverview.spatial.prototype import (
    SPATIAL_BUILD_ID,
    SPATIAL_DEPLOYMENT_TIMESTAMP,
    SPATIAL_DEPLOYMENT_TOKEN,
    SPATIAL_SOURCE_REVISION,
    prototype_html,
)


def _spatial_model_asset() -> Path:
    return Path(__file__).parents[1] / "spatial" / "assets" / "evelyn-test.glb"


_XR_LOGS: deque[dict[str, object]] = deque(maxlen=200)


def _certificate(cert_dir: Path, host: str) -> tuple[Path, Path]:
    cert_dir.mkdir(parents=True, exist_ok=True)
    cert_path, key_path = cert_dir / "spatial.crt.pem", cert_dir / "spatial.key.pem"
    if cert_path.exists() and key_path.exists():
        return cert_path, key_path
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host)])
    san = [x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address(host))]
    cert = x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(__import__("datetime").datetime.now(__import__("datetime").UTC)).not_valid_after(__import__("datetime").datetime.now(__import__("datetime").UTC) + __import__("datetime").timedelta(days=30)).add_extension(x509.SubjectAlternativeName(san), critical=False).sign(key, hashes.SHA256())
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return cert_path, key_path


def build_server(*, host: str = "192.168.1.88", port: int = 18443, cert_dir: Path = Path(r"A:\Riverview\runtime\operator\tls")) -> ThreadingHTTPServer:
    if ipaddress.ip_address(host).is_loopback:
        raise ValueError("RIV-UI-0018: LAN spatial listener must not silently bind loopback.")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            cache_control = "no-store"
            if self.path == "/health":
                body = b'{"status":"healthy","surface":"read-only-spatial"}'
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json")
            elif self.path == "/spatial":
                body = prototype_html().encode()
                cache_control = "no-store, no-cache, must-revalidate, max-age=0"
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
            elif self.path == "/spatial-build":
                body = json.dumps({
                    "build_id": SPATIAL_BUILD_ID,
                    "deployment_timestamp": SPATIAL_DEPLOYMENT_TIMESTAMP,
                    "deployment_token": SPATIAL_DEPLOYMENT_TOKEN,
                    "source_revision": SPATIAL_SOURCE_REVISION,
                    "process_id": os.getpid(),
                    "working_directory": str(Path.cwd()),
                }, sort_keys=True).encode()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json; charset=utf-8")
            elif self.path == "/spatial-xr-log":
                body = json.dumps(list(_XR_LOGS), sort_keys=True).encode()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json; charset=utf-8")
            elif self.path == "/spatial-assets/evelyn-test.glb":
                asset = _spatial_model_asset()
                if not asset.is_file():
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                body = asset.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "model/gltf-binary")
            else:
                body = b'{"error":"not_found"}'
                self.send_response(HTTPStatus.NOT_FOUND)
                self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", cache_control)
            if self.path == "/spatial":
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            if self.path != "/spatial-xr-log":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                length = min(int(self.headers.get("Content-Length", "0")), 8192)
                event = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(event, dict):
                    raise ValueError("event must be an object")
                event["server_received_at"] = time.time()
                event["server_process_id"] = os.getpid()
                _XR_LOGS.append(event)
                self.send_response(HTTPStatus.NO_CONTENT)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
            except (ValueError, TypeError, json.JSONDecodeError):
                self.send_error(HTTPStatus.BAD_REQUEST)

        def log_message(self, *_args: object) -> None:
            return

    server = ThreadingHTTPServer((host, port), Handler)
    cert_path, key_path = _certificate(cert_dir, host)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    return server
