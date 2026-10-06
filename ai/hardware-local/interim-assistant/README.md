# Interim Local Assistant — Preservation / Restart Package

**Status:** Paused / preserved 2026-10-06  
**Original local root:** `A:\AI\Assistant`  
**Host:** `DESKTOP-JA3RPNQ`  
**Primary model:** `qwen3:8b` through local Ollama  
**Web port:** `8765`

## Why this exists

This directory preserves the small Windows local assistant that was built as an interim tool while larger Riverview/Grace/Hermes work was unavailable or unreliable. The goal is to preserve the exact working code, state, history, and restart information so future work does not begin from zero.

This is distinct from the earlier **HermesVisionGateway / Qwen3-Next-80B multimodal gateway** work. That older gateway routed Hermes traffic and used an OctoMiner-hosted large model plus local vision. The interim assistant here is a much smaller standalone Python web application backed by local Ollama `qwen3:8b`.

## What was actually present on disk

The forensic collection taken 2026-10-06 found seven project files under `A:\AI\Assistant`:

- `assistant.py` — current/latest application.
- `assistant-v02-20260930-132727.py` — earlier source snapshot.
- `start-assistant.ps1` — starts the server hidden if port 8765 is not already listening.
- `data/state.json` — current persistent state.
- `data/state-v02-20260930-132727.json` — state snapshot.
- `data/state-20260930-131952.json` — earlier state snapshot.
- `data/assistant.log` — interaction/activity log from the working test period.

No virtual environment, package manifest, database, or separate front-end source tree was present. The HTML/CSS/JavaScript phone/dashboard interface is embedded directly in `assistant.py`.

## Architecture

```text
Phone / desktop browser
        |
        | HTTP to dev machine :8765
        v
A:\AI\Assistant\assistant.py
        |
        +-- deterministic command parser
        |     - Today
        |     - Waiting
        |     - Capture
        |     - Completed Today
        |
        +-- persistent JSON state
        |     A:\AI\Assistant\data\state.json
        |
        +-- append-only activity log
        |     A:\AI\Assistant\data\assistant.log
        |
        +-- fallback/general language requests
              Ollama native chat API
              http://127.0.0.1:11434/api/chat
              model: qwen3:8b
```

The Python server binds to `0.0.0.0:8765`, making the dashboard reachable from another device on the LAN when Windows networking/firewall permits it.

## Confirmed features

The latest source contains deterministic commands before falling back to Qwen: add to Today, move the last Capture to Today, add to Waiting, complete numbered Today items, report completed-today items, and show Today. It also contains a capture endpoint, dashboard rendering for Today/Waiting/Money/recent Capture, and Ollama fallback through `qwen3:8b`.

The source contains the browser UI itself, so restoring `assistant.py` restores both the HTTP API and dashboard.

## Evidence that it worked

`assistant.log` records successful interaction on 2026-09-30. The assistant answered requests for current priorities and captured multiple notes, including a phone-originated capture. This demonstrates that the HTTP/UI/state path was operating during that test session.

## Startup behavior

`start-assistant.ps1` checks whether TCP port 8765 already has a listener. If not, it launches `python "A:\AI\Assistant\assistant.py"` in a hidden window.

The 2026-10-06 machine inventory showed Ollama configured in Windows Startup, but did not show a Windows startup entry or service for this assistant itself. Therefore automatic Ollama startup was present, while automatic assistant startup was not proven by the forensic snapshot.

## Dependencies

1. Windows with Python available as `python`.
2. Ollama installed and running.
3. Ollama model `qwen3:8b` available locally.
4. Files restored to `A:\AI\Assistant`, unless hard-coded paths are changed.
5. TCP port 8765 available.

The application uses Python standard-library modules only (`http.server`, `pathlib`, `datetime`, `json`, `urllib.request`) based on the preserved source.

## Restart procedure

1. Restore `src/assistant.py` to `A:\AI\Assistant\assistant.py`.
2. Restore `src/start-assistant.ps1` to `A:\AI\Assistant\start-assistant.ps1`.
3. Restore `data/` if historical state should be retained.
4. Confirm `python --version`.
5. Confirm `ollama --version`.
6. Run `ollama list` and verify `qwen3:8b` exists.
7. Start Ollama if needed.
8. Run `A:\AI\Assistant\start-assistant.ps1`.
9. Verify port 8765 is listening.
10. Open `http://localhost:8765`. For phone access, use the dev machine LAN address with port 8765.
11. Test one deterministic command and one general question.

## Known limitations / unfinished work

- Interim assistant, not the full Riverview/Grace autonomous system.
- Persistence is a single JSON file; no database.
- Hard-coded Windows paths/model/port.
- No authentication on the LAN-facing HTTP server.
- No proven Windows service or scheduled startup mechanism for `assistant.py` in the forensic snapshot.
- State says version `0.1` while the current source prints `v0.2`; version naming was not normalized.
- Controlled commands were being added, but broader automation was unfinished.

## Relationship to HermesVisionGateway

Do **not** treat this directory as the HermesVisionGateway archive. The forensic scrape recovered extensive Hermes material already present throughout Riverview, including known-good 2026-09-22 multimodal gateway artifacts, tests, configuration, and scheduled-task XML. HermesVisionGateway is a separate historical line.

## Recommended next development step if resumed

Reproduce the preserved baseline before changing it: verify state load/save, desktop and phone dashboard, deterministic commands, Ollama fallback, then add a repeatable startup mechanism and smoke test. Only afterward decide whether this stays standalone or becomes a Riverview/Hermes front end.

## Preservation provenance

Reconstructed from a targeted forensic ZIP generated from the dev machine on 2026-10-06. Large models, caches, virtual environments, `.git` objects, and unrelated bulk Riverview content were intentionally excluded.