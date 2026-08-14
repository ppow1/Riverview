"""Riverview-owned RV-008.3 local runtime configuration."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPOSITORY_ROOT.parent / "runtime"
DOORBELL_ROOT = RUNTIME_ROOT / "doorbell"
CONFIG_PATH = DOORBELL_ROOT / "config" / "doorbell.json"
PROFILE_PATH = RUNTIME_ROOT / "browser" / "profile"
CHATGPT_CONVERSATION_ID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class DoorbellRuntimeConfig:
    conversation_id: str
    browser_executable: Path
    cdp_port: int = 9225
    adapter_version: str = "1.0.0"


def discover_browser_executable() -> Path:
    candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    playwright_root = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"
    candidates.extend(sorted(playwright_root.glob("chromium-*/chrome-win64/chrome.exe"), reverse=True))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise ValueError("RIV-PLY-0013: no supported local Chromium executable was found.")


def load_config(path: Path = CONFIG_PATH) -> DoorbellRuntimeConfig:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("RIV-PLY-0010: Riverview doorbell configuration is unavailable.") from exc
    allowed = {"conversation_id", "browser_executable", "cdp_port", "adapter_version"}
    if set(raw) != allowed:
        raise ValueError("RIV-PLY-0011: configuration contains unsupported or missing fields.")
    conversation_id = str(raw["conversation_id"]).lower()
    executable = Path(str(raw["browser_executable"])).resolve()
    port = raw["cdp_port"]
    if not CHATGPT_CONVERSATION_ID.fullmatch(conversation_id) or not executable.is_absolute():
        raise ValueError("RIV-PLY-0011: configuration target or executable is invalid.")
    if not isinstance(port, int) or not 9225 <= port <= 9325:
        raise ValueError("RIV-PLY-0011: CDP port is outside the Riverview localhost range.")
    if not isinstance(raw["adapter_version"], str) or not raw["adapter_version"].strip():
        raise ValueError("RIV-PLY-0011: adapter version is invalid.")
    return DoorbellRuntimeConfig(conversation_id, executable, port, raw["adapter_version"])


def bootstrap_config(conversation_id: str, browser_executable: str | None = None, path: Path = CONFIG_PATH) -> Path:
    if not CHATGPT_CONVERSATION_ID.fullmatch(conversation_id):
        raise ValueError("RIV-PLY-0011: conversation ID must match the ChatGPT conversation identifier format.")
    executable = (Path(browser_executable).expanduser().resolve()
                  if browser_executable else discover_browser_executable())
    if not executable.is_absolute():
        raise ValueError("RIV-PLY-0011: browser executable must be an absolute local path.")
    path.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.mkdir(parents=True, exist_ok=True)
    payload = {
        "conversation_id": conversation_id.lower(),
        "browser_executable": str(executable),
        "cdp_port": 9225,
        "adapter_version": "1.0.0",
    }
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return path
