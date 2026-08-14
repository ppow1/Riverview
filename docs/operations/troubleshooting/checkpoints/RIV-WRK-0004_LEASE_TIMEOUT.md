<!-- Version: 0.4.0 -->
# RIV-WRK-0004 — Worker lease expired

Trigger: A claimed or running work order stops heartbeating before completion.

Smallest repair: Preserve the attempt evidence, page the Steward, and determine whether the registered action is retry-safe before requeueing.

Verify: The order is `timed_out` and exactly one open Steward escalation identifies the work order and checkpoint.