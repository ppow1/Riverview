<!-- Version: 0.1.0 -->
# RIV-UI-0028 — Operator activity projection and primary-view isolation

Use this checkpoint when authoritative River activity exists but Activity is
empty/stale, or when Conversation controls remain mounted around Architecture,
Activity, Notifications, or Settings.

The Activity surface is a bounded read projection over durable `river_events`
and related authoritative projections. It must expose a cursor, category, and
human-readable summary without becoming a workflow ledger. Primary views are
mutually exclusive presentation surfaces: only Conversations owns its rail,
transcript, resident controls, composer, and room actions.

While Activity is active, the authenticated River event stream is the preferred
freshness signal. It invalidates the current projection and triggers one
bounded cursor-based reconciliation; a single in-flight recovery timer may
supplement that signal while the tab is visible. Do not refresh hidden Activity
DOM, overlap requests, reset filters, or discard the existing stream on a
transient fetch failure. The cursor returned by the authoritative projection,
not display text, is the merge boundary.

Diagnose the served HTML/controller and canonical client state before changing
backend state. There must be one primary-view router and one binding for each
conversation, activity, architecture, notification, and settings operation.
Do not repair stale handlers by adding capture-phase interception,
`stopImmediatePropagation`, or another wrapper/override generation.

Recovery verification covers a real River event appearing in Activity, cursor
reconciliation after reconnect, view switching with rail/context states, and
returning to Conversations with the same durable conversation selected.
