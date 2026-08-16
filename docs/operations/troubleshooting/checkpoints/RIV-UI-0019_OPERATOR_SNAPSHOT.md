# RIV-UI-0019 — Operator debug snapshot boundary

The authenticated Riverview Operator Snapshot exports only the current browser
DOM and bounded state needed for diagnosis. It redacts bearer/session material,
excludes cookies, credentials, protected payloads, selected file bytes, and raw
audio, and returns one in-memory ZIP. Failure evidence must contain only safe
checkpoint metadata and correlation references.
