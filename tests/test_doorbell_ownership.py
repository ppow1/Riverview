from pathlib import Path

import pytest

from riverview.doorbell.config import RUNTIME_ROOT, bootstrap_config, load_config

ROOT = Path(__file__).parents[1]
RUNTIME_MODULES = [
    ROOT / "src" / "riverview" / "doorbell",
    ROOT / "tools" / "riverview_doorbell_bridge.cjs",
    ROOT / "tools" / "riverview_browser_runtime.cjs",
]


def test_runtime_has_no_external_estate_path_dependency():
    for target in RUNTIME_MODULES:
        files = [target] if target.is_file() else list(target.rglob("*.py"))
        for file in files:
            source = file.read_text(encoding="utf-8")
            assert "A:\\theestate" not in source
            assert "A:\\theestate-data" not in source


def test_mutable_runtime_root_is_outside_repository():
    assert RUNTIME_ROOT == ROOT.parent / "runtime"
    assert not str(RUNTIME_ROOT).startswith(str(ROOT / "runtime"))


def test_bootstrap_writes_riverview_owned_safe_config(tmp_path):
    config_path = tmp_path / "runtime" / "doorbell" / "config" / "doorbell.json"
    result = bootstrap_config("00000000-0000-4000-8000-000000000000", r"C:\\Riverview\\chromium.exe", config_path)
    config = load_config(result)
    assert config.cdp_port == 9225
    assert "theestate" not in str(result).lower()


def test_chatgpt_identifier_accepts_non_rfc_uuidv4_shape(tmp_path):
    config_path = tmp_path / "doorbell.json"
    bootstrap_config("6a7f910b-1308-83ea-91a3-654e4a7aa4e7", r"C:\\Riverview\\chromium.exe", config_path)
    assert load_config(config_path).conversation_id == "6a7f910b-1308-83ea-91a3-654e4a7aa4e7"


def test_chatgpt_identifier_accepts_case_without_uuid_semantics(tmp_path):
    config_path = tmp_path / "doorbell.json"
    bootstrap_config("ABCDEFAB-CDEF-0123-FEDC-ABCDEFABCDEF", r"C:\\Riverview\\chromium.exe", config_path)
    assert load_config(config_path).conversation_id == "abcdefab-cdef-0123-fedc-abcdefabcdef"


def test_chatgpt_identifier_rejects_url_whitespace_and_malformed_values(tmp_path):
    invalid = [
        "",
        " 6a7f910b-1308-83ea-91a3-654e4a7aa4e7",
        "6a7f910b-1308-83ea-91a3-654e4a7aa4e7 ",
        "https://chatgpt.com/c/6a7f910b-1308-83ea-91a3-654e4a7aa4e7",
        "6a7f910b-1308-83ea-91a3-654e4a7aa4",
        "6a7f910b-1308-83ea-91a3-654e4a7aa4e77",
        "6a7f910b-1308-83ea-91a3-654e4a7aa4eg",
        "6a7f910b-1308-83ea-91a3-654e4a7aa4e7-extra",
    ]
    for index, value in enumerate(invalid):
        with pytest.raises(ValueError, match="ChatGPT conversation identifier"):
            bootstrap_config(value, r"C:\\Riverview\\chromium.exe", tmp_path / f"invalid-{index}.json")


def test_config_rejects_secret_fields(tmp_path):
    config_path = tmp_path / "doorbell.json"
    config_path.write_text('{"conversation_id":"00000000-0000-4000-8000-000000000000","browser_executable":"C:\\\\x.exe","cdp_port":9225,"adapter_version":"1.0.0","cookie":"secret"}', encoding="utf-8")
    try:
        load_config(config_path)
    except ValueError as error:
        assert "unsupported" in str(error)
    else:
        raise AssertionError("secret configuration field was accepted")
