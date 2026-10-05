from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .coordinator import SnailCoordinator
from .runtime import SnailRuntime


def serve(
    runtime: SnailRuntime,
    host: str,
    port: int,
    latest_frame: Path,
    coordinator: SnailCoordinator | None = None,
) -> None:
    build_server(runtime, host, port, latest_frame, coordinator).serve_forever()


def build_server(
    runtime: SnailRuntime,
    host: str,
    port: int,
    latest_frame: Path,
    coordinator: SnailCoordinator | None = None,
) -> ThreadingHTTPServer:
    dashboard = Path(__file__).with_name("static") / "index.html"

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/status":
                payload = runtime.state
                payload["recent_events"] = runtime.store.events()[-30:]
                payload["frame"] = runtime.frame_status(latest_frame)
                payload["infrastructure"] = payload.get("last_observation", {}).get("infrastructure", {})
                payload["coordinator_running"] = coordinator is not None
                self._send(200, json.dumps(payload, indent=2).encode(), "application/json")
                return
            if path == "/api/frame":
                status = runtime.frame_status(latest_frame)
                if not status["available"]:
                    self._send(404, b"frame unavailable", "text/plain")
                    return
                self._send(200, latest_frame.read_bytes(), mimetypes.guess_type(latest_frame.name)[0] or "image/jpeg")
                return
            if path == "/":
                self._send(200, dashboard.read_bytes(), "text/html; charset=utf-8")
                return
            self._send(404, b"not found", "text/plain")

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/api/control":
                self._send(404, b"not found", "text/plain")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                request = json.loads(self.rfile.read(length) or b"{}")
                control = runtime.store.enqueue_control(request["command"], request.get("value"))
                if coordinator:
                    coordinator.wake()
                self._send(202, json.dumps(control).encode(), "application/json")
            except (KeyError, ValueError, json.JSONDecodeError) as exc:
                self._send(400, json.dumps({"error": str(exc)}).encode(), "application/json")

        def log_message(self, _format: str, *_args: object) -> None:
            return

    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8785)
    parser.add_argument("--latest-frame", type=Path)
    args = parser.parse_args()
    runtime = SnailRuntime(args.runtime)
    runtime.start()
    serve(runtime, args.host, args.port, args.latest_frame or args.runtime / "video1" / "latest.jpg")


if __name__ == "__main__":
    main()
