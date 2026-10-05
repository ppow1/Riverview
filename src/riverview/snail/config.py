from __future__ import annotations

import json
from pathlib import Path


DEFAULT_CONFIG = Path(__file__).with_name("campaigns") / "octo1_multi_p100.json"


def load_config(path: Path | None = None) -> dict:
    return json.loads((path or DEFAULT_CONFIG).read_text(encoding="utf-8"))
