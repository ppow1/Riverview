from pathlib import Path

import pytest

from riverview.knowledge import inventory_file


def test_inventory_hashes_source_without_embedding_payload(tmp_path: Path) -> None:
    source = tmp_path / "export.json"
    source.write_text('{"bounded":true}', encoding="utf-8")
    record = inventory_file(source, source_kind="json-export", classification="operational", provenance={"source": "test"})
    assert len(record.content_sha256) == 64
    assert record.byte_size == source.stat().st_size


def test_inventory_rejects_unknown_classification(tmp_path: Path) -> None:
    source = tmp_path / "export.json"
    source.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="classification"):
        inventory_file(source, source_kind="json-export", classification="unknown", provenance={})
