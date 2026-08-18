# RIV-GRC-0008 — River-to-CME wakeup boundary

Component and seam owner: the persistent CME River consumer and its durable runtime projection.

Failure classes: `event-committed-no-wakeup`, `consumer-stopped`, `heartbeat-stale`, `cursor-replay`, `lost-wakeup`, `duplicate-delivery`.

## Symptom

An authoritative `river_events` row is committed, but CME does not observe it, its heartbeat becomes stale, or restart does not resume from the durable cursor.

## Diagnostic procedure

1. Confirm the event exists in `river_events` and record its `sequence_id`, `event_id`, `correlation_id`, and `causation_id`.
2. Inspect `cme_runtime_status` for `current_state`, `last_heartbeat_at`, and `last_river_sequence_seen`.
3. Verify the CME process has an active `LISTEN riverview_river_events` connection.
4. Compare the durable cursor with the event sequence. A cursor behind the event requires replay; a cursor ahead requires investigation.
5. Check diagnostic events for `RIV-GRC-0008` without exposing event payloads.
6. Inspect the external CME supervisor child/PID, restart policy, backoff, and
   stale-heartbeat probe. Correlate suspected GPU/provider pressure with
   absolute timestamps and measured `nvidia-smi`/provider evidence; current GPU
   load alone is not causal evidence.

## Smallest repair

Restore the persistent CME consumer lifecycle, PostgreSQL notification trigger,
cursor reconciliation, or external supervisor. The supervisor must recover an
exited child or stale heartbeat with bounded backoff. CME heartbeat and River
observation must not share a blocking provider execution path. Do not manually
insert business events, mark stages complete, or kick CME from the browser.

## Healthy verification

Promote a fresh bounded seed through the real Steward confirmation path, observe
the committed River event, verify a CME state transition and heartbeat update
without a manual cycle call, induce a safe child exit or stale heartbeat, and
verify supervisor recovery, replay exactly once, and continued healthy
heartbeats while a provider is saturated/unavailable. Record the exact last
healthy heartbeat, failure, restart, cursor, and objective lineage.

## DO NOT

Do not treat `ContinuousMomentumEngine.cycle()` tests, an Operator health response, a JavaScript timer, or a manually invoked cycle as proof that the runtime is listening.
