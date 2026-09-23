<!--
File: docs/operations/octominer/OCTO2_FAN_WATCHDOG_REBOOT_FORENSICS_2026-09-22.md
Version: 1.0
Date: 2026-09-22
Purpose: Verified OCTOMINER2 fan-controller, watchdog, reboot-path, and reboot-forensics findings collected during investigation of unexplained host reboots while running AI workloads.
-->

# OCTOMINER2 Fan, Watchdog, and Reboot Forensics — 2026-09-22

Status: Investigation in progress. This document separates verified facts from hypotheses and preserves the evidence needed for future troubleshooting.

## Scope

This document records the findings from the September 22, 2026 investigation of repeated OCTOMINER2 host reboots while the system was being used as a llama.cpp / Hermes AI server rather than as a mining rig.

The investigation focused on:

- Octominer USB fan-controller behavior.
- OctoFan hardware watchdog behavior.
- HiveOS mining watchdog behavior.
- HiveOS autofan behavior.
- HiveOS reboot paths.
- Physical chassis fan layout.
- Persistent reboot telemetry.
- Reboot classes distinguished by OctoFan reset-counter behavior.
- USB/fan-controller health.
- The persistent `sreboot` tripwire installed at the end of the investigation.

The current OCTOMINER2 control-plane documentation is:
`docs/operations/octominer/RIVERVIEW_OCTO_CONTROL_FEATURES_AND_API_2026-09-14.md`.

## Executive summary

The most important finding is that OCTOMINER2 has at least two distinct reboot classes.

1. Some historical boot transitions incremented the OctoFan controller's hardware watchdog Reset Counter.
2. A series of recent reboots, including the reboot at 2026-09-22 19:18:38 EDT, did **not** increment that counter.

Therefore the recurring recent reboot problem cannot be attributed solely to OctoFan watchdog expiry.

The HiveOS reboot helper `/hive/sbin/sreboot` was inspected in full. A normal invocation of `sreboot` ultimately performs a SysRq reboot with:

`echo b > /proc/sysrq-trigger`

and does **not** explicitly push the OctoFan reset command unless invoked as:

`sreboot wd`

This means an ordinary Hive software reboot can produce the exact signature observed in the recent events: a new Linux boot with the OctoFan Reset Counter unchanged.

The obvious Hive automatic reboot sources were not active at the time of inspection:

- Hive mining watchdog: `WD_ENABLED=0`.
- AutofAN `REBOOT_ON_ERROR`: unset.
- AutofAN `CRITICAL_TEMP_ACTION`: empty.
- No obvious reboot schedule was found in cron or systemd timers.
- No host-reboot implementation was found in the Riverview OCTO control code.

A persistent wrapper tripwire was therefore installed around `/hive/sbin/sreboot` so that the next software-triggered Hive reboot can be attributed to its caller.

## Current host and controller baseline

At the final verification point:

- Current boot start: `2026-09-22 19:18:38`.
- Current boot ID: `101646b3-fb91-4855-8921-1e9e89560e66`.
- OctoFan Watchdog Mode: `2`.
- OctoFan Reset Counter: `34`.
- Short watchdog timeout: `120s`.
- Controller-reported long timeout: `732s`.

The watchdog script requests a long timeout value of 1500 seconds, while the controller reports 732 seconds. The cause of this discrepancy has **not** yet been decoded and must not be treated as understood.

## OctoFan hardware watchdog architecture

The active watchdog script is:

`/hive/opt/octofan/watchdog-octofan`

Its relevant behavior is:

- Programs the controller watchdog with short timeout `120`.
- Requests long timeout `1500`.
- Probes local SSH on port 22 every 5 seconds.
- If SSH responds, runs:
  `/hive/opt/octofan/fan_controller_cli -s`
  to feed/reset the watchdog heartbeat.
- If SSH does not respond, it deliberately does **not** feed the watchdog.
- It supports an extended timeout mode that requests short `600`, long `1500`.
- It supports an explicit hardware reset path via:
  `fan_controller_cli -x`.

This is a real external motherboard-reset safety mechanism. It is not merely a Linux process watchdog.

The watchdog launcher runs in a detached screen session named `watchdog-octofan`.

## USB fan-controller identity

The Octominer controller is visible as:

- USB ID: `16c0:05dc`.
- Product: `Fan-Controller`.
- Manufacturer: `info@octominer.com`.

Controller versions observed:

- CLI: `3.1`
- Firmware: `2.7`
- Hardware: `1.2`
- Bootloader: `2.0`

Controller serial:

`0x51514353423809192002`

## USB communication health

A dedicated USB/watchdog feed test was performed.

Findings:

- The watchdog screen repeatedly showed:
  - `Pinging watchdog`
  - `Success`
- A direct machine-readable controller query completed successfully with exit code 0.
- No relevant current-boot USB disconnect/reset/timeout/XHCI errors were found.
- The watchdog process remained running normally.
- The OctoFan Reset Counter remained at 34.

One transient `fan_controller_cli -s` process had previously been observed in `D` state, but the deeper follow-up did not show an ongoing stuck feed. The later evidence therefore does **not** support a persistent USB hang as the current reboot cause.

## HiveOS mining watchdog

Hive configuration contains:

`WD_ENABLED=0`

The Hive `wd` utility contains reboot paths for conditions such as:

- High load.
- Lost GPUs.
- GPU power issues.
- Low hashrate.

However, the configured mining watchdog is disabled, so these paths are not currently the leading explanation for the recent reboot series.

## HiveOS autofan

Observed live config from `/hive-config/autofan.conf`:

- `TARGET_TEMP=60`
- `TARGET_MEM_TEMP=90`
- `MIN_FAN=40`
- `MAX_FAN=100`
- `CRITICAL_TEMP=90`
- `CRITICAL_TEMP_ACTION=""`
- `REBOOT_ON_ERROR=`

The autofan process is running, but the current config does not enable reboot-on-error and does not define a critical-temperature action.

The autofan script contains code capable of invoking `sreboot` under error or critical-temperature conditions if configured, but the observed config does not enable those actions.

## Physical chassis fan finding

The controller exposes 12 fan channels, but the chassis uses a subset.

Current live RPM values showed:

- Fan 0: approximately 1780 RPM.
- Fan 2: approximately 1300–1400 RPM.
- Fan 4: approximately 1280–1320 RPM.
- Fan 6: approximately 1290–1350 RPM.
- Fan 8: `0 RPM`.

The controller's stored maximum RPM values showed:

- Fan 0 max: `3700`
- Fan 2 max: `3580`
- Fan 4 max: `3445`
- Fan 6 max: `3415`
- Fan 8 max: `3435`

Fan 8 is therefore different from truly unused channels: it currently reports 0 RPM but has a previously learned nonzero maximum.

The physical machine configuration explains this. One chassis fan was intentionally removed to create clearance for the RTX 4090 in the Octominer 12 Ultra chassis.

The evidence strongly supports:

**Fan 8 is the intentionally removed fifth chassis fan.**

The controller still commands PWM to Fan 8, but no tachometer RPM is returned.

## Missing Fan 8 is not currently supported as reboot cause

The OctoFan script was inspected for RPM, fan-failure, reboot, shutdown, reset, and `sreboot` handling.

Relevant findings:

- Low fan maximum RPM can generate warning/error messages.
- Fan-control logic adjusts PWM factors based on actual versus target fan speed.
- Missing/zero fan readings are skipped or handled in fan-control calculations.
- No code path was found that directly reboots the machine merely because a chassis fan is absent or reports 0 RPM.
- The OctoFan error LED behavior can be enabled/disabled independently.
- The current config has `BLINK_ON_ERRORS=0`.

Therefore:

**The removed Fan 8 is a verified hardware-layout fact, but no evidence currently shows that it causes the unexplained host reboots.**

This distinction must be preserved in future troubleshooting.

## HiveOS `sreboot` behavior

The complete `/hive/sbin/sreboot` script was inspected.

Important behavior:

1. If the root filesystem is already read-only:
   - Enables SysRq.
   - Executes `echo b > /proc/sysrq-trigger`.
   - Calls `reboot -f`.

2. In normal mode:
   - May prepare the system and stop watchdog feed processes.
   - Extends the OctoFan watchdog timeout.
   - Syncs filesystems with SysRq `s`.
   - Remounts/unmounts with SysRq `u`.
   - Finally performs:
     `echo b > /proc/sysrq-trigger`
     followed by `reboot -f`.

3. Only when invoked as:
   `sreboot wd`
   does it explicitly issue hardware watchdog reset commands, including:
   `/hive/opt/octofan/watchdog-octofan reset`.

This is critical to interpreting the Reset Counter:

**An unchanged OctoFan Reset Counter does not rule out a normal Hive `sreboot`.**

It rules out watchdog-expiry-style resets for that event, but ordinary software `sreboot` remains compatible with the observed signature.

## SysRq configuration

Observed:

`kernel.sysrq = 176`

The `sreboot` script explicitly writes:

`echo 1 > /proc/sys/kernel/sysrq`

before using SysRq, so the preexisting value does not prevent Hive from executing forced SysRq reboot operations.

## Reboot history from persistent Riverview monitoring

The persistent monitor records boot IDs and OctoFan watchdog reset counts.

Historical transitions with Reset Counter increase included:

- `0953c654 -> dfdbf981 | 25 -> 31`
- `dfdbf981 -> bedfa775 | 31 -> 32`
- `67d9bbaf -> 23001f96 | 32 -> 33`
- `ae1e8700 -> a399070f | 33 -> 34`

The `25 -> 31` jump may represent multiple unseen hardware watchdog resets between retained samples and should not be interpreted as six resets caused by one transition.

Recent transitions with **no** Reset Counter increase included:

- `a399070f -> 26494e02 | 34 -> 34`
- `26494e02 -> 18f90d66 | 34 -> 34`
- `18f90d66 -> 89b04603 | 34 -> 34`
- `89b04603 -> 9e01fee4 | 34 -> 34`
- `9e01fee4 -> 85ce3fa3 | 34 -> 34`
- `85ce3fa3 -> 101646b3 | 34 -> 34`

The last transition corresponds to the reboot at approximately 19:18:38 EDT on September 22, 2026.

This establishes that the recent reboot pattern is not primarily explained by OctoFan watchdog expiry.

## Thermal and power observations

Persistent telemetry immediately before several non-OctoFan-counter reboots showed:

- GPU utilization often at or near 0%.
- GPU temperatures generally in the approximate 43–56 C range.
- Low/modest power draw.
- OctoFan watchdog counter unchanged.

The final sample before a reboot can precede the actual reboot by tens of seconds or minutes, so this does not prove that no transient thermal/power event occurred between samples.

However, there is no consistent telemetry signature showing thermal overload or sustained high-power operation immediately before the recent reboot series.

The OctoFan controller PSU telemetry during investigation also showed normal PSU temperatures and modest load.

## Heavy model-load observations

At least one earlier boot showed substantial model allocation/loading behavior:

- GPU memory allocations increased significantly across multiple GPUs.
- One GPU reached 100% utilization for roughly 50 seconds.
- Allocations later dropped.

Heavy AI workload activity can therefore occur near reboot windows, but this pattern was not present before every reboot and is not sufficient evidence of causality.

A stale model-profile note saying that a 65K Hermes test "coincided with" an OCTO2 reboot must not be interpreted as proof that 65K context caused the reboot.

Other evidence confirms 65,536-context Hermes operation can work.

## Persistent monitor implementation and limitation

Riverview's monitor stores persistent data under:

`/mnt/octo-models-stage/riverview-octo-monitor`

Relevant files include:

- `current.json`
- `events.jsonl`
- `telemetry.jsonl`
- `load-history.json`

The monitor:

- Samples approximately every 10 seconds.
- Captures boot ID, uptime, GPUs, watchdog state, deployment state, instances, and other host state.
- Writes a `boot_changed` event when it detects a boot ID transition.
- Records watchdog reset count before/after a boot transition.

A known limitation is that monitor service detection checks `riverview-llama.service`, while the legacy active llama server was observed under `llama-server.service`. This can make `service_active=false` misleading even when the legacy server process is running.

That mismatch should be corrected separately.

## Normal logs are not sufficient for previous-boot forensics

Current HiveOS logging was found to be largely volatile for this purpose.

Findings:

- `last -x` started at the current boot.
- Current journal/syslog data did not preserve the previous boot cause.
- `pstore` was empty.
- Therefore a reboot can erase the best software-side evidence before it is examined.

This is why persistent telemetry and tripwire logging are necessary.

## Scheduled reboot investigation

Systemd timers and cron were inspected.

Observed timers were routine maintenance jobs such as:

- dpkg database backup.
- logrotate.
- tmpfiles cleanup.
- filesystem trim.
- snap/UA maintenance.

Root Hive cron contained routine mining/log/cache/agent jobs.

No explicit recurring reboot schedule was found.

## Hive agent reboot capability

HiveOS contains code paths capable of rebooting the host on explicit commands.

`/hive/bin/agent.do_command.sh` can invoke `sreboot` in response to remote reboot commands and certain firmware-related flows.

This remains a viable software reboot mechanism.

The current logs did not contain a preserved previous-boot event proving that the Hive agent invoked the recent reboot.

## Filesystem read-only emergency path

`/hive/bin/agent` contains an emergency path that can force reboot if the filesystem becomes read-only.

`sreboot` itself also has a read-only-root shortcut that performs an immediate SysRq reboot.

Because previous-boot logging is not persistent, this path is not yet ruled out.

## Riverview OCTO control service

The Riverview control-plane code was inspected.

No host reboot implementation was found in:

- `server.py`
- `monitor.py`
- `instance_manager.py`

The control service manages model processes/services, GPU allocations, fan commands, monitoring, and API state, but the inspected implementation does not initiate host reboot.

Therefore the current evidence does not support Riverview OCTO Control as the source of the host resets.

## OLED stale-IP behavior

The OctoFan OLED's stale IP display was investigated separately.

The OctoFan code saves selected text to EEPROM. The Hive `hello` flow calls the save-to-EEPROM function and writes the current IP into persistent controller storage.

Other display updates are nonpersistent.

Therefore a stale OLED IP is consistent with an old EEPROM snapshot and does **not** indicate that the current network stack is using that stale address.

## Reboot tripwire installed

Because normal logs are not persistent enough to identify the next software reboot caller, a persistent tripwire was installed around:

`/hive/sbin/sreboot`

Installation details:

- Original Hive script preserved as:
  `/hive/sbin/sreboot.riverview-original`
- Preserved original SHA-256:
  `f4e0dcb44afbb1344f4e66adb1b9a007f56483c29e98fe750afcaf6abb09a6b3`
- Wrapper installed at:
  `/hive/sbin/sreboot`
- Both original and wrapper passed `bash -n` syntax validation.
- No reboot was triggered to test the tripwire.
- The wrapper logs evidence, then executes the untouched original script with the original arguments.

Persistent event log:

`/mnt/octo-models-stage/riverview-octo-monitor/reboot-tripwire/sreboot-events.log`

The wrapper records:

- Timestamp.
- Boot ID.
- Uptime.
- `sreboot` arguments.
- Wrapper PID.
- Parent PID.
- Parent command line.
- Grandparent PID.
- Grandparent command line.
- Process ancestry.
- Recent Hive agent log content.
- A sync before executing the original reboot script.

Current tripwire state at installation:

- Status: `ARMED`
- Boot ID: `101646b3-fb91-4855-8921-1e9e89560e66`
- OctoFan Reset Counter: `34`

## What the tripwire can and cannot prove

If the next unexplained reboot produces a new entry in `sreboot-events.log`, that will strongly identify the software caller and its arguments.

If the machine reboots and the log contains no corresponding `sreboot` event, the normal Hive `sreboot` path becomes substantially less likely.

An empty tripwire log does **not** rule out:

- Direct `reboot -f`.
- Direct writes to `/proc/sysrq-trigger`.
- Kernel panic/crash.
- AC/power interruption.
- Motherboard-level reset.
- OctoFan hardware watchdog expiry.
- Another hardware watchdog.
- A controller reset path that bypasses `sreboot`.
- Filesystem failure severe enough to prevent persistent logging.

Further instrumentation may be needed if the next reboot bypasses the tripwire.

## Current working conclusions

### Verified

- The OctoFan hardware watchdog is active.
- Its feed loop checks SSH every 5 seconds.
- Its configured short timeout is 120 seconds.
- The controller reports Watchdog Mode 2.
- Some historical reboots incremented the OctoFan Reset Counter.
- The recent reboot series did not increment the counter.
- Normal Hive `sreboot` can reboot without incrementing the OctoFan counter.
- Hive mining watchdog is configured disabled.
- AutofAN reboot-on-error is not enabled.
- AutofAN critical-temperature action is empty.
- No obvious scheduled reboot was found.
- Riverview control code does not contain a host-reboot implementation.
- USB communication to the OctoFan controller was healthy during testing.
- The chassis historically had five populated fan channels: 0, 2, 4, 6, 8.
- Fan 8 currently reads 0 RPM but has a learned max RPM and corresponds to the intentionally removed fan required for RTX 4090 clearance.
- No OctoFan script path was found that reboots simply because Fan 8 is absent.
- A persistent `sreboot` tripwire is now armed.

### Not yet proven

- What caused the 19:18:38 reboot.
- Whether the Hive agent issued a reboot command.
- Whether a read-only filesystem condition triggered reboot.
- Whether another software path wrote directly to SysRq.
- Whether a motherboard/power-level reset occurred.
- Exact OctoFan firmware semantics of Watchdog Mode 2.
- Why requested long timeout 1500 is reported as 732.
- Exactly which controller events increment Reset Counter.
- Whether any future reboot will be attributed by the new tripwire.

## Recommended next action after another reboot

Do **not** manually power-cycle the machine after the next unexplained reboot if it comes back by itself.

Immediately collect:

1. `/mnt/octo-models-stage/riverview-octo-monitor/reboot-tripwire/sreboot-events.log`
2. Latest persistent monitor `boot_changed` event.
3. Watchdog Reset Counter before/after.
4. New boot ID and boot start time.
5. Last telemetry samples from the previous boot.

Interpretation:

- Tripwire event + unchanged OctoFan counter:
  likely ordinary Hive software reboot.
- No tripwire event + incremented OctoFan counter:
  likely OctoFan watchdog/hardware-reset class.
- No tripwire event + unchanged OctoFan counter:
  investigate direct SysRq, kernel crash, power/reset, filesystem emergency, or other bypass paths.

## Operational caution

Do not disable the OctoFan watchdog or fan-control stack merely to stop the reboots.

The system is now running high-value AI hardware, including an RTX 4090, in a chassis whose original airflow layout was physically modified. The existing fan and watchdog mechanisms provide real thermal and recovery protection.

Changes should target the proven reboot source once identified, while preserving:

- Active chassis cooling.
- PSU monitoring.
- Temperature protection.
- Useful watchdog protection that is compatible with AI-server workloads.

## Related documentation

- `docs/operations/octominer/RIVERVIEW_OCTO_CONTROL_FEATURES_AND_API_2026-09-14.md`
- `docs/operations/octominer/OCTOMINER_REMOTE_POWER_AND_WOL.md`
