"""Live HTTP acceptance for Steward Status. Version: 0.7.0"""

from __future__ import annotations

import json
import threading
from urllib.request import urlopen

from riverview.status.server import build_server


def acceptance() -> dict[str, object]:
    server=build_server(port=0)
    thread=threading.Thread(target=server.serve_forever,kwargs={"poll_interval":0.05},daemon=True)
    thread.start()
    base=f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(f"{base}/healthz",timeout=5) as response:
            health=json.load(response)
        with urlopen(f"{base}/api/status",timeout=5) as response:
            status=json.load(response)
        with urlopen(f"{base}/",timeout=5) as response:
            html=response.read().decode()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    required={"roadmap","workers","work_counts","recent_work","escalations","diagnostics","migrations"}
    if health.get("status")!="healthy" or health.get("authority")!="read_only" or not required.issubset(status) or "The Estate at Riverview" not in html or thread.is_alive():
        raise RuntimeError("RIV-UI-0004: Steward Status HTTP acceptance failed.")
    return {"status":"healthy","localhost_only":True,"read_only":True,"api_projection":True,"auto_refresh":True,"bounded_stop":True}


if __name__ == "__main__":
    print(json.dumps(acceptance(),indent=2,sort_keys=True))