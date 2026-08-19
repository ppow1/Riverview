# Riverview Storage Erasure Tooling and Capability

**Date:** 2026-08-19  
**Purpose:** Durable record of the additional software/tooling added or configured during the hard-drive erasure/sanitization investigation, and the resulting capability now available on the Riverview workstation.

**Future retrieval search terms:** Riverview storage erasure tooling, hard drive erase software, sanitize tools, smartmontools, smartctl, MSYS2, nvme-cli, NVMe sanitize capability, SATA secure erase capability, drive retirement tooling.

> This document describes software/tooling capability only. No drive was erased during the investigation. The tools can expose destructive commands, so future use must positively identify the intended physical device before any erase/sanitize operation is issued.

## Executive summary

During the storage-erasure investigation, Riverview gained a much stronger low-level storage inspection and sanitization toolchain. The system can now inventory SATA and NVMe devices, inspect SMART/ATA security capabilities, identify NVMe controller capabilities, inspect NVMe sanitize support/status, and prepare for future secure-retirement workflows.

The key additions/configuration were:

1. **Smartmontools / smartctl** was already installed but was not in the Windows PATH. Its installation was located and its binary directory was added to the SYSTEM PATH.
2. **MSYS2** was installed to provide a supported Windows/UCRT64 build environment for current nvme-cli.
3. **MSYS2 UCRT64 development/build dependencies** were installed, including Git, GCC/toolchain components, Meson, Ninja, json-c, ccache, and related dependencies required by the nvme-cli Windows build.
4. **nvme-cli** was cloned from the upstream `linux-nvme/nvme-cli` repository and built successfully for Windows.
5. The resulting `nvme.exe` was tested successfully against the installed Bestoss NVMe drive for read-only Identify Controller and Sanitize Log queries.

This means Riverview now has persistent local capability to perform low-level SATA/ATA diagnostics with smartctl and low-level NVMe diagnostics/sanitize-capability interrogation with nvme-cli.

## 1. Smartmontools / smartctl

### Status before investigation

Smartmontools was already installed on the machine, but `smartctl.exe` was not callable directly because its directory was not present in PATH.

Located executable:

`C:\Program Files\smartmontools\bin\smartctl.exe`

Observed version:

`smartctl 7.5 2025-04-30 r5714`

### Configuration change made

The following directory was added to the Windows SYSTEM PATH:

`C:\Program Files\smartmontools\bin`

The current PowerShell session was also updated so `smartctl` could be invoked immediately without reopening the shell.

### Capability this provides Riverview

`smartctl` can now be invoked directly from PowerShell to:

- enumerate supported storage devices;
- read SMART health/telemetry;
- identify ATA/SATA device model, serial, firmware, size, interface, and security state;
- inspect ATA Security states such as supported/enabled/locked/frozen;
- read low-level ATA IDENTIFY information;
- inspect NVMe information exposed through Smartmontools;
- gather device-health and historical error information before retirement decisions.

This tool was used to identify all four SATA devices and one NVMe device and to establish that the three SATA SSDs expose ATA Security while the Toshiba HDD reports ATA Security unavailable through this path.

## 2. MSYS2

### Installation

MSYS2 was installed through Windows Package Manager (`winget`) using the MSYS2 package.

Installed root:

`C:\msys64`

Important environment/runtime paths:

- `C:\msys64\ucrt64.exe`
- `C:\msys64\msys2_shell.cmd`
- `C:\msys64\usr\bin\bash.exe`
- `C:\msys64\ucrt64\bin`

### Why MSYS2 was required

Current upstream nvme-cli supports Windows builds through the MSYS2 UCRT64 environment. Riverview did not previously have the native Windows build environment required to compile the current nvme-cli source tree.

MSYS2 therefore became the compatibility/build layer used to create a native Windows `nvme.exe`.

### System update performed

MSYS2's package database/core runtime was updated with `pacman -Syu`. The runtime update required the MSYS2 process to terminate/restart once, which is normal for an MSYS2 runtime upgrade.

## 3. MSYS2 UCRT64 build toolchain and packages

A UCRT64 compiler/build environment was installed through MSYS2. The investigation explicitly verified:

- Git: `git version 2.55.0`
- Meson: `1.12.0`
- Ninja: `1.13.2`
- GCC: `gcc.exe (Rev3, Built by MSYS2 project) 16.2.0`

Packages installed or confirmed as part of the build setup included the UCRT64 toolchain and nvme-cli dependencies, including:

- `git`
- `base-devel`
- `mingw-w64-ucrt-x86_64-toolchain`
- `mingw-w64-ucrt-x86_64-meson`
- `mingw-w64-ucrt-x86_64-ninja`
- `mingw-w64-ucrt-x86_64-json-c`
- `mingw-w64-ucrt-x86_64-ccache`
- `mingw-w64-ucrt-x86_64-fmt`
- `mingw-w64-ucrt-x86_64-hiredis`
- `mingw-w64-ucrt-x86_64-hwloc`
- `mingw-w64-ucrt-x86_64-libblake3`
- `mingw-w64-ucrt-x86_64-libltdl`
- `mingw-w64-ucrt-x86_64-tbb`
- Python/jsonschema support packages pulled by the upstream setup script
- other standard dependencies automatically installed by the UCRT64 toolchain group

The upstream repository-provided Windows setup helper used was:

`C:\nvme-cli\scripts\win-ucrt64-setup.sh`

### Capability this provides Riverview

Riverview now has a functional MSYS2 UCRT64 native-build environment capable of compiling current Windows-targeted C/C++ utilities that use this ecosystem, not only nvme-cli. This is a broader development/diagnostic capability than the original storage investigation required.

## 4. nvme-cli

### Source

The upstream repository was cloned to:

`C:\nvme-cli`

Repository source:

`linux-nvme/nvme-cli`

### Build

The repository was configured and compiled using Meson/Ninja under MSYS2 UCRT64.

Successful build output:

`C:\nvme-cli\build\nvme.exe`

Observed versions after build:

- `nvme version 3.0-rc1 (git v3.0-rc1-69-g2d02e50+)`
- `libnvme version 3.0-rc1 (git v3.0-rc1-69-g2d02e50+)`

The build completed successfully with all reported build steps completed.

### Runtime dependency path

The native Windows executable depends on DLLs from the MSYS2 UCRT64 runtime. During testing, Windows initially reported the missing dependency:

`libjson-c-5.dll`

That DLL was present at:

`C:\msys64\ucrt64\bin\libjson-c-5.dll`

For successful execution, the UCRT64 runtime directory was added to the active PowerShell PATH along with the nvme-cli build directory:

`C:\msys64\ucrt64\bin`

`C:\nvme-cli\build`

A future permanent PATH cleanup/installation step may be desirable if Riverview is expected to call `nvme.exe` routinely from arbitrary shells.

### Capability verified on Riverview

`nvme list` successfully detected the installed Bestoss device as:

- Node: `nvme0n1`
- Generic Windows path: `\\.\PhysicalDrive4`
- Model: `Bestoss GM528 2TB`
- Serial: `UB528K5S263ON00048`
- Firmware: `SVN22817`

Read-only NVMe commands were successfully executed to retrieve:

- controller identity;
- firmware/model/serial;
- NVMe version;
- optional admin command capabilities;
- SANICAP sanitize capabilities;
- Format NVM attributes;
- sanitize status/log information;
- sanitize timing fields when reported by firmware.

This established that Riverview can directly interrogate NVMe sanitize capabilities rather than relying on Windows Storage cmdlets or model-number assumptions.

## 5. New storage-management capability now available to Riverview

As a result of this investigation, Riverview now has the technical tooling required for a future controlled storage-retirement workflow.

### SATA / ATA capability

Using Smartmontools, Riverview can:

- enumerate SATA drives;
- read model/serial/firmware/capacity;
- inspect SMART telemetry and error history;
- inspect ATA Security state;
- determine whether a device is security-frozen/locked/enabled;
- read ATA IDENTIFY capability information;
- evaluate candidate ATA Secure Erase / Enhanced Secure Erase / sanitize paths.

### NVMe capability

Using the locally built nvme-cli, Riverview can:

- enumerate NVMe devices and map them to Windows physical-drive identifiers;
- perform Identify Controller/Namespace queries;
- inspect SANICAP;
- determine support for Crypto Erase, Block Erase, and Overwrite Sanitize;
- inspect Format NVM secure-erase capability;
- inspect the Sanitize Status log and progress fields;
- observe drive-advertised sanitize completion estimates when firmware supplies them;
- eventually issue supported NVMe sanitize/format operations when explicitly authorized and after target verification.

### Important distinction

The existence of the tooling does **not** imply that destructive commands should be automated casually. A future erase workflow must include strong guardrails:

- enumerate devices immediately before action;
- confirm model, serial number, capacity, and physical-drive mapping;
- prevent accidental operation on the wrong disk;
- account for the boot/system disk;
- verify that UPS power margin is sufficient;
- log command initiation and completion status;
- verify successful sanitize/erase completion before shutdown or physical retirement.

## 6. Software/configuration footprint created by the investigation

The principal persistent additions/changes on Riverview are:

| Item | Location / state | Purpose |
|---|---|---|
| Smartmontools | `C:\Program Files\smartmontools\bin\smartctl.exe` | ATA/SATA/SMART diagnostics; was pre-existing |
| Smartmontools PATH entry | `C:\Program Files\smartmontools\bin` | Allows direct `smartctl` command use |
| MSYS2 | `C:\msys64` | UCRT64 build/runtime environment |
| MSYS2 UCRT64 packages | under `C:\msys64\ucrt64` | Compiler, Meson/Ninja, json-c and build/runtime dependencies |
| nvme-cli source tree | `C:\nvme-cli` | Upstream nvme-cli source/build tree |
| nvme-cli executable | `C:\nvme-cli\build\nvme.exe` | Low-level NVMe inspection/sanitize utility |
| nvme-cli runtime DLL directory | `C:\msys64\ucrt64\bin` | Required runtime DLLs for the locally built executable |

## 7. Recommended future hardening

If this capability is going to become a maintained Riverview feature rather than a one-off diagnostic environment, consider a future cleanup/hardening task to:

1. Put the tested `nvme.exe` and required runtime dependencies into a stable Riverview tools location rather than relying on a source-tree build directory.
2. Add a stable launcher or PowerShell wrapper that establishes the correct runtime PATH automatically.
3. Record exact tested nvme-cli/libnvme build revision and hashes.
4. Add a read-only `storage-capability-audit.ps1` script that inventories every drive and prints model/serial/capability information without exposing destructive actions.
5. Build destructive erase/sanitize commands as a separate, heavily guarded workflow rather than adding them to the audit script.
6. Require explicit serial-number confirmation and boot-disk protection before a destructive command can execute.
7. Record sanitize results and completion verification to a durable log.

## 8. Relationship to the drive-erasure investigation

The detailed five-drive findings are stored separately in:

`docs/HARD_DRIVE_ERASURE_SANITIZATION_INVESTIGATION_2026-08-19.md`

This document is the companion record describing **what software and system capability Riverview gained while performing that investigation**.

## Retrieval note for future ChatGPT sessions

If a future session is asked what storage-erasure tooling was added to Riverview, search the Riverview GitHub repository for:

- `RIVERVIEW_STORAGE_ERASURE_TOOLING_AND_CAPABILITY`
- `storage erasure tooling`
- `smartmontools nvme-cli MSYS2`
- `Riverview sanitize capability`
- `nvme-cli Windows build`
- `hard drive erase software`

Canonical file:

`docs/RIVERVIEW_STORAGE_ERASURE_TOOLING_AND_CAPABILITY_2026-08-19.md`
