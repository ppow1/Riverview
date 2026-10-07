# OCTOMINER1 C1 BAD FLASH — FULL POST-MORTEM AND RECOVERY HANDOFF — 2026-10-07

> **AI / FUTURE SESSION START HERE**
>
> Search terms: **OctoMiner, OCTO1, C1, C1-128G, bad flash, interrupted BIOS, no POST, MX25L6473E, FPT, P100, PiKVM, PiKM, Video1, recovery**.
>
> This is the Riverview durable handoff for the 2026-10-07 OCTO1 C1 firmware incident. It is intentionally self-contained so a future AI conversation can reconstruct the campaign state without relying on prior chat memory.
>
> Status: **OCTO1 NO-POST / C1 RESULT INDETERMINATE / RECOVERY REQUIRED**
>
> Canonical duplicate also exists in repository `ppow1/OctoMiner_BIOS_Campaign` at:
> `INCIDENTS/OCTO1_C1_FLASH_INTERRUPTION_POSTMORTEM_2026-10-07.md`

# OCTO1 C1-128G Flash Interruption Post-Mortem — 2026-10-07

Status: **OCTO1 NO-POST / C1 RESULT INDETERMINATE / RECOVERY REQUIRED**

Purpose: preserve the complete operational state, evidence, paths, hashes, commands, mistakes, and exact continuation point so a future session can resume without rediscovery.

## 1. Executive conclusion

OCTO1 reached the x64 UEFI shell from the physical SanDisk recovery medium and manually started:

```text
Fpt.efi -f C1BIOS.BIN -bios
```

Intel FPT 11.8.65.3606 recognized the SPI flash as MX25L6473E, read the 6 MiB BIOS region, and visibly entered erase/program cycles. The last observed screen showed an erase operation at approximately 18% for a flash block around `0x2E7000`. The display subsequently disappeared before an FPT completion/success message was observed.

Afterward:
- Video1 showed no HDMI signal.
- OCTO1 did not answer ping at 192.168.1.160.
- SSH to alias `octo1` timed out.
- One physical reset was performed.
- No POST/video returned.
- Keyboard/USB initialization did not appear to occur.

Therefore the C1 experiment is **not a valid C1 firmware pass/fail result**. The candidate may have been only partially programmed. Current state is consistent with an interrupted BIOS-region write / soft-bricked SPI contents, but that remains a diagnosis to verify by direct SPI read if pre-POST recovery is unavailable.

Do not classify C1 as BAD. Classify it:
`C1_RESULT=INDETERMINATE_FLASH_INTERRUPTED_BEFORE_VERIFIED_COMPLETION`.

## 2. Campaign goal and C1 scope

North Star: stable multi-P100 operation on OCTOMINER1, ultimately 10+ Tesla P100 16 GB if platform limits permit, while retaining practical stock-equivalent boot behavior.

C1 was intentionally a small MMIO aperture experiment:
- Candidate: `OCTOMINER1-C1-128G-UNFLASHED.bin`
- Full image size: 8,388,608 bytes
- Full SHA256: `1aa985e185a5eb2dbfcd732d38e75788244752565236f419e9c42860cae37741`
- BIOS-region SHA256: `84406c847c5c2027217db2df81751c8e497887a7628e19935e02f2e602e55b21`
- Semantic changes: PciHostBridge PE offsets `0x1275`, `0x128c`, `0x12cd`, each byte `0x10 -> 0x20`
- PciBus threshold unchanged
- Intended high aperture: [128,256) GiB
- Offline structural validation: PASS

C1 test intent after a verified write: prove 3 P100, then 4 P100, with the same firmware.

## 3. Authoritative machine identities and roles

Physical OCTO1:
- Management MAC: `00:e0:4c:6b:05:a9`
- Management IP: `192.168.1.160`
- SSH alias: `octo1`
- Board: OCTOMINER X12 Ultra / Ver:1.52
- Chipset: Intel B250
- CPU: Intel Core i5-6500
- RAM: 16 GiB
- OCTO1 SSH is an OS diagnostic/control path only; it is not required for firmware control.

Other aliases:
- `octo2` -> root@192.168.1.162
- `video1` -> pi@192.168.1.101
- `pikvm` -> root@192.168.1.169

Control path:
`DEV/SNAIL -> SSH pikvm -> KVMD/PiKM USB HID -> OCTO1`

Media path:
`DEV/SNAIL -> SSH pikvm -> KVMD MSD -> PiKM USB gadget -> OCTO1`

Independent observation:
`OCTO1 HDMI -> video1 -> /dev/video0 -> ffmpeg -> DEV latest.jpg`

## 4. Authoritative Windows / project locations

Campaign repository:
`T:\OctoMiner_BIOS_Campaign\repo`

Campaign workspace runtime:
`T:\OctoMiner_BIOS_Campaign\workspace\campaign-runtime`

SNAIL campaign runtime:
`T:\OctoMiner_BIOS_Campaign\repo\runtime\snail`

Riverview/SNAIL qualification worktree:
`A:\Riverview\SNAIL-qualification`

Python:
`C:\Python314\python.exe`

Video relay:
`T:\OctoMiner_BIOS_Campaign\repo\controller\video1_relay.py`

Latest observation frame:
`T:\OctoMiner_BIOS_Campaign\repo\runtime\video1\latest.jpg`

FFmpeg:
`A:\AI\Tools\FFmpeg\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe`

FFplay:
`A:\AI\Tools\FFmpeg\ffmpeg-8.1.2-essentials_build\bin\ffplay.exe`

Campaign HID adapter:
`T:\OctoMiner_BIOS_Campaign\repo\controller\Send-PiKVMKeys.ps1`

Permanent PiKM UEFI media builder:
`T:\OctoMiner_BIOS_Campaign\repo\controller\build_pikm_uefi_media.py`

Qualified FPT directory:
`T:\OctoMiner_BIOS_Campaign\repo\runtime\recovery\qualified-fpt-11.8.65.3606`

C1 transaction:
`A:\Riverview\SNAIL-qualification\runtime\snail\transactions\C1-128G-20261007-101441`

C1 staged full candidate:
`A:\Riverview\SNAIL-qualification\runtime\snail\staging\OCTOMINER1-C1-128G-UNFLASHED.bin`

Canonical stock full SPI image:
`C:\Users\wille\Desktop\OCTOMINER1-BIOS-5.12-2021-09-18.bin`

## 5. Firmware and tool hashes

Canonical stock full SPI:
- size: 8,388,608
- SHA256: `52418F6A0DE6FD6A6C1C5CE90DC4FA9D6C4BBA910E09B79F2377B740CA857014`
- descriptor: 0x000000-0x000FFF
- ME: 0x001000-0x1FFFFF
- BIOS: 0x200000-0x7FFFFF
- BIOS-region length: 0x600000 / 6,291,456
- stock BIOS-region SHA256: `372353AEF71055EC58AB413D2F197C1FA8A01EFADCFA59FC84A6668186D6489`

Qualified FPT:
- file: `Fpt.efi`
- version: 11.8.65.3606
- size: 4,076,800
- SHA256: `01BE50081142F2314AAB4366AB2A20AC6C3D1A7879A92003897EF78BC30E8001`

Matching flash-parts database:
- file: `fparts.txt`
- size: 15,153
- SHA256: `77A5A9A384E29F907714D31069A558203DCFEA30486A7E6D2D1BDDD813CABEB4`

Qualified UEFI shell:
- `EFI/BOOT/BOOTX64.EFI`
- size: 938,880
- SHA256: `50437F8F0623A076F350AE937B0054F5912A14BBF9948C9665CA6AE4B0F31E7A`

C1 BIOS-region payload:
- file: `C1BIOS.BIN`
- size: 6,291,456
- SHA256: `84406C847C5C2027217DB2DF81751C8E497887A7628E19935E02F2E602E55B21`

## 6. C1 transaction evidence

Transaction ID:
`C1-128G-20261007-101441`

Transaction directory:
`A:\Riverview\SNAIL-qualification\runtime\snail\transactions\C1-128G-20261007-101441`

Important contents:
- `C1BIOS.BIN`
- `prewrite-evidence.txt`
- `transaction.json`

The BIOS payload was extracted from full-image offset `0x200000`, length `0x600000`.

At the pre-execution checkpoint, candidate construction and offline validation were complete and no firmware write had yet occurred.

## 7. PiKM virtual-media work completed before the incident

A deterministic 64 MiB MBR/FAT32 UEFI image format was qualified:
- MBR disk ID: `0x92D54F64`
- one bootable W95 FAT32 LBA partition
- partition start: sector 2048
- partition length: 129024 sectors
- FAT label: `PIKMUEFI`
- standard loader: `EFI/BOOT/BOOTX64.EFI`
- no `startup.nsh`

Previously qualified direct-boot image:
`OCTO1-PIKM-DIRECT-UEFI-20261007.img`
SHA256:
`ffee154b726e824fe0a79227485b1fbff622b088ca8bf948785a505fe75d8a37`

The initial C1 execution image `OCTO1-C1-128G-EXECUTION-SEAM.img` was rejected because it lacked FPT/fparts. Its SHA256 was:
`4268991a7dcc1631cfb58e7e395273ae4da6d42320dc27723d9a6095948b7dd0`

A corrected image was later built:
`/tmp/c1-fixed-20261007-132013/OCTO1-C1-128G-FIXED-20261007-132013.img`

PiKM storage path:
`/var/lib/kvmd/msd/OCTO1-C1-128G-FIXED-20261007-132013.img`

Corrected image:
- size: 67,108,864
- SHA256: `dc557d7b4d0626493c5107c7667f710998f77f927ebac9ba5af66bcacf36ce34`
- builder validation: PASS
- post-unmount verification: PASS
- required four files present
- `startup.nsh` absent

In HiveOS the PiKM medium enumerated as `/dev/sr0` / Optical Drive. Direct mounting of the partitioned disk image as `/dev/sr0` was not useful for the final execution path, so the known physical SanDisk was used instead.

## 8. Physical SanDisk execution medium

Device observed in HiveOS:
- disk: `/dev/sdb`
- size: 14.6G
- model: `Cruzer Switch`
- partition: `/dev/sdb1`
- filesystem: vfat
- label: `OCTOV3`
- UUID: `5CA8-E207`
- USB ID: `0781:5572 SanDisk Corp. Cruzer Switch`

The three execution files on the SanDisk were independently hashed:

```text
-rwxr-xr-x 1 root root 4076800 Apr  9  2020 /mnt/octov3/Fpt.efi
-rwxr-xr-x 1 root root   15153 Apr  9  2020 /mnt/octov3/fparts.txt
-rwxr-xr-x 1 root root 6291456 Oct  7 15:12 /mnt/octov3/C1BIOS.BIN

01be50081142f2314aab4366ab2a20ac6c3d1a7879a92003897ef78bc30e8001  /mnt/octov3/Fpt.efi
77a5a9a384e29f907714d31069a558203dcfea30486a7e6d2d1bddd813cabeb4  /mnt/octov3/fparts.txt
84406c847c5c2027217db2df81751c8e497887a7628e19935e02f2e602e55b21  /mnt/octov3/C1BIOS.BIN
```

The existing `startup.nsh` was renamed:
`startup.nsh.DISABLED`

This was critical because historical recovery media had contained FPT commands in startup.nsh.

Other historical files observed on the SanDisk:
- `V3BIOS.BIN`
- `CURRENT.BIN`
- `FPT-READ-SUCCESS.TXT`
- `INTERRUPTED-WRITE-STARTUP.NSH`
- `VERIFY.BIN`
- `STOCKBIOS.BIN`
- `STOCK-DONE.TXT`
- `STOCKVERIFY.BIN`
- `OLD-HEALTHY-BIOS-REGION.BIN`

## 9. Boot-menu and UEFI mapping evidence

F11 boot menu showed:
- `UEFI OS (P3: PNY CS900 120GB SSD)`
- `UEFI: SanDisk Cruzer Switch 1.27, Partition 1`
- `Enter Setup`

Successful SanDisk UEFI boot mapped:
- `FS0:` = `PciRoot(0x0)/Pci(0x14,0x0)/USB(0x5,0x0)/HD(1,MBR,0x00000000,0x800,0x1D1CFE0)`
- `FS1:` = SATA HiveOS EFI partition
- PiKM raw USB appeared as `BLK0` at `USB(0x1,0x3)` without a filesystem in that session.

UEFI shell displayed:
`Press ESC in 1 seconds to skip startup.nsh or any other key to continue.`

Because `startup.nsh` had been renamed, no startup script was intentionally executed.

## 10. HID adapter and exact interface

Canonical adapter:
`T:\OctoMiner_BIOS_Campaign\repo\controller\Send-PiKVMKeys.ps1`

It sends text through:
`POST /hid/print?text=<encoded>`

It sends keys through:
`POST /hid/events/send_key?key=<encoded>`

The key must be in the URL query string. An earlier attempt incorrectly sent `key=F11` in the POST body and received HTTP 400. That attempt did NOT send F11 and must never be repeated.

Known adapter usage:
```powershell
$Adapter = 'T:\OctoMiner_BIOS_Campaign\repo\controller\Send-PiKVMKeys.ps1'
& $Adapter -Key F11
& $Adapter -Key ArrowDown
& $Adapter -Key Enter
& $Adapter -Text 'fs0:' -Enter
```

Important: API success is not physical proof. Visual state is authoritative. One adapter text attempt intended as `fs0:` appeared visually as `s0:`, proving that text delivery can lose characters/timing even when the adapter returns success.

## 11. Reboot/UEFI entry sequence actually used

A proven software reboot from live HiveOS was:
```powershell
ssh octo1 'sync; systemctl reboot'
```

A prior reboot was physically verified by network transition and boot-ID change. Do not infer reboot solely from an SSH disconnect.

The successful automated UEFI-entry sequence used during this session was:

```powershell
$Adapter = 'T:\OctoMiner_BIOS_Campaign\repo\controller\Send-PiKVMKeys.ps1'
$Result = @()
$Result += ssh octo1 'sync; systemctl reboot' 2>&1
Start-Sleep -Seconds 3
1..18 | ForEach-Object {
    & $Adapter -Key F11 2>&1 | Out-Null
    Start-Sleep -Milliseconds 300
}
Start-Sleep -Milliseconds 700
$Result += & $Adapter -Key ArrowDown 2>&1
Start-Sleep -Milliseconds 400
$Result += & $Adapter -Key Enter 2>&1
Start-Sleep -Seconds 4
$Result += & $Adapter -Text 'fs0:' -Enter 2>&1
$Result | Set-Clipboard
```

Campaign PowerShell requirements:
- no `else` token
- no `throw`
- substantial probe output copied with `$Result | Set-Clipboard`
- avoid Format-List objects in `$Result`

The UEFI environment was time-sensitive. Waiting too long could allow the system to continue/exit and return to HiveOS.

## 12. Actual C1 write command and observed FPT output

The write command was manually entered in the UEFI shell:

```text
Fpt.efi -f C1BIOS.BIN -bios
```

Observed FPT output included:
```text
Intel (R) Flash Programming Tool. Version: 11.8.65.3606
Reading HSFSTS register... Flash Descriptor: Valid
Flash device: MX25L6473E    ID:0xC22017    Size: 8192KB (65536Kb)
GbE Region does not exist.
Reading Flash [0x0B00000] 6144KB of 6144KB - 100 percent complete.
```

Erase/program activity was visibly underway. Observed examples:
```text
Erasing Flash Block [0x206000] - 100 percent complete.
Programming Flash [0x206000] 8KB of 8KB - 100 percent complete.
Erasing Flash Block [0x213000] - 100 percent complete.
Programming Flash [0x213000] 12KB of 12KB - 100 percent complete.
Erasing Flash Block [0x219000] - 100 percent complete.
Programming Flash [0x219000] 16KB of 16KB - 100 percent complete.
```

Last known visible progress:
```text
Erasing Flash Block [0x2E7000] - 18 percent complete.
```

No final FPT success/completion line was captured.

## 13. Failure observation

After the write had visibly begun:
- HDMI output disappeared.
- Video1/capture reported looking for signal.
- No verified FPT completion was observed.
- The exact instant and cause of the transition are unknown.
- A watchdog/reset/power event is suspected as one possible cause but is NOT proven.

The post-flash survival check was:

```powershell
Clear-Host

$Result = @()
$Result += "========== OCTO1 POST-FLASH SURVIVAL CHECK =========="
$Result += "TIME=$(Get-Date -Format o)"
$Result += ""

$Result += "=== NETWORK ==="

1..10 | ForEach-Object {
    $Ping = Test-Connection 192.168.1.160 -Count 1 -Quiet -TimeoutSeconds 1
    $Result += "PING_$($_)=$Ping"
    Start-Sleep -Seconds 1
}

$Result += ""
$Result += "=== SSH ==="

$SSH = ssh -o ConnectTimeout=3 -o BatchMode=yes octo1 'echo SSH_ALIVE; hostname; cat /proc/sys/kernel/random/boot_id; uptime; lspci | grep -i -E "NVIDIA|VGA|3D" || true' 2>&1

$Result += $SSH
$Result += "SSH_EXIT=$LASTEXITCODE"

$Result += ""
$Result += "NO_RESET_SENT=True"
$Result += "NO_POWER_CYCLE_SENT=True"
$Result += "NO_FURTHER_FLASH_COMMAND_SENT=True"

$Result | ForEach-Object { Write-Host $_ }
$Result | Set-Clipboard
```

Observed result at 2026-10-07T15:25:42.5412584-04:00:
```text
PING_1=False
PING_2=False
PING_3=False
PING_4=False
PING_5=False
PING_6=False
PING_7=False
PING_8=False
PING_9=False
PING_10=False

ssh: connect to host 192.168.1.160 port 22: Connection timed out
SSH_EXIT=255
```

At that point no reset/power cycle/additional flash command had been sent.

One physical reset was then performed. Result:
- no video output
- no POST observed
- keyboard did not appear alive
- network did not recover

No further reset or power-cycle should be used as a substitute for firmware recovery.

## 14. Previously proven stock recovery procedure

Historical stock recovery was successful when the machine could still reach the x64 UEFI shell.

Read-only dump:
```text
fs0:
cd \
Fpt.efi -bios -d CURRENT.BIN
```

Intentional stock BIOS-region recovery:
```text
fs0:
cd \
Fpt.efi -f STOCKBIOS.BIN -bios
```

Independent readback:
```text
fs0:
cd \
Fpt.efi -bios -d STOCKVERIFY.BIN
```

Descriptor and ME were deliberately not written. BIOS-region-only recovery was the proven method.

Current problem: OCTO1 presently does not POST far enough to reach UEFI, so the proven EFI/FPT rollback cannot currently execute.

## 15. Current recovery boundary

The campaign records do NOT establish a proven:
- pre-POST blind USB recovery,
- board recovery jumper procedure,
- dual-BIOS fallback,
- external SPI programmer procedure for this exact board.

Do not invent one.

Next recovery investigation must first establish the board-level SPI recovery interface:
1. identify the physical MX25L6473E package and board location;
2. identify any SPI header / service header / recovery jumper / socket;
3. determine whether the chip can safely be read/programmed in-circuit;
4. identify voltage and programmer requirements from authoritative component/board evidence;
5. before any external write, read the chip at least twice and hash/compare the dumps;
6. preserve the failed-flash dump as forensic evidence;
7. compare it against stock BIOS region and C1 BIOS region to determine how far the interrupted write progressed;
8. only then construct the minimum stock restoration operation.

Do not buy hardware until the required interface/programmer is identified.

## 16. Process failure / lessons learned

This incident was not merely a firmware experiment failure. It exposed a workflow defect.

The UEFI execution environment was known to be time-sensitive, but the final flash transaction was split across conversational turns and required manual typing after the machine had already entered the critical execution window.

The campaign had already qualified:
- remote reboot into firmware,
- F11 boot-menu entry,
- boot-device selection,
- UEFI shell,
- HID key delivery,
- HID text delivery,
- C1 payload hashes,
- FPT and fparts hashes,
- observation through Video1.

Therefore future write attempts must be structured so **all authorization, hashes, target identity, rollback material, and exact transaction text are resolved before rebooting into the time-sensitive firmware environment**.

If a human action is required by an external policy boundary, that human action must occur before the critical timed sequence whenever possible. Do not introduce a conversational wait at the UEFI prompt.

Do not equate an automation/policy limitation with a technical limitation of the machine. The HID transport was technically capable of typing commands.

Do not use API acceptance as evidence of physical key/text delivery. Observe the target.

Do not classify a candidate as failed unless:
- the complete candidate write was verified,
- readback was verified where feasible,
- and the resulting boot behavior was observed.

For this incident:
`C1_RESULT=INDETERMINATE`
`FLASH_WRITE_COMPLETION=UNVERIFIED`
`CURRENT_MACHINE_STATE=NO_POST`
`LIKELY_RECOVERY_CLASS=SPI_FIRMWARE_RECOVERY`

## 17. Exact continuation point for a future session

A future session must NOT rediscover PiKM, Video1, FPT, the UEFI shell, the C1 candidate, or the C1 transaction.

Start here:

1. Read this post-mortem.
2. Read `PROVEN_FACTS.md`.
3. Read the historical `OCTOMINER1_FPT_EFI_BIOS_RECOVERY_AND_MULTI_P100_MMIO_PLAN_2026-09-14.md`.
4. Confirm OCTO1 remains no-POST without repeatedly resetting it.
5. Investigate the physical X12 Ultra SPI recovery interface for the identified MX25L6473E.
6. Preserve the existing flash contents before any recovery write.
7. Restore known-good stock firmware using the least invasive proven/qualified method available.
8. Verify POST, HiveOS, SSH, CPU/RAM, and baseline behavior.
9. Only after recovery, redesign C1 execution as one uninterrupted transaction.
10. Re-run C1; do not count the 2026-10-07 interrupted attempt as a C1 firmware failure.

## 18. Durable references

Repository:
`ppow1/OctoMiner_BIOS_Campaign`

Primary durable campaign facts:
`PROVEN_FACTS.md`

Historical recovery source:
`A:\Riverview\SNAIL-qualification\docs\operations\octominer\OCTOMINER1_FPT_EFI_BIOS_RECOVERY_AND_MULTI_P100_MMIO_PLAN_2026-09-14.md`

C1 published artifact:
branch `c1-128g-artifact`
path `docs/operations/octominer/firmware/candidates/OCTOMINER1-C1-128G-UNFLASHED.bin`
publication commit prefix `873dec55`

## 19. Verification checklist for this post-mortem

Cross-checked against:
- current GitHub `PROVEN_FACTS.md`;
- C1 media-builder defect inspection and source-hash reconfirmation;
- durable HID adapter source and Hermes bridge references;
- historical FPT EFI recovery plan;
- observed SanDisk file hashes;
- observed UEFI mapping and boot-menu state;
- observed FPT write screen;
- post-failure ping/SSH survival probe;
- post-reset physical no-video/no-keyboard observation.

Known uncertainty is intentionally preserved rather than filled in:
- exact cause of the display/system disappearance during FPT;
- whether a watchdog caused the interruption;
- exact percentage of the entire BIOS-region transaction completed;
- whether C1 would POST if fully programmed;
- exact board-level pre-POST recovery mechanism.

END OF POST-MORTEM

