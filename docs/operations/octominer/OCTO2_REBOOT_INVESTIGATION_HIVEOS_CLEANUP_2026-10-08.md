# OCTO2 Reboot Investigation — HiveOS Mining-Stack Isolation (2026-10-08)

**Status:** Changes applied and verified during current boot; reboot stability and persistence **not yet verified**. Follow-up to [September 22 OCTO2 fan/watchdog/reboot forensics](OCTO2_FAN_WATCHDOG_REBOOT_FORENSICS_2026-09-22.md).

## Purpose and scope
Document verified observations and configuration changes made October 8, 2026 (EDT) while investigating unexplained OCTOMINER2 restarts. OCTO2 is an AI inference host, **not an intended cryptocurrency miner**. Avoid conflating reboot-capable code with a proven cause of any reboot.

## Machine baseline
- Host: **OCTOMINER2**, HiveOS Linux; current boot ID `bcbd305d-0f9d-4b7c-8a3e-17879cc20584`, observed at 21:44–21:54 EDT.
- NVIDIA enumeration: **five GPUs**: Tesla P100 16GB ×4 (GPU indices 0,2,3,4) and RTX 4090 (index 1). A separate installed 3060 Ti was not enumerated in earlier investigation; this cleanup did not resolve that.
- `llama-server.service` running Qwen3-Next 80B; `curl http://127.0.0.1:8080/health` returned `{"status":"ok"}` after each change.
- OctoFan hardware controller `/hive/opt/octofan/fan_controller_cli -h`: Watch-Dog Mode **2**, Reset Counter **55**, short timeout **120s**, reported long timeout **732s**; counter unchanged during cleanup.
- OctoFan controller/watchdog and `autofan` continued running after each change.
- User confirmed motherboard HDMI video works from power-on splash through Linux boot; HDMI recovery no longer active priority.

## Discovery 1 — Unexpected live cryptocurrency miner
At 21:44 EDT, process tree included `/hive/bin/miner-run custom 1` launching `/hive/miners/custom/onezerominer/h-run.sh` and `onezerominer` using **qhash** against `ca.luckypool.io:8611`. Wallet/flight-sheet config was found in `/hive-config/wallet.conf`; **wallet address deliberately omitted** from this documentation. The wallet worker suffix and `WORKER_NAME` were **OCTOMINER1**, despite hostname **OCTOMINER2**, suggesting a stale or copied mining configuration (not proven).
- `/hive-config/rig.conf` line 21 was `MINER=custom`.
- `/hive/bin/hive` invokes `miner start` at startup.
- A sampled `onezerominer` child was only 3 seconds old while its `miner-run` parent was nearly 6 minutes old, consistent with repeated miner launches/restarts, but not definitive proof of the restart reason.
- Hive startup also attempted NVIDIA overclock application; an earlier log recorded a failed NVIDIA overclock operation. No evidence establishes that overclocking or mining caused a reboot.

### Applied change (21:45 EDT)
1. Backed up `/hive-config/rig.conf` to **`/hive-config/rig.conf.before-ai-only-20261008-214529`**.
2. Changed `MINER=custom` to **`MINER=`** in `/hive-config/rig.conf`.
3. Executed HiveOS `miner stop`; it sent Ctrl+C to the miner screen.
4. Verified no `onezerominer` or `miner-run` process; hardware controls, five GPUs, Qwen health intact.
**Persistence after next boot not yet tested.** `/hive-config/wallet.conf` and miner binaries were **not** deleted.

## Discovery 2 — Hive cloud agent can receive remote reboot commands
- `/hive/bin/agent` sends statistics and receives commands; sources `/hive/bin/agent.do_command.sh`.
- `agent.do_command.sh` has a `reboot)` command branch that launches `sreboot`; other command paths can reboot after ROM flashing.
- `/hive/bin/agent` has a separate `reboot -f` emergency path if root filesystem becomes read-only.
- `/hive/bin/hive` invoked `agent-screen start` during boot.
- `/hive/etc/crontab.root` and installed root crontab ran `agent-screen dontattach` **every 10 minutes**; the wrapper restarts missing or stale agents.
- Both `agent` and `agent.gpu-stats` were running before change.
- **No preserved log evidence proves the agent caused any spontaneous reboot.**

### Applied change (21:51 EDT)
1. Backed up `/hive/bin/hive` to **`/hive/bin/hive.before-ai-only-20261008-215142`**.
2. Backed up `/hive/etc/crontab.root` to **`/hive/etc/crontab.root.before-ai-only-20261008-215142`**.
3. Commented the startup invocation at Hive script line 344: `# AI_ONLY_DISABLED agent-screen start`.
4. Commented the 10-minute agent restart cron entry with `# AI_ONLY_DISABLED`, then installed modified crontab using `crontab /hive/etc/crontab.root`.
5. Ran `agent-screen stop`, which quit the agent screen; verified no agent or gpu-stats processes.
6. Verified OctoFan controller, hardware watchdog, autofan, all five GPUs, and Qwen healthy.

## Discovery 3 — Hive software watchdog still running despite WD_ENABLED=0
- `hive-watchdog.service`: `ExecStart=/hive/bin/wd run`, `Restart=always`, `KillMode=process`; **active** though `UnitFileState=disabled` (Hive startup calls `wd start`).
- `/hive-config/rig.conf`: `WD_ENABLED=0`.
- Service logs at 21:37:55 stated `Watchdog disabled in config`, yet the daemon continued printing load checks every minute.
- Source `/hive/bin/wd` includes reboot-capable branches: 5-minute load average at/above 24, 1-minute load average at/above 48 after repeated checks, lost GPU stats, and abnormal GPU power; invokes `sreboot` or `sreboot fast` under corresponding conditions. **Code presence is not proof these branches were active while disabled.** The watchdog's `loadconf` returns early with `disable=1` when `WD_ENABLED!=1`; actual invocation/guarding of individual checks should be verified before attributing a reset to this service.
- Observed load averages were roughly 0.78–2.32, well below reported thresholds; logs did not show a load-triggered reboot.

### Applied change (21:54 EDT)
1. Backed up `/hive/bin/hive` to **`/hive/bin/hive.before-watchdog-disable-20261008-215419`**.
2. Commented Hive startup line 294: `# AI_ONLY_DISABLED wd start`.
3. Ran `systemctl stop hive-watchdog.service` and `systemctl disable hive-watchdog.service`.
4. Verified `ActiveState=inactive`, `UnitFileState=disabled`.
5. Verified independent OctoFan watchdog screen, OctoFan fan control, autofan, five NVIDIA GPUs, and Qwen healthy; hardware Reset Counter remained 55.

## Hardware watchdog — deliberately preserved
The OctoFan watchdog is **not** `hive-watchdog.service`. Its script `/hive/opt/octofan/watchdog-octofan` probes localhost SSH port 22 every 5 seconds; only when the port responds does it feed the external controller with `fan_controller_cli -s`. If SSH fails for long enough, the hardware watchdog may reset the motherboard. Do not stop or replace this feed without planning controller safety, timing, and a single feeder. Script requests 1500s long timeout while controller reports 732s; discrepancy remains unresolved.

## Other observations and limitations
- HiveOS autofan was running, but `CRITICAL_TEMP_ACTION=""` and `REBOOT_ON_ERROR=`; automatic reboot actions were not configured. **Autofan retained.**
- Earlier October 8 inspection found configured mount `/mnt/octo-models-stage` absent from `lsblk`/`blkid` during that boot; Riverview monitor and `sreboot` tripwire logs on that volume were unavailable. Investigate missing drive/mount separately; do not assume files were deleted. Lack of durable logs limits causal attribution.
- Previously installed `sreboot` tripwire wrapper may still be present, but logging destination on missing model-stage mount is not reliably available. No new reboot occurred during this cleanup window.
- Motherboard HDMI was confirmed working; an `octo2-hdmi.service` detection failure seen earlier does not override the user's live confirmation.
- No OS reinstall, GPU BIOS changes, fan controller firmware changes, or deliberate reboot performed.

## Follow-up / acceptance criteria
1. **Observe stability without further changes**; record next reboot time, boot ID, OctoFan Reset Counter, GPU enumeration, Qwen `/health`, and whether miner/agent/software watchdog stay disabled.
2. If reset counter **increases**, prioritize OctoFan hardware watchdog expiry, feed failure, or external controller reset. If **unchanged**, software reboot (including Hive `sreboot`), power, firmware, and other mechanisms remain possible; do not treat unchanged count as proof of software origin.
3. Recheck `MINER=`, `agent-screen` boot and cron suppression, and `hive-watchdog.service` inactivity **after a natural reboot**.
4. Restore reliable persistent monitor and tripwire logging once `/mnt/octo-models-stage` mount issue is understood; avoid logging only to a missing volume.
5. Evaluate remaining unnecessary Hive startup functions (e.g. `hello boot`, NVIDIA OC, `tweakers`) **separately**, only after stability observation and without endangering drivers, fan control, or video.
6. Preserve timestamped backups; note that `/hive/bin/hive` was edited twice, with the second backup containing the prior agent-disable edit.

## Evidence and audit timestamps
- 21:38–21:44: initial process/config/drive/HDMI inspection; live OneZeroMiner found.
- 21:45: miner disabled and stopped, successful post-change verification.
- 21:48–21:50: agent, cron, autofan, software watchdog audit.
- 21:51: agent startup and cron disabled, agent stopped, successful verification.
- 21:52–21:54: software watchdog source inspected, then stopped/disabled, successful verification.
- Final observed state: miner absent; cloud agent absent; Hive software watchdog inactive; OctoFan hardware watchdog + cooling running; **5 NVIDIA GPUs**; Qwen `{"status":"ok"}`; Reset Counter **55**.

**Conclusion:** The mining stack contained several reboot-capable pathways and unexpected active mining workload. We removed the unnecessary components without disrupting AI inference or external hardware control. **Root cause of spontaneous reboots remains unproven; post-change stability is the decisive next test.**
