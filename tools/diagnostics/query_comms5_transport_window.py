"""Query bounded Comms5 events by local timestamp window and operation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="ISO-8601 timestamp, inclusive")
    parser.add_argument("--end", required=True, help="ISO-8601 timestamp, exclusive")
    parser.add_argument("--operation", required=True)
    parser.add_argument("--events", type=Path, default=Path("runtime/diagnostics/comms5-transport/http-events.jsonl"))
    args = parser.parse_args()
    start, end = _time(args.start), _time(args.end)
    events = []
    if args.events.is_file():
        for line in args.events.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
                timestamp = _time(str(event["timestamp"]))
            except (KeyError, ValueError, json.JSONDecodeError):
                continue
            if start <= timestamp < end:
                events.append(event)
    operation_events = [event for event in events if event.get("operation") == args.operation]
    request_ids = {event.get("request_id") for event in operation_events}
    joined = [event for event in events if event.get("request_id") in request_ids]
    by_request = []
    for request_id in sorted(request_ids):
        rows = [event for event in joined if event.get("request_id") == request_id]
        names = {event.get("event") for event in rows}
        if "mcp.complete" in names and "http.sent" in names:
            classification = "SERVER_COMPLETED"
        elif "mcp.complete" in names:
            classification = "SERVER_COMPLETED_CLIENT_CANCELED_OR_RETURN_PATH_UNOBSERVED"
        elif "http.received" in names and "mcp.dispatch" not in names:
            classification = "CADDY_RECEIVED_BACKEND_INCOMPLETE"
        elif "db.start" in names and "db.complete" not in names:
            classification = "COMMS5_RECEIVED_DB_INCOMPLETE"
        else:
            classification = "COMMS5_RECEIVED_INCOMPLETE"
        by_request.append({"server_request_id": request_id, "classification": classification, "events": rows})
    print(json.dumps({"operation": args.operation, "start": args.start, "end": args.end, "requests": by_request, "no_server_record": not by_request}, indent=2))


if __name__ == "__main__":
    main()
