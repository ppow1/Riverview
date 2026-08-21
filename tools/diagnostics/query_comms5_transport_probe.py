"""Query bounded Comms5 transport evidence by opaque probe ID."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("probe_id")
    parser.add_argument("--events", type=Path, default=Path("runtime/diagnostics/comms5-transport/http-events.jsonl"))
    args = parser.parse_args()
    matches = []
    if args.events.is_file():
        for line in args.events.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("probe_id") == args.probe_id:
                matches.append(event)
    print(json.dumps({"probe_id": args.probe_id, "server_record": bool(matches), "events": matches}, indent=2))


if __name__ == "__main__":
    main()
