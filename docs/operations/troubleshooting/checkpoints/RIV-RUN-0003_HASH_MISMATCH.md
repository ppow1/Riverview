<!-- Version: 0.5.0 -->
# RIV-RUN-0003 — Registered command hash mismatch

Trigger: The repository script bytes do not match the hash approved in PostgreSQL.

Smallest repair: Inspect the source change, rerun its acceptance, and intentionally register the new hash. Do not bypass verification.

Verify: The runner starts only after the stored and calculated SHA-256 values match.