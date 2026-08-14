<!-- Version: 0.6.1 -->
# RIV-WRK-0009 — Worker acceptance invariant

One or more notification-loop invariants failed: notification receipt, successful work completion, durable worker state, or bounded shutdown. Query the work order and `relay_workers` row using the shared correlation evidence.
Observed startup readiness race: readiness was signaled before backlog drain, allowing new work to complete before notification accounting. Drain backlog before signaling readiness, then require explicit invariant evidence.
