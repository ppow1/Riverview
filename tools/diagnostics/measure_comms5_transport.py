"""Bounded Comms5 transport probe; records timings without request credentials.

Version: 1.0.0

This probe performs MCP initialize calls only. It is intentionally bounded and
does not issue Grace execution or mutation operations.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import ssl
import statistics
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

BODY = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "riverview-comms5-transport-probe", "version": "1.0.0"},
        },
    }
).encode()


def one(endpoint: str, timeout: float, auth: str | None, label: str) -> dict[str, object]:
    request_id = f"transport-{label}-{uuid4()}"
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": "2025-11-25",
        "X-Riverview-Request-ID": request_id,
    }
    if auth:
        headers["Authorization"] = f"Bearer {auth}"
    started = time.perf_counter()
    result: dict[str, object] = {"request_id": request_id, "started_utc": datetime.now(UTC).isoformat()}
    try:
        request = urllib.request.Request(endpoint, data=BODY, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            payload = response.read()
            result.update({"status": response.status, "bytes": len(payload), "content_type": response.headers.get("content-type")})
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        result.update({"status": None, "error": type(exc).__name__})
    result["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
    return result


def run_round(endpoint: str, count: int, parallel: int, timeout: float, auth: str | None, label: str) -> list[dict[str, object]]:
    if parallel <= 1:
        return [one(endpoint, timeout, auth, label) for _ in range(count)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as pool:
        return list(pool.map(lambda _: one(endpoint, timeout, auth, label), range(count)))


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    latencies = [float(row["latency_ms"]) for row in rows]
    successes = [row for row in rows if row.get("status") == 200]
    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered) - 1, max(0, int(len(ordered) * 0.95) - 1))] if ordered else None
    return {
        "count": len(rows),
        "successes": len(successes),
        "failures": len(rows) - len(successes),
        "p50_ms": round(statistics.median(latencies), 3) if latencies else None,
        "p95_ms": p95,
        "max_ms": round(max(latencies), 3) if latencies else None,
        "errors": sorted({str(row["error"]) for row in rows if row.get("error")}),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--auth-env")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.count <= 100:
        raise SystemExit("count must be between 1 and 100")
    if not 1 <= args.parallel <= 24:
        raise SystemExit("parallel must be between 1 and 24")
    auth = os.environ.get(args.auth_env) if args.auth_env else None
    sequential = run_round(args.endpoint, args.count, 1, args.timeout, auth, "sequential")
    parallel = run_round(args.endpoint, min(args.parallel, args.count), args.parallel, args.timeout, auth, "parallel")
    report = {
        "version": "1.0.0",
        "endpoint": args.endpoint,
        "generated_utc": datetime.now(UTC).isoformat(),
        "request_policy": "MCP initialize only; no execution or mutation operations",
        "sequential": {"summary": summarize(sequential), "requests": sequential},
        "parallel": {"summary": summarize(parallel), "requests": parallel},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sequential": report["sequential"]["summary"], "parallel": report["parallel"]["summary"]}))


if __name__ == "__main__":
    main()
