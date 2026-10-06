"""Campaign anchor injection for SNAIL review snapshots.

Every external-review snapshot must carry the canonical project requirements and
process map so the campaign objective and operating process travel with the
snapshot rather than depending on conversational memory.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Callable

CAMPAIGN_ANCHORS = ("PROJECT_REQUIREMENTS.md", "PROCESS_MAP.md")


def campaign_docs_root() -> Path:
    """Return the canonical OctoMiner campaign document directory in this checkout."""
    repository = Path(__file__).resolve().parents[3]
    return repository / "docs" / "operations" / "octominer" / "campaign"


def install_snapshot_anchor_wrapper(runtime_class: type) -> None:
    """Wrap ``runtime_class.snapshot`` once so every ZIP includes campaign anchors."""
    original: Callable = runtime_class.snapshot
    if getattr(original, "_campaign_anchors_installed", False):
        return

    def snapshot_with_campaign_anchors(self, reason: str) -> Path:
        target = original(self, reason)
        docs = campaign_docs_root()
        missing = [name for name in CAMPAIGN_ANCHORS if not (docs / name).is_file()]
        if missing:
            raise RuntimeError(f"campaign anchor documents missing: {', '.join(missing)}")
        with zipfile.ZipFile(target, "a", zipfile.ZIP_DEFLATED) as archive:
            for name in CAMPAIGN_ANCHORS:
                archive.write(docs / name, name)
        return target

    snapshot_with_campaign_anchors._campaign_anchors_installed = True  # type: ignore[attr-defined]
    runtime_class.snapshot = snapshot_with_campaign_anchors
