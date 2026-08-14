<!-- Version: 0.6.0 -->
# RIV-WRK-0007 — Listener startup failure

The acceptance worker did not establish `LISTEN riverview_work_orders` within five seconds. Verify PostgreSQL, credential ownership, and migration `0005` before retrying.