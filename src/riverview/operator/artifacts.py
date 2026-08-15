"""Reference-only artifact intake over the RV-013.2 storage contract."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from riverview.knowledge.inventory import ExportRecord, inventory_file


def intake_artifact(path: Path, *, correlation_id: UUID, classification: str) -> ExportRecord:
    if classification not in {"public", "operational", "private", "sensitive"}:
        raise ValueError("RIV-UI-0011: artifact classification is denied.")
    return inventory_file(
        path,
        source_kind="operator-artifact",
        classification=classification,
        provenance={"correlation_id": str(correlation_id), "source": "riverview-operator"},
    )
