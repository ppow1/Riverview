from pathlib import Path

from riverview.doorbell.config import bootstrap_config, load_config

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


def test_bootstrap_writes_riverview_owned_safe_config(tmp_path):
    config_path = tmp_path / "runtime" / "doorbell" / "config" / "doorbell.json"
    result = bootstrap_config("00000000-0000-4000-8000-000000000000", r"C:\\Riverview\\chromium.exe", config_path)
    config = load_config(result)
    assert config.cdp_port == 9225
    assert "theestate" not in str(result).lower()


def test_config_rejects_secret_fields(tmp_path):
    config_path = tmp_path / "doorbell.json"
    config_path.write_text('{"conversation_id":"00000000-0000-4000-8000-000000000000","browser_executable":"C:\\\\x.exe","cdp_port":9225,"adapter_version":"1.0.0","cookie":"secret"}', encoding="utf-8")
    try:
        load_config(config_path)
    except ValueError as error:
        assert "unsupported" in str(error)
    else:
        raise AssertionError("secret configuration field was accepted")
