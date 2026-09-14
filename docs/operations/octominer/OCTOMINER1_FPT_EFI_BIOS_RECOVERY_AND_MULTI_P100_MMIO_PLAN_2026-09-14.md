# OCTOMINER1 EFI FPT BIOS Recovery and Multi-P100 MMIO Plan

Status: **Stock BIOS recovery functionally successful; EFI-level Intel FPT recovery path proven on physical OCTOMINER1.**

Date: 2026-09-14

## 1. Recovery result

OCTOMINER1 was recovered from the unusable experimental high-MMIO firmware by abandoning Linux-dependent recovery and the AMI AFU modified-image path and using Intel Flash Programming Tool for EFI directly from the working x64 UEFI shell.

The successful recovery was deliberately limited to the 6 MiB BIOS region. The Intel flash descriptor and Intel ME regions were not intentionally written.

Proven chain:

1. Boot FAT32 USB into the working x64 UEFI shell.
2. Use Intel CSME 11.x `Fpt.efi` with the matching `fparts.txt`.
3. Prove read access with `Fpt.efi -bios -d CURRENT.BIN`.
4. Extract the canonical stock BIOS region from the trusted 8 MiB full SPI image at full-image offsets `0x200000-0x7FFFFF`.
5. Program BIOS region only with `Fpt.efi -f STOCKBIOS.BIN -bios`.
6. Change `startup.nsh` to a read-only verification command and dump live BIOS to `STOCKVERIFY.BIN`.
7. Compare readback rather than blindly reflashing mutable firmware state.
8. Cold boot without recovery USB and validate HiveOS, SSH, CPU clocks, RAM, and a reproducible CPU benchmark.

## 2. Physical machine identity

### Physical OCTOMINER1

- Management NIC MAC: `00:e0:4c:6b:05:a9`
- Restored validation IP: `192.168.1.160`
- Board DMI: `OCTOMINER / X12ULTRA / Ver:1.52`
- Chipset observed by flashrom: Intel B250
- CPU: Intel Core i5-6500 @ 3.20 GHz
- CPU topology: 4 cores / 4 threads
- RAM: 16 GiB, 2 x 8 GiB DDR3-1600, dual-channel
- HiveOS kernel after recovery: `6.6.0-hiveos`
- Important software-identity defect after recovery: the physical OCTOMINER1 was reporting hostname and Hive worker name `OCTOMINER2`. Physical identity is determined by MAC, not the stale hostname.

### Physical OCTOMINER2 comparison machine

- MAC: `00:e0:4c:53:9e:5e`
- IP during validation: `192.168.1.162`
- Board DMI revision: `1.12`
- CPU: Intel Core i5-6500 @ 3.20 GHz
- RAM: 16 GiB, 2 x 8 GiB DDR3-1600
- Use as behavioral/performance control only. Its BIOS build is different and is not a restoration source for OCTOMINER1.

## 3. Canonical firmware and SPI map

Canonical OCTOMINER1 stock full image:

- File: `OCTOMINER1-BIOS-5.12-2021-09-18.bin`
- Known Windows path: `C:\Users\wille\Desktop\OCTOMINER1-BIOS-5.12-2021-09-18.bin`
- Size: `8388608` bytes
- SHA-256: `52418F6A0DE6FD6A6C1C5CE90DC4FA9D6C4BBA910E09B79F2377B740CA857014`

Intel SPI layout:

- Descriptor: `0x000000-0x000FFF`
- Intel ME: `0x001000-0x1FFFFF`
- BIOS: `0x200000-0x7FFFFF`
- BIOS-region size: `6291456` bytes

Extracted canonical stock BIOS region:

- Recovery filename: `STOCKBIOS.BIN`
- Size: `6291456`
- SHA-256: `372353AEF71055EC58AB413D2F197C1FA8A01EFADCFA59FC84A6668186D6489A`

Recovery rule: **BIOS region only. Do not write Descriptor or ME without a separately reviewed justification.**

## 4. EFI recovery tooling proven on hardware

Working UEFI shell:

- `EFI\BOOT\BOOTX64.EFI`
- Size: `938880`
- SHA-256: `50437F8F0623A076F350AE937B0054F5912A14BBF9948C9665CA6AE4B0F31E7A`

Intel FPT EFI:

- File: `Fpt.efi`
- FPT version observed on OCTOMINER1: `11.8.65.3606`
- Size: `4076800`
- SHA-256: `01BE50081142F2314AAB4366AB2A20AC6C3D1A7879A92003897EF78BC30E8001`

Matching flash-parts database:

- File: `fparts.txt`
- Size: `15153`
- SHA-256: `77A5A9A384E29F907714D31069A558203DCFEA30486A7E6D2D1BDDD813CABEB4`

AMI AFU used earlier:

- `AfuEfix64.efi`
- Size: `642128`
- SHA-256: `7740B6A92EAA955728E4095B7E8E0EBA6A3B631046DB43978CA5DFAC99DC18CB`

AFU normal `/P` and `/CAPSULE` paths hit Secure Flash/Error 18. `/RECOVERY /P` reached native AMI recovery processing but modified images were rejected by Secure Flash ROM verification. These are not the preferred recovery path now that EFI FPT is proven.

## 5. First FPT proof: read-only BIOS-region dump

Command:

```text
Fpt.efi -bios -d CURRENT.BIN
```

The command initialized the Intel SPI interface, found the MX25-series 8 MiB flash, read the 6 MiB BIOS region to 100%, and reported FPT operation successful.

`CURRENT.BIN`:

- Size: `6291456`
- SHA-256: `5853865AB715FA0F0A5B55F6B68ACCB74E1A4555D50B8AA7566BDF784E6EA910`

This was the decisive proof that the platform could be recovered at EFI level even while Linux recovery was unreliable.

## 6. V3 FPT programming lesson

V3 full image:

- SHA-256: `F2F72A722026559B069BD705C37475F614EE6375D12F4BDBDD3E95E4BA16EECD`

V3 extracted BIOS region:

- File: `V3BIOS.BIN`
- Size: `6291456`
- SHA-256: `FF8F6DF8EDC9A41416721764C5154D1281F0581EEB51FFB7DD82855FA8BA4279`

One FPT write attempt was interrupted by a reset during programming. This exposed a bad automation design: a simple `ATTEMPTED.TXT` marker blocked a needed retry. Recovery automation must distinguish **write started** from **FPT successfully returned**. Never let a pre-write marker permanently suppress recovery after an interrupted flash.

Later read-only V3 verification:

```text
Fpt.efi -bios -d VERIFY.BIN
```

`VERIFY.BIN` SHA-256: `78D2610A34F8D883B64B5EA579771383F7FCAB11E3222D444EED92E4DE5F9046`

Forensics showed all 9,145 residual differences from the static V3 target were within the first 64 KiB of the BIOS region; differences beyond BIOS offset `0x010000` were zero. FPT had programmed the executable payload while live firmware/NVRAM content remained mutable.

## 7. Successful stock restoration

The canonical full image was validated by exact size and hash, and its BIOS region was extracted to `STOCKBIOS.BIN`.

Proven write command:

```text
fs0:
cd \
Fpt.efi -f STOCKBIOS.BIN -bios
```

Scope:

- BIOS region: YES
- Descriptor: NO
- Intel ME: NO

Do not substitute the 8 MiB full image when using this BIOS-region recovery procedure.

## 8. Independent readback after stock write

After the write was complete, `startup.nsh` was changed to the read-only command:

```text
fs0:
cd \
Fpt.efi -bios -d STOCKVERIFY.BIN
```

A Windows-side safety check confirmed:

- read command present: TRUE
- write command present: FALSE
- safe read-only boot: TRUE

`STOCKVERIFY.BIN`:

- Size: `6291456`
- SHA-256: `5D7DD00C847ED34FA519D43658AA4B328351E5FE84F8EA4AD2134B9D6F2467C6`

Compared with static `STOCKBIOS.BIN`:

- Full differing bytes: `734`
- First 64 KiB differences: `7`
- Beyond first 64 KiB: `727`
- Difference ranges: `40`
- `690/734` differences concentrated in the 4 KiB block at BIOS offset `0x015000`
- None of the 727 beyond-64K residual bytes equaled the prior V3 live values at those same offsets.

The historical live dump was not a useful byte-for-byte stock target: it differed from the static stock BIOS region by `2,524,177` bytes, while the restored image differed by only `734`. Therefore the correct next gate was functional validation rather than another blind write.

## 9. Functional validation after recovery

Physical OCTOMINER1 booted HiveOS and accepted SSH after the stock restoration.

Physical identity was proven by NIC MAC `00:e0:4c:6b:05:a9` even though the software hostname was stale and reported `OCTOMINER2`.

CPU/RAM scan after recovery:

- i5-6500, 4 cores / 4 threads
- all four CPUs near 3.2 GHz
- `performance` governor
- 16 GiB RAM
- two 8 GiB DDR3-1600 DIMMs
- dual-channel layout

The same hardware scan on physical OCTOMINER2 showed the same CPU model, core count, memory size, DIMM layout, configured DDR3 speed, cache sizes, and governor/frequency behavior. This made OCTOMINER2 a valid CPU/RAM performance control despite its different board revision and BIOS build.

A reproducible 15-second CPU benchmark was created and saved as `CHUDNOVSKY_DECIMAL_15S_V1`.

Script SHA-256:

`543464ff9b5646f6133c1d058e68ba3394cc627cc32498ced449bf55a99e07c0`

Results using the **exact same script**:

- physical OCTOMINER1: `6000` completed decimal places, last completed at `14.158793 s`
- physical OCTOMINER2: `6000` completed decimal places, last completed at `14.161248 s`

The systems are effectively identical in this CPU/RAM workload. The earlier historical `14880` figure came from a different/lost benchmark implementation and is not directly comparable.

## 10. Why the original multi-P100 problem still matters

Before the firmware work, stock OCTOMINER1 reliably operated approximately:

- 2 x Tesla P100 PCIe 16 GB
- 1 x RTX 3060 Ti

Adding another P100 failed before normal BIOS setup/boot. Above-4G decoding was already enabled and changing PCIe generation did not solve it.

Observed P100 BAR layout:

- BAR0: 16 MiB
- BAR1: 16 GiB
- BAR3: 32 MiB

BAR1 requires 16-GiB alignment. The stock high-MMIO window was identified as:

- Base: 128 GiB
- Length: 64 GiB
- Range: 128-192 GiB

Observed allocation pattern explained the failure:

- P100 #1 BAR1: 128-144 GiB
- smaller resources then consume address space around the boundary
- P100 #2 BAR1 aligns at 160-176 GiB
- next P100 BAR1 wants 192-208 GiB
- stock aperture ends at 192 GiB

Thus a 16-GiB P100 BAR can effectively consume roughly 32 GiB of aperture when bridge-window alignment/padding is included. Treat this as a topology/allocation problem, not a claim that every P100 always consumes exactly 32 GiB in every system.

## 11. What the failed 384/372-GiB experiments taught us

Original high-MMIO window:

- base `0x2000000000` = 128 GiB
- length `0x1000000000` = 64 GiB
- range 128-192 GiB

Experimental 384-GiB window:

- base 128 GiB
- length 384 GiB
- end 512 GiB

The candidate was successfully programmed and independently read back, proving the binary reached flash correctly, but firmware initialization became catastrophically slow. The i5-6500 exposes a 39-bit physical-address ceiling of 512 GiB, so consuming essentially the whole 128-512 GiB region was legal in arithmetic but unusable in this firmware/platform implementation.

Four logical allocator changes were made in the old experiment:

- `PciHostBridge +0x1275`: `0x10 -> 0x60`
- `PciHostBridge +0x128C`: `0x10 -> 0x60`
- `PciHostBridge +0x12CD`: `0x10 -> 0x60`
- `PciBus +0x6F78`: `0x10 -> 0x60`

V3 used `0x5D` at the corresponding logical locations. Do not again change all four together without determining their individual semantics.

## 12. Multi-P100 investigation plan after recovery

The recovery capability changes the risk profile: experimental BIOS-region images can now be rolled back at EFI level without depending on Linux. It does **not** make arbitrary firmware edits safe. Use measured, staged experiments.

### Phase A - preserve recovery baseline

Before any new GPU/MMIO experiment:

1. Keep canonical 8 MiB stock image and hashes offline.
2. Keep `STOCKBIOS.BIN`, `Fpt.efi`, `fparts.txt`, and working `BOOTX64.EFI` on a dedicated recovery USB.
3. Keep the stock write command out of the default startup script except during an intentional recovery operation.
4. Maintain a separate read-only `startup.nsh` template.
5. Record each candidate's full-image and BIOS-region hashes before it reaches the machine.
6. Never write descriptor or ME as part of MMIO experiments.

### Phase B - inspect for a hidden firmware setting before patching code

Search the stock Setup/IFR/HII data for hidden controls such as:

- `Above 4G MMIO Size`
- `MMIO High Size`
- `MMIOH Size`
- `Above 4GB MMIO BIOS assignment`
- `PCI MMIO Size`
- related VarStore offsets/options

If the AMI setup already contains a hidden selectable aperture size, prefer exposing or setting that supported variable over changing allocator machine code.

Do not assume AMIBCP compatibility. Extract IFR and identify the VarStore/offset/value mapping first.

### Phase C - measure the PCIe topology and bridge windows

Start with known-good stock firmware and the known-good population `2 x P100 + 3060 Ti`.

Capture:

- `lspci -tv`
- `lspci -Dnn`
- `lspci -vv` for every P100, the 3060 Ti, and every upstream bridge/switch
- BAR start/end/size
- each bridge's prefetchable memory window
- 64-bit vs 32-bit window flags
- bus numbering
- physical slot -> BDF -> upstream bridge mapping
- `/proc/iomem`
- relevant kernel PCI resource messages

Build a slot/topology table instead of treating all twelve connectors as equivalent.

### Phase D - test slot order under stock firmware

Because bridge windows can be rounded/aligned independently, slot placement may change packing efficiency.

Test in a controlled sequence:

1. known-good `2 x P100 + 3060 Ti`
2. add third P100 with the 3060 Ti in different branch/edge positions
3. three P100s without 3060 Ti
4. only after measurements, add the 3060 Ti back

Record the exact first failure point and whether failure occurs before video, before setup, during resource assignment, or in the OS.

### Phase E - decode the four firmware constants

Before a new candidate, determine what each old `0x10` constant actually represents.

Required questions:

- Is `0x10` a count of 4-GiB units?
- Does each PciHostBridge occurrence apply to different boot/resource phases?
- Is `PciBus` an independent cap or derived allocator limit?
- Must PciHostBridge and PciBus agree?
- Is the slow boot from an oversized aperture, an allocator search loop, a mismatch between modules, or another interaction?

Create candidates changing **one semantic control at a time** whenever technically possible.

### Phase F - use modest apertures, not another 128-512 GiB jump

Do not return directly to 372/384 GiB.

Candidate sizes should be driven by measured bridge/BAR requirements. Reasonable experiment points to evaluate mathematically include roughly:

- 96 GiB aperture
- 128 GiB aperture
- 160 GiB aperture
- 192 GiB aperture

These are investigation points, not predetermined byte values. Convert to firmware constants only after the encoding is proven.

For a target such as 10-11 P100s plus a 3060 Ti, first calculate the worst-case bridge-aligned requirement from the real topology. Do not simply multiply 16 GiB VRAM BAR by card count.

### Phase G - acceptance gate for every BIOS candidate

For each candidate:

1. Offline structural comparison against canonical stock.
2. Prove only intended logical modules/constants changed.
3. Record candidate SHA-256.
4. Flash BIOS region only.
5. Read back BIOS region with FPT.
6. Verify intended executable payload.
7. Cold boot with no GPUs and time firmware initialization.
8. Reject immediately if no-GPU POST/boot latency regresses materially.
9. Add GPUs incrementally while recording enumeration and bridge windows.
10. On failure or abnormal latency, EFI-recover to stock before the next experiment.

## 13. Proven emergency rollback runbook

Use the physical MAC to identify OCTOMINER1 if DHCP or hostname state is confusing:

`00:e0:4c:6b:05:a9`

Read-only BIOS dump:

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

Independent readback after the write:

```text
fs0:
cd \
Fpt.efi -bios -d STOCKVERIFY.BIN
```

Never mix the write and verification command accidentally in `startup.nsh`. Before a verification boot, inspect the exact script and confirm there is no `-f` command.

## 14. Current conclusion

OCTOMINER1 is no longer dependent on Linux booting successfully in order to recover the BIOS region. Intel FPT EFI provides a proven path to read, program, and independently read back the BIOS region directly from the UEFI shell.

The system is functionally restored: HiveOS boots, SSH works, CPU and RAM configuration are normal, and the exact same reproducible CPU benchmark produces the same result as the healthy OCTOMINER2 control.

The next objective is not another giant MMIO patch. It is to **measure the PCIe topology and actual bridge-window cost, inspect for a hidden supported MMIO-size setup variable, decode the four allocator constants, and then increase the aperture in the smallest evidence-backed steps needed to move beyond two P100s.**
