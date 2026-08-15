# RIV-MCP-0010 — Steward seed draft and ChatGPT schema boundary

SYMPTOM: The local MCP surface exposes `submit_steward_seed`, but an application or
existing conversation does not expose it, or a seed is duplicated/promoted without
confirmation.

LIKELY BOUNDARY: Local tool registration, manifest/deployment version, conversation
schema binding, or the bounded seed-draft lifecycle.

SAFE DIAGNOSTIC: Compare the local tool list, nonsecret manifest, deployed endpoint
tool list, and conversation-bound schema separately; inspect `steward_seed_drafts`
by idempotency key.

EXPECTED HEALTHY RESULT: One bounded seed creates one `draft` for
`chatgpt:riverview_001`; no work order or objective is created until explicit
Steward confirmation.

KNOWN FAILURE: `RIV-0085-0001` rejects empty/oversized/unsupported input;
`RIV-0085-0002` rejects non-Steward promotion. A deployed app may be stale even when
the repository and app administration schema are current.

REPAIR: Fix the local contract or refresh the supported application binding. Preserve
the draft and do not create another seed to mask a schema cache.

VERIFY: Confirm one draft, no executable work, explicit `steward` promotion, and the
expected tool at the actual external conversation boundary.

DO NOT: treat conversation text as authority, promote automatically, rotate secrets,
or widen MCP to generic mutation.

EVIDENCE: `steward_seed_drafts`, manifest version, MCP tool-list evidence, and the
external-platform checkpoint.
