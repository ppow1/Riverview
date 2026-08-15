import json
from pathlib import Path
from uuid import uuid4

import pytest

from riverview.knowledge.normalize import normalize_message_export


def test_normalizer_rejects_empty_or_unsupported_exports(tmp_path: Path) -> None:
    source = tmp_path / "messages.json"
    source.write_text(json.dumps([]), encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty"):
        normalize_message_export(source, source_export_id=uuid4())
    source.write_text(json.dumps([{"body": "x"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="classification"):
        normalize_message_export(source, source_export_id=uuid4(), classification="undercurrent")
