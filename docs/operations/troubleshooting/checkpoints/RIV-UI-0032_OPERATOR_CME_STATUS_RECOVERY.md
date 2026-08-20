# RIV-UI-0032 — Operator/CME status recovery

When Operator Activity shows an old River sequence while CME has advanced, compare
the displayed sequence with `MAX(river_events.sequence_id)` and the durable
`cme_runtime_status` projection. Activity reads the River projection; `/cme`
reads `/api/cme/status`, which reads the CME projection. A mismatch is not repaired
by refreshing the browser.

The expected behavior during a temporary backend or CME interruption is:

`UNAVAILABLE` → `RECONNECTING` → current healthy status.

Both pages must keep a bounded retry scheduled after fetch, HTTP, JSON, visibility,
or database errors. GET requests use no-store semantics and a bounded cache-buster;
older asynchronous responses must not overwrite newer state. If the last successful
projection is retained, its age must be visible and it must not be labeled current.

For runtime recovery, inspect the canonical supervisor owner and use the supervisor-
owned CME recycle request. Do not kill arbitrary Python processes or treat a browser
reload as the runtime repair. Verify one runtime supervisor, one CME supervisor tree,
one live CME consumer, one Relay owner, current heartbeat, and monotonic River cursor.
