"""LAN-only HTTPS read-only spatial prototype listener."""

from __future__ import annotations

import ipaddress
import ssl
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from riverview.spatial.prototype import prototype_html


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
            if self.path == "/health":
                body = b'{"status":"healthy","surface":"read-only-spatial"}'
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json")
            elif self.path == "/spatial":
                body = prototype_html().encode()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
            else:
                body = b'{"error":"not_found"}'
                self.send_response(HTTPStatus.NOT_FOUND)
                self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args: object) -> None:
            return

    server = ThreadingHTTPServer((host, port), Handler)
    cert_path, key_path = _certificate(cert_dir, host)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    return server
