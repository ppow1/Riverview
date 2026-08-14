<!-- Version: 0.4.0 -->
# RIV-WRK-0001 — Action unknown or disabled

Trigger: A producer requests an action absent from the enabled approved-action registry.

Smallest repair: Verify the intended `action_type`; register and test a versioned action through an approved migration. Never substitute arbitrary shell text.

Verify: Enqueue the registered action and require one queued work order with its declared version and limits.