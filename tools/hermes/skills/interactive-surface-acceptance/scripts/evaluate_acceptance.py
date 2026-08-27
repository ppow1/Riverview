#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def severity(sample):
    flags = []
    if sample.get("ack_ms", 0) > 100:
        flags.append("ack-slow")
    if sample.get("shell_ms", 0) > 500:
        flags.append("shell-slow")
    usable = sample.get("usable_ms")
    hydrate = sample.get("hydrate_ms")
    if usable is not None and usable > 2000:
        flags.append("usable-slow")
    if hydrate is not None and hydrate > 2000:
        flags.append("hydrate-slow")
    if usable is not None and usable > 10000:
        flags.append("usable-fail")
    if hydrate is not None and hydrate > 10000:
        flags.append("hydrate-fail")
    return flags


def ratchet(values):
    if len(values) < 4:
        return False
    rises = sum(1 for a, b in zip(values, values[1:]) if b > a)
    growth = values[-1] - values[0]
    base = max(abs(values[0]), 1)
    return rises >= len(values) - 2 and growth / base >= 0.15


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics_json")
    args = ap.parse_args()
    data = json.loads(Path(args.metrics_json).read_text(encoding="utf-8"))

    out = {"sample_count": 0, "latency_flags": [], "cycle_flags": []}
    for s in data.get("samples", []):
        out["sample_count"] += 1
        flags = severity(s)
        if flags:
            out["latency_flags"].append({
                "view": s.get("view"),
                "action": s.get("action"),
                "flags": flags,
            })

    for c in data.get("cycles", []):
        flags = []
        if ratchet(c.get("memory_mb", [])):
            flags.append("memory-ratchet")
        if ratchet(c.get("dom_nodes", [])):
            flags.append("dom-ratchet")
        if flags:
            out["cycle_flags"].append({"name": c.get("name"), "flags": flags})

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
