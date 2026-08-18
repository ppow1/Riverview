# RIV-UI-0019 — Operator debug snapshot boundary

The authenticated Riverview Operator Snapshot is a bounded forensic representation
of the operator-visible state plus supporting system evidence at capture time.
Schema v2 separates `visible_state.json` (machine-readable client projection)
from `rendered_state.html` (the bounded rendered `#app` projection). The legacy
`current_dom.html` remains available for compatibility and must not be treated as
the complete visible-state contract by itself.

For Activity, `visible_state.json` records loaded and displayed items, stable
event/activity identifiers, display order, filter, cursor/page boundary, loading,
error, empty, selection, and `has_more` state. Other views record their bounded
loaded projection and the rendered artifact supplies the cross-check. Client and
server timestamps are both recorded; capture is not claimed atomic across browser
and backend sources.

The snapshot redacts bearer/session material, excludes cookies, credentials,
protected payloads, selected file bytes, raw audio, and unrestricted internal
prompts, and declares any visible-state or rendered-state truncation. Failure
evidence contains only safe checkpoint metadata and correlation references.

When diagnosing a snapshot, distinguish API/backend evidence from `visible_state`
and `rendered_state`: the latter answer what the authorized operator was actually
seeing, while API state explains the supporting projection and may differ because
of client loading, filtering, or pagination timing.
