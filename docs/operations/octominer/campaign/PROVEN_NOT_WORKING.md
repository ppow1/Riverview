# Proven Not Working / Known Failure Conditions

## PNW-001 — Riverview telemetry monitor currently cannot start
riverview-octo-monitor.service requires /mnt/octo-models-stage.
That filesystem is not currently mounted, causing a systemd dependency failure.

## PNW-002 — Riverview monitor deployment state is stale
/opt/riverview-octo-control/state.json describes the previous Qwen3-Coder 30B
deployment on port 8101, not the currently running Qwen3-Next 80B service on
port 8080.

## PNW-003 — Octo2 has an unresolved reboot problem
Root cause unknown.
The BIOS campaign must tolerate and record Octo2 outages rather than assuming
continuous availability.

## PNW-004 — Automated physical reset is not yet available
Current implementation is Steward notification followed by manual RESET.

## PNW-005 — Original OCTO2 monitor parser produced false worker-down state
T-SCAF-001 demonstrated that parsing multiple shell-derived fields through one
SSH command can shift field boundaries. The original implementation falsely
reported `80B_PROCESS_DOWN`.

Corrective rule: use simple remote output and perform structural parsing in the
DEV-side controller.

## PNW-006 — Boot-change event can be lost across unreachable samples
The current OCTO2 monitor compares boot identity against the immediately
previous sample.

During T-SCAF-002, unreachable samples contained no boot ID, so the monitor
failed to emit an explicit `octo2_boot_changed` event when OCTO2 returned with
a new boot ID.

Required correction:
retain `last_known_boot_id` across unreachable samples.
