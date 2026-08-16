"""Bounded isolated backup/restore drill for classified reference metadata."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    source_reference: str
    restored_reference: str
    classification: str
    content_hash: str
    credential_reference: str
    isolated: bool


def run_isolated_recovery_drill(*, root: Path, source_reference: str, classification: str, content_hash: str, credential_reference: str) -> RecoveryResult:
    if not all(value.strip() for value in (source_reference, classification, content_hash, credential_reference)):
        raise ValueError("RIV-SEC-0006: recovery metadata is incomplete.")
    backup = root / "backup" / "synthetic-reference.json"
    restored = root / "restored" / "synthetic-reference.json"
    record = {"source_reference": source_reference, "classification": classification, "content_hash": content_hash, "credential_reference": credential_reference}
    backup.parent.mkdir(parents=True, exist_ok=True)
    restored.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    restored.write_bytes(backup.read_bytes())
    recovered = json.loads(restored.read_text(encoding="utf-8"))
    if recovered != record or hashlib.sha256(restored.read_bytes()).hexdigest() != hashlib.sha256(backup.read_bytes()).hexdigest():
        raise RuntimeError("RIV-SEC-0006: isolated recovery verification failed.")
    return RecoveryResult(source_reference, f"isolated://{restored.name}", classification, content_hash, credential_reference, True)
