<!-- Version: 0.2.0 -->
# RIV-EVT-0001 — River event append failed

Trigger: A validated event cannot be appended to `river_events`.

Distinguish: First run the database health check. If healthy, inspect field shape, UUIDs, classification, JSON serialization, and unique keys. Preserve the original event and correlation identifiers.

Smallest repair: Correct only the rejected event field or the identified database boundary; do not bypass idempotency.

Verify: Run `.venv\Scripts\python.exe -m riverview.health event`; require one insertion, one non-inserting replay, and stream length one.