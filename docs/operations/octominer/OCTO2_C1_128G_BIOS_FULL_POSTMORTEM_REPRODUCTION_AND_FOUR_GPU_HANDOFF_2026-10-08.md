# C1 128-GiB BIOS — engineering postmortem, reproducibility dossier, OCTO2 four-GPU milestone
**Date:** 2026-10-08 EDT  
**Repository:** ppow1/Riverview  
**Status:** OCTO2 C1 BIOS boot + 4090/3×P100 + 80B inference **verified**; fifth GPU **not yet tested**; stability **unqualified**. OCTO1 interrupted flash remains separate NO-POST incident.

> **START HERE FOR A NEW AI:** Read this entire document, then the linked OCTO1 incident and recovery documents and canonical campaign requirements/process map. Do not confuse OCTO1 and OCTO2, or interpret the interrupted OCTO1 write as proof of a bad C1 firmware image. Do not flash from an unverified filename. Current next action is physical addition of one more P100 to OCTO2 by Steward, followed by staged enumeration/BAR/driver/model/stability qualification.

## 1. Executive summary
The campaign seeks stable support for **10+ Tesla P100 16-GiB** cards on an OctoMiner platform by addressing PCIe high-memory MMIO/BAR allocation while retaining workable firmware boot times. A deliberately modest **C1 128-GiB high-MMIO** candidate was constructed by changing three bytes in the PciHostBridge module while leaving the PciBus threshold unchanged. Earlier 372/384-GiB aperture experiments suffered catastrophic firmware initialization latency; they must not be confused with C1.

On OCTO1 on 2026-10-07, Intel FPT entered BIOS erase/program but lost observation before success; OCTO1 subsequently had no POST. Outcome **INDETERMINATE / interrupted write**. On OCTO2 on 2026-10-08, C1 was flashed with EFI FPT, FPT reported completion and immediate verification, HiveOS booted, and a 128-GiB root bridge window was observed at 0x2000000000–0x3fffffffff. CPU baseline remained unchanged within measurement variation. The RTX4090 plus two P100s loaded the 80B model and completed two inference runs. Adding a third P100 (four GPUs total) resulted in all four GPUs enumerating, driver initialization and model allocations on all four, model health OK, and two successful inference runs. One unexpected reboot occurred in the four-GPU configuration before the successful run. Persistent journaling was enabled afterward. Stability and fifth GPU remain unproven.

## 2. Source hierarchy / documents
- Canonical requirements: `docs/operations/octominer/campaign/PROJECT_REQUIREMENTS.md`
- Canonical process: `docs/operations/octominer/campaign/PROCESS_MAP.md`
- Approved proposal, reground contract/packet, proven facts, lessons, open questions in `docs/operations/octominer/campaign/`
- OCTO1 C1 interrupted flash, extensive hashes/media/paths: `docs/operations/octominer/OCTOMINER1_C1_BAD_FLASH_FULL_POSTMORTEM_AND_RECOVERY_HANDOFF_2026-10-07.md`
- Proven stock recovery and prior large-aperture experiment: `docs/operations/octominer/OCTOMINER1_FPT_EFI_BIOS_RECOVERY_AND_MULTI_P100_MMIO_PLAN_2026-09-14.md`
- Hardware identity: `docs/operations/octominer/OCTOMINER1_OCTOMINER2_HARDWARE_SCAN_2026-09-14.md`
- Reboot/watchdog forensics: `docs/operations/octominer/OCTO2_FAN_WATCHDOG_REBOOT_FORENSICS_2026-09-22.md`
- Separate campaign repo: `ppow1/OctoMiner_BIOS_Campaign`; OCTO1 incident duplicate at `INCIDENTS/OCTO1_C1_FLASH_INTERRUPTION_POSTMORTEM_2026-10-07.md`.
- This document records OCTO2 results reported in the October 8 operator terminal transcript; not all terminal logs/artifacts are yet committed. **This is a reconstruction, not a claim of possessing a byte-for-byte OCTO2 flash log.**

## 3. Identities, interfaces, roles
| Node | Alias/IP | Notes |
|---|---|---|
| OCTO1 | `octo1` / 192.168.1.160 | X12 Ultra Ver 1.52; MAC 00:e0:4c:6b:05:a9; i5-6500; OCTO1 C1 flash interrupted, no POST as of prior incident |
| OCTO2 | `octo2` / 192.168.1.162 | Four-GPU success target; observed NIC MAC 00:e0:4c:53:9e:5e; HiveOS/Linux; i5-6500 reported in current campaign |
| DEV | Windows PowerShell 7 | SSH control and evidence collection; interface 192.168.1.88 in Oct 8 diagnosis |
| PiKVM | `pikvm` / 192.168.1.169 | Historical firmware HID/media control path for OCTO1 |
| Video1 | `video1` / 192.168.1.101 | Independent OCTO1 HDMI capture |
| Steward dashboard | DEV localhost:8785 | Control/status; status alone not proof of physical state |
| OCTO2 model API | 127.0.0.1:8080 on OCTO2 | `/health`, `/completion` |

Do not assume OCTO1's physical flash process, shell mappings or slot mapping is identical on OCTO2 without observation. OCTO2 SSH may work even when local video output is absent.

## 4. Candidate derivation: reproducibility-critical data
**Trusted stock full SPI image** (OCTO1 canonical historical source):
- Path `C:\Users\wille\Desktop\OCTOMINER1-BIOS-5.12-2021-09-18.bin`
- Size **8,388,608 bytes (8 MiB)**; SHA256 `52418F6A0DE6FD6A6C1C5CE90DC4FA9D6C4BBA910E09B79F2377B740CA857014`
- Descriptor full-file offset `0x000000–0x000FFF`
- ME `0x001000–0x1FFFFF`
- BIOS region `0x200000–0x7FFFFF`, length `0x600000 = 6,291,456 bytes`
- Stock BIOS-region SHA256 `372353AEF71055EC58AB413D2F197C1FA8A01EFADCFA59FC84A6668186D6489`.

**C1 full candidate:** `OCTOMINER1-C1-128G-UNFLASHED.bin`; size 8,388,608; SHA256 `1aa985e185a5eb2dbfcd732d38e75788244752565236f419e9c42860cae37741`. Published candidate historical branch `c1-128g-artifact`, path `docs/operations/octominer/firmware/candidates/OCTOMINER1-C1-128G-UNFLASHED.bin`, publication commit prefix `873dec55` (verify branch and artifact still exist).

**C1 BIOS-only payload:** `C1BIOS.BIN`, length 6,291,456; SHA256 `84406C847C5C2027217DB2DF81751C8E497887A7628E19935E02F2E602E55B21`. It is extracted from the full candidate at offset `0x200000` for length `0x600000`.

**Semantic firmware patch** (offsets are *within the extracted PciHostBridge module*, NOT full-SPI offsets):
- PciHostBridge +`0x1275`: `0x10 → 0x20`
- PciHostBridge +`0x128C`: `0x10 → 0x20`
- PciHostBridge +`0x12CD`: `0x10 → 0x20`
- PciBus threshold **unchanged**.
- Target high MMIO aperture **[128 GiB, 256 GiB)** = `0x2000000000–0x3fffffffff` inclusive, 128 GiB.
- C1 offline structural validation recorded PASS. **Do not patch these numeric module-relative offsets directly into an 8-MiB SPI file.** Reproduce by identifying the exact PciHostBridge firmware volume/module in the trusted stock image, reproducing the original extraction/rebuild toolchain, checking three original bytes, editing the extracted module, rebuilding firmware with correct firmware-volume integrity/length checks, and matching the **entire full-image and BIOS-region SHA256 above**. The present documentation does not establish the exact module extraction/reinsertion command-line invocation, tool versions or absolute SPI offsets for the three edits; locate the original campaign transaction/build artifacts before asserting byte-for-byte reproducibility. Hash-match is the decisive criterion; do not invent missing build commands.
- OCTO1 transaction: `A:\Riverview\SNAIL-qualification\runtime\snail\transactions\C1-128G-20261007-101441` (`C1BIOS.BIN`, `prewrite-evidence.txt`, `transaction.json`); staged candidate `A:\Riverview\SNAIL-qualification\runtime\snail\staging\OCTOMINER1-C1-128G-UNFLASHED.bin`.
- Campaign worktree `T:\OctoMiner_BIOS_Campaign\repo`; runtime `T:\OctoMiner_BIOS_Campaign\workspace\campaign-runtime`; SNAIL worktree `A:\Riverview\SNAIL-qualification`.

**Historical failed high-aperture experiment:** PciHostBridge +0x1275/+0x128C/+0x12CD and PciBus +0x6F78 all changed `0x10→0x60`; 384-GiB window from 128 to 512 GiB led to unacceptable boot behavior despite programmed/readback firmware. C1 changed only three host-bridge values and kept PciBus unchanged.

## 5. Qualified EFI FPT tooling and preparation
- `Fpt.efi` Intel Flash Programming Tool 11.8.65.3606, 4,076,800 bytes, SHA256 `01BE50081142F2314AAB4366AB2A20AC6C3D1A7879A92003897EF78BC30E8001`.
- `fparts.txt`, 15,153 bytes, SHA256 `77A5A9A384E29F907714D31069A558203DCFEA30486A7E6D2D1BDDD813CABEB4`.
- x64 UEFI `EFI/BOOT/BOOTX64.EFI`, 938,880 bytes, SHA256 `50437F8F0623A076F350AE937B0054F5912A14BBF9948C9665CA6AE4B0F31E7A`.
- FPT identified flash `MX25L6473E`, ID `0xC22017`, 8192 KB, on OCTO1.
- Physical SanDisk `Cruzer Switch` OCTO1 execution media: /dev/sdb, partition /dev/sdb1 vfat, label OCTOV3, UUID 5CA8-E207, USB 0781:5572. It contained qualified FPT/fparts/C1BIOS. `startup.nsh` was renamed `startup.nsh.DISABLED` to prevent uncommanded writes.
- In OCTO1 boot menu F11, select `UEFI: SanDisk Cruzer Switch 1.27, Partition 1`; historical UEFI mapping `FS0:` was SanDisk. **Revalidate FS mapping each boot**; do not assume FS0.
- Manual UEFI commands for a deliberate *authorized, preflight-verified* BIOS-region-only transaction:
  ```text
  fs0:
  cd \
  Fpt.efi -bios -d CURRENT.BIN
  Fpt.efi -f C1BIOS.BIN -bios
  Fpt.efi -bios -d VERIFY.BIN
  ```
  Verify that `CURRENT.BIN` and `VERIFY.BIN` do not overwrite forensic originals, and compare readback after accounting for mutable firmware/NVRAM bytes. **Never write the 8-MiB full image using a BIOS-only FPT command; never overwrite descriptor/ME for this experiment.** Never automatically execute these commands via startup.nsh. Confirm image, hashes, target machine, stable power, physical recovery plan and rollback authority before starting.
- Proven stock rollback *only when UEFI shell is reachable*: `Fpt.efi -f STOCKBIOS.BIN -bios`; then independent `Fpt.efi -bios -d STOCKVERIFY.BIN`. No pre-POST external recovery was proven for OCTO1 as of the Oct 7 incident.

## 6. OCTO1 October 7 failure — separate from OCTO2
- FPT recognized descriptor and MX25L6473E, entered BIOS-region erase/program, visible last erase around `0x2E7000` at ~18%; **no success/completion was captured**.
- Video disappeared; ping/SSH to OCTO1 failed; one physical reset did not restore POST/video/USB. **OCTO1_C1_RESULT=INDETERMINATE_FLASH_INTERRUPTED_BEFORE_VERIFIED_COMPLETION**.
- Root cause of interruption not proven. Possible watchdog/power/other event; do not claim a defective C1 patch from this.
- No established blind USB or external SPI recovery procedure. Before any external write: identify chip and voltage, obtain two consistent SPI reads and hashes, preserve original failed image, compare stock/C1 and only then plan recovery.
- Detailed media image/PiKM history, commands, HID transport failures and precise OCTO1 timeline are in the dedicated OCTO1 incident document. Avoid duplicating its misleading title “BAD FLASH” as “BAD C1”.

## 7. OCTO2 October 8 verified C1 firmware and 3-GPU control
- C1 BIOS-only FPT write on OCTO2 completed with immediate FPT verification; HiveOS booted. Exact full flash console log not embedded in this dossier.
- OCTO2 readback comparison to expected image had **786 differing bytes**, suspected mutable state, **not proved**; archive exact offsets/dumps before asserting all code bytes match. Immediate FPT verification and functioning boot are recorded; readback is not claimed byte-identical.
- `dmesg` showed high root bus resource `[mem 0x2000000000-0x3fffffffff window]` (128 GiB). **No pre-C1 same-machine aperture measurement available**, so do not assert delta proved solely by before/after logs.
- CPU test `/root/octominer-pi-15s.py`, SHA256 `543464ff9b5646f6133c1d058e68ba3394cc627cc32498ced449bf55a99e07c0`, Chudnovsky 6000 digits: pre 14.161248 s, C1 14.167809 s (no meaningful regression).
- 4090 + 2×P100: GPU enumeration, 16-GiB BAR1 each P100 and 256-MiB BAR1 4090, 80B model loaded, two completions using identical request. Run1 209 generated tokens / 44.002389668238905 tok/s / wall 5.466 s / prompt 31.38 tok/s; Run2 209 tokens / 44.69880740143483 tok/s / wall 5.483 s / prompt 46.35 tok/s. Older informal 49–50 tok/s figure is not directly comparable.

## 8. Four-GPU cold-add, boot, reboot, recovery
- Steward cold-shutdown, unplugged AC and added third P100: **4090 + 3×P100 = four GPUs, 72 GiB aggregate VRAM**.
- 2026-10-08 ~19:13 EDT: `nvidia-smi -L` all four UUIDs:
  - GPU0 P100 `GPU-c0c253d2-ff9e-3121-f1f1-ba4990420a8c`
  - GPU1 RTX4090 `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2`
  - GPU2 P100 `GPU-7b1a4d4b-8593-d3b7-6cf9-480ff81ea013`
  - GPU3 P100 `GPU-6785b322-899d-8eec-e817-31d83279a414`
- 19:16 `nvidia-smi` showed llama-server PID 784 allocated memory on all four: 10,550 / 16,677 / 10,554 / 9,416 MiB respectively. API initially `503 Loading model`. Local video output missing while SSH initially worked; do not conflate video with boot failure.
- At 19:18:50 an SSH benchmark attempt timed out (192.168.1.162:22). **Actual reboot confirmed**: later boot ID `b98f8a1c-1cc3-4a57-8c7c-189c82c01bac`, boot time **19:19:56 EDT**; earlier dashboard boot ID `00b68fa3-2b54-41a7-a0ce-8f619dbcaa8e`. Cause unknown; no previous boot journal existed.
- At 19:21:27 ping 4/4, SSH TCP22 true, API TCP8080 true; OCTO2 MAC `00-e0-4c-53-9e-5e`.
- Persistent journaling enabled ~19:23 using:
  ```sh
  mkdir -p /var/log/journal
  mkdir -p /etc/systemd/journald.conf.d
  printf '[Journal]\nStorage=persistent\nSystemMaxUse=200M\n' > /etc/systemd/journald.conf.d/90-octo-persistent.conf
  systemctl restart systemd-journald
  journalctl --flush
  ```
  Verification: 8.0 MiB journal storage; `journalctl --list-boots` displayed current boot only. **Future** reboot logs may persist; abrupt hardware loss may still leave no final diagnostic.
- 19:27:48 30-sec `nvidia-smi` thermal sampling: P100s ~34/34/49°C at end, 4090 37°C; 4090 fan 50%; all `hw_thermal_slowdown=Not Active`; GPU memory used 11424 / 17763 / 11308 / 10274 MiB; GPU utilization idle at sampling. `/health` returned `{"status":"ok"}`.
- 19:29:10 two-pass four-GPU completion success. Run1 196 generated tokens, 40.02408012861892 tok/s, wall 5.701 s, prompt 27.916415823509993 tok/s; Run2 196 tokens, 40.81094486755279 tok/s, wall 5.710 s, prompt 41.555100256196226 tok/s. Same request settings as 3-GPU baseline; **output token counts differ (209 vs 196)**, so direct percentage speed comparison is indicative, not controlled enough to attribute causation solely to GPU count. Four-GPU second run ~8.7% slower than three-GPU second run.
- Loading takes approximately 365–380 seconds in prior observation; `503 Loading model` during this interval is not itself failure.

## 9. Exact inference reproducibility request
```json
{"prompt":"Explain the difference between PCIe MMIO address space and physical GPU VRAM in approximately 150 words.","n_predict":250,"temperature":0,"cache_prompt":false}
```
POST `http://127.0.0.1:8080/completion`, Content-Type application/json. Record `tokens_predicted`, `timings.predicted_per_second`, `timings.prompt_per_second`, wall time, output, boot ID, GPU UUIDs, service process and context configuration. Run twice after `/health` reports `{"status":"ok"}`. This is a smoke/performance test, not a long-duration stability qualification.

## 10. Exact 4-GPU PCIe/BAR audit (2026-10-08 19:31:31 EDT)
Root high window: `0x2000000000–0x3fffffffff`, 128 GiB.
```text
BDF             GPU       BAR0 32-bit      BAR1 64-bit prefetchable     BAR3 64-bit prefetchable     Link
0000:01:00.0    P100      de000000 16M     3800000000 16G             3c00000000 32M             Gen1 x16
0000:02:00.0    RTX4090   da000000 16M     3c20000000 256M           3c30000000 32M             Gen1 x1 downgraded
0000:04:00.0    P100      dd000000 16M     3000000000 16G             3400000000 32M             Gen1 x1 downgraded
0000:05:00.0    P100      dc000000 16M     2800000000 16G             2c00000000 32M             Gen1 x1 downgraded
```
GPU BAR1 total 48.25 GiB; BAR3 4×32 MiB = 0.125 GiB; **GPU high BAR total 48.375 GiB**, excluding other reservations/bridge rounding. Earlier chat rounded to 48.34 GiB; use exact 48.375 GiB. Arithmetic 128 - 48.375 = 79.625 GiB not allocated to those GPU BARs; **NOT** a measured usable contiguous hole. Additional BARs, bridge windows and 16-GiB alignment must be checked before any capacity claim.

**Known audit bug:** A prior Python `/proc/iomem` parser filtered by indentation `depth != 1` and reported `ALLOCATED_GIB=0`, `UNALLOCATED_GIB=128`, `UTILIZATION=0%`. **FALSE**: the BAR addresses above prove usage. Do not reuse that parser or trust its percentage. Use `lspci -Dnn`, `lspci -vv -s BDF`, `/sys/bus/pci/devices/*/resource`, bridge prefetchable windows, and normalized interval-union accounting. On some systems `/proc/iomem` redacts addresses for unprivileged processes. High GPU BAR ranges may overlap bridge reservations: count each address only once. Note GPU BARs and bridge windows separately.

## 11. Recommended next five-GPU test — not yet performed
Steward physically powers down and installs **fourth P100**, making **RTX4090 + 4×P100 = five GPUs, 88 GiB aggregate VRAM**. Do not claim successful enumeration yet.
1. Observe boot and note video/no-video, POST delay, fan behavior and network reachability. Allow 6–7 minutes for normal model loading after successful OS boot; do not mistake `503 Loading model` for crash.
2. Record exact `date -Is`, `uptime -s`, `/proc/sys/kernel/random/boot_id`, `journalctl --list-boots`, `journalctl -b -1 -p warning` when present; preserve any reboot forensic logs before stress.
3. `lspci -Dnn | grep -Ei '(VGA compatible controller|3D controller).*NVIDIA'`; `nvidia-smi -L`; compare UUIDs and BDFs to four-GPU baseline; inspect `dmesg` for BAR allocation failures and NVIDIA Xid (do not mistake Realtek r8169 XID 2c9 for NVIDIA Xid).
4. `lspci -vv -s <BDF>` for each GPU; capture BAR1/3 base and size, link width, upstream bridges, `/sys/bus/pci/devices/<BDF>/resource`, and root window. Do not infer 5th BAR assignment from free arithmetic alone.
5. Verify NVIDIA memory allocation and temperatures; then `curl -sS --max-time 10 http://127.0.0.1:8080/health` and two identical inference requests only after READY.
6. Conduct separately authorized extended stability test, capture logs and reboot ID transitions. One prior unexplained reboot is a known risk.
7. Classify separately: firmware POST, OS boot, GPU enumeration, BAR allocation, driver init, workload, stability. Preserve exact evidence. No new BIOS flash needed for the physical fifth-GPU experiment unless observations demand a new candidate and it passes the campaign's authorization process.

## 12. PowerShell/automation practices
Operator prefers complete PowerShell 7 blocks, `$Result = @()`, `$Result | Set-Clipboard`, full output and no `else` or `throw` in campaign scripts. SSH is via alias `octo2`; remote heredoc scripts are passed through PowerShell single-quoted here-strings `@' ... '@`. Record timestamps, command exit codes, hashes, boot IDs and outputs. Avoid repeated uncontrolled resets. Do not confuse command acceptance with observed hardware effect.

Historical OCTO1 PiKVM HID:
`T:\OctoMiner_BIOS_Campaign\repo\controller\Send-PiKVMKeys.ps1`; text via POST `/hid/print?text=...`; key via POST `/hid/events/send_key?key=...` (key in URL query, not POST body). `fs0:` was once visually received as `s0:`; visual confirmation required. Historic video relay `T:\OctoMiner_BIOS_Campaign\repo\controller\video1_relay.py`; latest frame `T:\OctoMiner_BIOS_Campaign\repo\runtime\video1\latest.jpg`. These are **OCTO1 historical details**, not proof that same paths are live now.

## 13. Unresolved / do not silently fill gaps
- Precise original firmware module extraction/repack tools and commands, absolute full-SPI patch offsets, and complete OCTO2 FPT console output: **not in this evidence packet**; recover transaction artifacts to make bit-for-bit rebuild independently reproducible.
- OCTO2 786-byte readback delta: exact bytes and reasons unknown; mutable firmware state suspected, not verified.
- Which component caused OCTO2 ~19:19 unexpected reboot: unknown (power, watchdog, GPU/PCIe, kernel, driver, etc.). Persistent journal was enabled only *after* that reboot.
- Four-GPU local video missing, while SSH/API worked; cause unknown.
- Why third P100 was ~15°C hotter at idle: unknown; not throttling at observed sample.
- 4090 x1 Gen1 and two P100 x1 Gen1 links are measured; avoid attributing throughput loss solely to PCIe without controlled tests.
- Exact fifth-GPU slot/topology, five-GPU BAR allocations and stability: **not yet observed**.
- OCTO1 hardware recovery remains separate unresolved incident.

## 14. Handoff/acceptance checklist for successor AI
Read canonical requirements and process map, OCTO1 incident, stock recovery, this dossier, current SNAIL state/evidence, and most recent machine boot ID. Distinguish **verified** vs **reported** vs **hypothesized**. Never overwrite original firmware backups or forensic dumps. Before any new firmware write, independently validate hardware identity, full-image and BIOS-region hashes, module semantics, authorized rollback, and stable power. After every test preserve timestamped raw logs and promote facts into durable campaign state; don't treat chat context as durable authority.

**Checkpoint as of 2026-10-08 ~19:31 EDT:** OCTO2 C1 + 4090 + 3 P100: high root MMIO 128 GiB, four GPU BARs allocated, NVIDIA driver OK, Qwen 80B API READY and two completions PASS, one prior unexplained reboot, persistent journal enabled. Steward preparing physical installation of fourth P100 (fifth GPU total). **Await next physical observation.**
