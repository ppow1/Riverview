<!-- Version: 0.5.0 -->
# RIV-RUN-0005 — Registered action exceeded hard timeout

Trigger: The subprocess remains active beyond its registered maximum runtime.

Smallest repair: Terminate the process, preserve captured output, mark the order timed out, and page the Steward before any retry.

Verify: The induced timeout probe is terminated and produces exactly one open escalation.