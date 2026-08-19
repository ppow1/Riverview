# Hard Drive Erasure / Sanitization Investigation

**Date:** 2026-08-19  
**Purpose:** Durable reference for the Riverview workstation storage-erasure investigation.  
**Search terms for future retrieval:** hard drive analysis, hard drive erasure investigation, drive sanitization, SSD secure erase, NVMe crypto erase, SATA secure erase, UPS erase window, Bestoss GM528, Kingston Q500, SPCC SSD, WD WDS100T2B0B, Toshiba MG04ACA400NY.

> IMPORTANT: This document records an investigation and planning estimates. No drive was erased during the investigation. Timing estimates that were not reported by the drive are explicitly labeled as planning estimates rather than guarantees.

## Executive summary

The workstation has five drives: four solid-state drives and one 4 TB 7200-RPM mechanical HDD. The investigation focused on whether the SSDs could be securely sanitized within a short UPS-backed power window, and what method/time would apply to the mechanical HDD.

The strongest result is the Bestoss GM528 2 TB NVMe. Its controller explicitly advertises NVMe Crypto Erase Sanitize and Block Erase Sanitize. Overwrite Sanitize is not supported. It also advertises cryptographic erase through Format NVM. The drive does not publish an estimated completion time for any sanitize operation. Based on the nature of cryptographic erase, a completion time in seconds to under a minute is a reasonable planning expectation, but it is NOT a drive-reported or measured guarantee. For system planning, a one-minute allowance was considered reasonable pending an actual timed test on expendable/equivalent hardware.

The three SATA SSDs expose ATA Security but were observed in the `Disabled, frozen` state under the running Windows system. We did not obtain authoritative drive-reported Secure Erase completion times for these three devices. Planning allowances discussed were 10 minutes for the SPCC 120 GB, 10 minutes for the Kingston Q500 240 GB, and 15 minutes for the WD 1 TB SATA SSD. These are conservative engineering allowances, NOT measured values or manufacturer guarantees. A 25-minute UPS-backed window therefore appears likely to be sufficient for the SSD group, particularly if independent erase operations can be initiated in parallel, but this must not be treated as proven until the SATA SSD erase behavior/timing is validated.

The Toshiba 4 TB 7200-RPM HDD reports ATA Security as unavailable in smartctl. Therefore the investigation did not establish ATA Secure Erase as an available retirement method for that disk. If no other firmware sanitize mechanism is found, the dependable fallback is a full-device overwrite, which should be planned in hours rather than minutes. Its SMART extended-test recommendation is 452 minutes (~7.5 hours), which provides useful scale for a full platter traversal but is not itself an overwrite-time measurement.

## Confirmed drive inventory

| Device | Model | Capacity/type | Investigation result |
|---|---|---|---|
| `/dev/sda` | SPCC Solid State Disk | 120 GB SATA SSD | ATA Security present; Disabled, frozen |
| `/dev/sdb` | KINGSTON SQ500S37240G | 240 GB SATA SSD | ATA Security present; Disabled, frozen |
| `/dev/sdc` | TOSHIBA MG04ACA400NY | 4 TB 7200-RPM SATA HDD | ATA Security reported unavailable |
| `/dev/sdd` | WDC WDS100T2B0B-00YS70 | 1 TB M.2 SATA SSD | ATA Security present; Disabled, frozen; this was the Windows boot/system disk during investigation |
| `nvme0n1` / `\\.\PhysicalDrive4` | Bestoss GM528 2TB | 2 TB NVMe SSD | NVMe Crypto Erase and Block Erase Sanitize supported |

## Bestoss GM528 2 TB NVMe findings

Identity observed through nvme-cli:

- Model: `Bestoss GM528 2TB`
- Serial: `UB528K5S263ON00048`
- Firmware: `SVN22817`
- NVMe version reported by Identify Controller: 2.0 (`ver 0x20000`)
- Windows nvme-cli device: `nvme0n1`
- Generic Windows path: `\\.\PhysicalDrive4`
- Controller vendor ID observed: `0x1e4b` (associated in research with Maxio Technology; controller-family inference should not substitute for the actual Identify data above)

Key Identify Controller fields:

- `sanicap = 0x40000003`
  - Crypto Erase Sanitize: SUPPORTED
  - Block Erase Sanitize: SUPPORTED
  - Overwrite Sanitize: NOT SUPPORTED
- `fna = 0x4`
  - Cryptographic erase is supported as part of Secure Erase / Format NVM.
- `oacs = 0x17`
  - Format NVM is supported.

Read-only sanitize-log results:

- Sanitize Progress (SPROG): `65535`
- Sanitize Status (SSTAT): `0`
- Estimated overwrite time: `4294967295` = no time period reported
- Estimated block erase time: `4294967295` = no time period reported
- Estimated crypto erase time: `4294967295` = no time period reported
- No-deallocate variants likewise reported no time period.

Therefore the drive itself gives NO numerical sanitize-time estimate. The sub-minute crypto-erase expectation is an engineering planning inference, not firmware telemetry.

## SATA SSD findings

### SPCC 120 GB SATA SSD

- Model: SPCC Solid State Disk
- SATA SSD
- ATA Security observed as: `Disabled, frozen [SEC2]`
- Secure-Erase timing was not successfully extracted during this investigation.
- Planning allowance discussed: approximately 10 minutes.
- This 10-minute value is NOT a measured or drive-reported figure.
- Separate SMART inspection showed historical uncorrectable/read errors; do not infer drive health merely from an overall SMART PASSED result.

### Kingston Q500 240 GB SATA SSD

- Model: `KINGSTON SQ500S37240G`
- Firmware observed: `S3501103`
- Capacity: 240,057,409,536 bytes
- ATA Security observed as: `Disabled, frozen [SEC2]`
- Secure-Erase timing was not successfully extracted.
- Planning allowance discussed: approximately 10 minutes.
- This 10-minute value is NOT a measured or drive-reported figure.

### WD 1 TB M.2 SATA SSD

- Model: `WDC WDS100T2B0B-00YS70`
- Firmware observed: `X61190WD`
- Capacity: 1,000,204,886,016 bytes
- Form factor: M.2
- Interface is SATA, NOT NVMe.
- ATA Security observed as: `Disabled, frozen [SEC2]`
- Secure-Erase timing was not successfully extracted.
- Planning allowance discussed: approximately 15 minutes.
- This 15-minute value is NOT a measured or drive-reported figure.
- This drive was the Windows boot/system disk during the investigation, so an eventual erase cannot be performed while continuing to boot Windows from that same drive; retirement would require booting from another environment/device.

### Meaning of `frozen`

For the three SATA SSDs, `frozen` is a security state imposed by the host/firmware to prevent unexpected ATA security changes while the system is running. It does not by itself mean the SSD lacks Secure Erase support. Any future retirement procedure must deliberately handle the frozen state and re-confirm exact device identity immediately before issuing destructive commands.

## Toshiba MG04ACA400NY 4 TB HDD findings

- Model: `TOSHIBA MG04ACA400NY`
- Firmware observed: `FK5D`
- Capacity: 4,000,787,030,016 bytes
- 3.5-inch, 7200 RPM, SATA 6 Gb/s
- ATA Security reported by smartctl as: `Unavailable`
- SMART extended self-test recommended polling time: 452 minutes (~7.5 hours)

The investigation therefore did not establish ATA SECURITY ERASE as available for this particular drive/firmware/path. Unless another supported sanitize mechanism is subsequently discovered, plan on a full-device overwrite for retirement. That means HOURS rather than a 25-minute UPS window. The 452-minute SMART-test figure is only an indication of full-surface traversal scale; it is not an erase-time guarantee.

## UPS / power-loss planning conclusion

The engineering question considered was whether a UPS capable of sustaining the machine for at least 25 minutes could plausibly provide enough time to sanitize all SSDs after loss of mains power.

Current conclusion:

- Bestoss NVMe: very likely well inside 25 minutes; crypto erase is expected to be the fastest mechanism and a sub-minute completion is plausible, but unmeasured on this exact drive.
- SPCC 120 GB SATA SSD: 25 minutes is likely ample based on the current 10-minute planning allowance, but timing is not proven.
- Kingston Q500 240 GB SATA SSD: 25 minutes is likely ample based on the current 10-minute planning allowance, but timing is not proven.
- WD 1 TB SATA SSD: 25 minutes is likely ample based on the current 15-minute planning allowance, but timing is not proven.
- Toshiba 4 TB HDD: 25 minutes is NOT sufficient if retirement requires a full overwrite.

If the SSD erase operations can be initiated independently/concurrently, the UPS duration is governed primarily by the slowest SSD sanitize operation plus verification and orderly shutdown margin, rather than the sum of all four SSD erase durations. This concurrency assumption must be validated in the eventual implementation.

## Practical planning table

| Drive | Preferred/likely retirement path | Current time knowledge | Working allowance |
|---|---|---|---|
| Bestoss GM528 2 TB NVMe | NVMe Crypto Erase Sanitize | Drive reports no estimate | ~1 minute planning allowance; not guaranteed |
| SPCC 120 GB SATA SSD | ATA SSD secure erase/sanitize path | Exact time unknown | 10 minutes planning allowance |
| Kingston Q500 240 GB SATA SSD | ATA SSD secure erase/sanitize path | Exact time unknown | 10 minutes planning allowance |
| WD WDS100T2B0B 1 TB SATA SSD | ATA SSD secure erase/sanitize path | Exact time unknown | 15 minutes planning allowance |
| Toshiba MG04ACA400NY 4 TB HDD | Full overwrite unless another sanitize mechanism is found | Hours expected | Several hours; 452-min SMART full-test time gives scale only |

## Tools installed / investigation environment

The investigation installed/used:

- smartmontools 7.5; `smartctl.exe` was added to the Windows system PATH.
- MSYS2 UCRT64 environment.
- nvme-cli built from source for Windows.
- Built nvme-cli version observed: `nvme version 3.0-rc1 (git v3.0-rc1-69-g2d02e50+)`.
- libnvme version observed: `3.0-rc1`.
- Built executable location: `C:\nvme-cli\build\nvme.exe`.
- MSYS2 UCRT64 runtime DLL directory needed in PATH for nvme-cli: `C:\msys64\ucrt64\bin`.

No destructive storage command was intentionally issued during this investigation. The commands used for capability discovery were read-only Identify/SMART/sanitize-log operations.

## What remains unresolved

1. Obtain authoritative or measured ATA Secure Erase / Enhanced Secure Erase timing for the SPCC, Kingston, and WD SATA SSDs.
2. Determine whether any of those SATA SSDs provide a preferable ATA Sanitize mechanism beyond the ATA Security information exposed by smartctl.
3. Determine whether the Toshiba MG04ACA400NY exposes any usable sanitize mechanism through another tool/path before accepting full overwrite as the only practical logical retirement method.
4. If the system will rely operationally on a 25-minute UPS window, validate the complete sequence on expendable/equivalent hardware: command initiation, concurrent operation if applicable, completion verification, failure behavior, and UPS shutdown margin.
5. Do not convert the current planning allowances into guarantees without those tests.

## Retrieval note for future ChatGPT sessions

If asked to recover this investigation later, search the Riverview GitHub repository for any of the following phrases:

- `HARD_DRIVE_ERASURE_SANITIZATION_INVESTIGATION`
- `hard drive erasure investigation`
- `SSD sanitization`
- `UPS erase window`
- `Bestoss GM528 SVN22817`
- `Toshiba MG04ACA400NY`
- `WDS100T2B0B secure erase`

The canonical document is intended to be:

`docs/HARD_DRIVE_ERASURE_SANITIZATION_INVESTIGATION_2026-08-19.md`

This file is the durable summary of the August 19, 2026 five-drive erasure/sanitization investigation.