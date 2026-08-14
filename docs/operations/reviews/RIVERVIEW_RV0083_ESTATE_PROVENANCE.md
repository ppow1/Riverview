# RV-008.3 Estate provenance and ownership boundary

The Estate browser worker and bounded proof-of-concept were inspected as
provenance. Useful mechanics were the localhost CDP connection, persistent
browser-profile concept, bounded readiness probe, fixed composer interaction,
metadata-only evidence, and timeout classification.

Riverview deliberately rejects heuristic target fallback, generic prompt
input, arbitrary DOM evaluation, navigation/recovery, target enumeration, and
response scraping. Riverview runtime code does not import, execute, or read
Estate source, data, configuration, or browser state.

Riverview owns:

- `tools/riverview_doorbell_bridge.cjs`;
- `tools/riverview_browser_runtime.cjs`;
- `A:\Riverview\runtime\doorbell\` configuration and diagnostics;
- `A:\Riverview\runtime\browser\profile\` persistent browser profile;
- `src/riverview/doorbell/browser_bridge.py`.

The local configuration is created with:

```powershell
python -m riverview.doorbell.bootstrap --conversation-id <uuid>
```

The command discovers a supported installed Chromium executable unless an
explicit local override is supplied. It stores only target identity, browser
executable path, localhost CDP port, and adapter version. Authentication remains a normal interactive
browser-profile action and is never captured by Riverview.
