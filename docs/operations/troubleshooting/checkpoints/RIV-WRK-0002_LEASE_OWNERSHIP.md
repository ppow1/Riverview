<!-- Version: 0.4.0 -->
# RIV-WRK-0002 — Worker heartbeat lacks lease ownership

Trigger: A worker heartbeats an order it does not currently own or whose lifecycle is terminal.

Smallest repair: Stop the stale worker, inspect the current owner and attempt, and reclaim only when the action is explicitly retry-safe.

Verify: One worker claims the order; a different worker must be unable to heartbeat it.