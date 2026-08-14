<!-- Version: 0.5.0 -->
# RIV-RUN-0001 — Runner rejected the action definition

Trigger: The claimed action is absent, disabled, version-mismatched, or missing its approved source hash.

Smallest repair: Correct the exact approved-action record through a migration or installer acceptance. Never execute raw command text from the work order.

Verify: Run the restricted-runner acceptance and require the registered no-op to succeed.