"""Foreground entrypoint for the bounded private-LAN spatial listener."""

from __future__ import annotations

from riverview.operator.lan_spatial import build_server


def main() -> None:
    server = build_server()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
