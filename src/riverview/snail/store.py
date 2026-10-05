from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class DurableStore:
    """Atomic state/checkpoints plus an append-only, hash-chained flight recorder."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.evidence = self.root / "evidence"
        self.checkpoints = self.root / "checkpoints"
        self.snapshots = self.root / "snapshots"
        for path in (self.root, self.evidence, self.checkpoints, self.snapshots):
            path.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "state.json"
        self.events_path = self.root / "events.jsonl"

    @staticmethod
    def _write_json(path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def save_state(self, state: dict[str, Any]) -> None:
        self._write_json(self.state_path, state)

    def events(self) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        return [json.loads(line) for line in self.events_path.read_text(encoding="utf-8").splitlines() if line]

    def append_event(self, record: dict[str, Any]) -> dict[str, Any]:
        previous = self.events()[-1]["hash"] if self.events_path.exists() and self.events_path.stat().st_size else "GENESIS"
        body = {"event_id": f"EV-{len(self.events()) + 1:08d}", "timestamp": utcnow(), "previous_hash": previous, **record}
        encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        body["hash"] = hashlib.sha256(encoded).hexdigest()
        with self.events_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(body, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return body

    def verify_events(self) -> bool:
        previous = "GENESIS"
        for event in self.events():
            digest = event.pop("hash", None)
            if event.get("previous_hash") != previous:
                return False
            actual = hashlib.sha256(json.dumps(event, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if digest != actual:
                return False
            previous = digest
        return True

    def checkpoint(self, state: dict[str, Any]) -> Path:
        state["checkpoint_time"] = utcnow()
        self.save_state(state)
        path = self.checkpoints / f"{state['campaign_id']}-{state['event_sequence']:08d}.json"
        self._write_json(path, state)
        return path

    def preserve(self, source: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        data = source.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        evidence_id = f"EVD-{digest[:16]}"
        target = self.evidence / f"{evidence_id}{source.suffix.lower()}"
        if not target.exists():
            shutil.copyfile(source, target)
        record = {"evidence_id": evidence_id, "class": "OBSERVED", "sha256": digest, "captured_at": utcnow(), "source": str(source), "file": target.name, **metadata}
        self._write_json(self.evidence / f"{evidence_id}.json", record)
        return record
