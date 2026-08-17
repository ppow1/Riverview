<!-- Version: 0.1.0 -->
# RIV-UI-0024 — Operator UX state reconciliation

Use this checkpoint when an existing Operator control is present but its
observable lifecycle, layout state, archive state, room display projection, or
secondary-route navigation is incorrect.

Safe probes include extracting the live HTML/JavaScript, checking the
authoritative Operator projection, and exercising the control through the
running service. Repairs must preserve resident continuity/canon and must not
replace authoritative event state with browser-only state.

Recovery verification covers microphone IDLE/LISTENING/TRANSCRIBING/FAILURE
states, independent conversation scrolling, rail/context-independent routing,
human-first message details with raw disclosure, archive/reopen behavior, and
human-readable room participant projections.
