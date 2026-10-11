# OCTOMINER1 C1-128G SPI Recovery and CPU Qualification — 2026-10-10

## Outcome
**PASS — SPI recovery, POST, operating-system boot, 128 GiB root PCIe MMIO aperture, and deterministic CPU regression test.**
**NOT YET TESTED — GPU enumeration, BAR allocation with NVIDIA GPUs, multi-GPU inference, and long-duration stability.**

## Hardware and firmware
- Host: OCTOMINER1, SSH alias `octo1`.
- Motherboard: OctoMiner X12 Ultra, X12ULTRA-PKB12-2203, Ver 1.52.
- SPI flash: Macronix MX25L6473E, 8 MiB, 3.3 V, motherboard position UH1.
- External programmer: CH341A SPI / SOIC8 clip, flashrom v1.7.0 Windows.
- Recovery image: `A:\tools\Flashrom\BIOS_Backup\OCTO1_C1_RECOVERY_8MB.bin`.
- Image layout: existing UH1 descriptor and Intel ME (first 2 MiB) preserved; C1 BIOS region (last 6 MiB) installed.
- Recovery image SHA256: `7B8FAFAFC75E8C6BF6825A713FA9C5BA92C78579CBD3EF072FB7C0F5E4ED8DFA`.
- Independent post-flash readback: `A:\tools\Flashrom\BIOS_Backup\OCTO1_C1_POSTFLASH_READBACK.bin`; size 8,388,608 bytes; SHA256 identical to image.
- Original pre-recovery chip reads: `UH1_Read1.bin` and `UH1_Read2.bin` in `A:\tools\Flashrom\BIOS_Backup`; both SHA256 `01E4C606A39FB116FCCBB994DF0BB34C4C135179E1BF42EEB7FFD225AB689043`.

## External SPI flash evidence
Flashrom identified MX25L6473E and reported:
```text
Updating flash chip contents... Erase/write done from 0 to 7fffff
Verifying flash... VERIFIED.
FLASHROM_EXIT_CODE=0
```
Independent second read:
```text
Reading flash... done.
READ_EXIT_CODE=0
READBACK_SIZE=8388608
READBACK_SHA256=7B8FAFAFC75E8C6BF6825A713FA9C5BA92C78579CBD3EF072FB7C0F5E4ED8DFA
SOURCE_SHA256=7B8FAFAFC75E8C6BF6825A713FA9C5BA92C78579CBD3EF072FB7C0F5E4ED8DFA
C1_FLASH_VERIFIED=True
```
Flashrom emitted nonfatal WinUSB driver-detach and WP/config warnings; write and readback succeeded.

## POST, Linux and PCIe MMIO
- Operator observed motherboard POST after reassembly.
- SSH confirmed HiveOS/Linux host `OCTOMINER1` up for three minutes.
- Kernel ACPI host bridge resource:
```text
pci_bus 0000:00: root bus resource [mem 0x2000000000-0x3fffffffff window]
```
This is a 128 GiB PCIe MMIO address aperture above 4 GiB. It is not evidence of 128 GiB RAM or proof of successful P100 BAR allocation.
- `lspci` showed Intel HD Graphics 530 and no NVIDIA GPUs. Operator confirmed no NVIDIA GPUs were physically installed; all were in OCTOMINER2.
- No failed BAR assignments appeared in the provided boot-log extract; no GPU allocation was attempted.

## Deterministic 15-second pi CPU regression test
- Identifier: `CHUDNOVSKY_DECIMAL_15S_V1`.
- Script: `/root/octominer-pi-15s.py`.
- Script SHA256: `543464ff9b5646f6133c1d058e68ba3394cc627cc32498ced449bf55a99e07c0` (verified on OCTOMINER1).
- Command from Windows: `ssh octo1 "sha256sum /root/octominer-pi-15s.py; python3 /root/octominer-pi-15s.py"`.
- New OCTOMINER1 C1 result:
```text
BENCHMARK=CHUDNOVSKY_DECIMAL_15S_V1
LIMIT_SECONDS=15.0
COMPLETED_DECIMAL_PLACES=6000
LAST_COMPLETED_AT_SECONDS=14.160698
TOTAL_WALL_SECONDS=15.104519
HISTORICAL_RECORDED_BASELINE=14880
```

| Machine and firmware | 6000-digit last completion |
|---|---:|
| OCTOMINER1 stock | 14.158793 s |
| OCTOMINER1 C1-128G (2026-10-10) | **14.160698 s** |
| OCTOMINER2 stock | 14.161248 s |
| OCTOMINER2 C1-128G | 14.167809 s |

OCTOMINER1 stock-to-C1 difference: +0.001905 s (~0.0135%), negligible for a single-run CPU comparison. The 15.104519 s total wall time is the bounded benchmark runtime, not the 6000-digit completion time. Historical 14,880-digit result used an unrecovered different method and is not directly comparable.

## Next qualification
Preserve working OCTOMINER2 inference setup unless a transfer is planned. On OCTOMINER1, install P100s incrementally and capture `lspci -nnvv`, `/proc/iomem`, `dmesg` BAR/window allocation messages, `nvidia-smi`, reboot stability, and model inference. Do not claim multi-GPU qualification until physically tested.

## Related Riverview records
- `docs/operations/octominer/OCTOMINER1_C1_BAD_FLASH_FULL_POSTMORTEM_AND_RECOVERY_HANDOFF_2026-10-07.md`
- `docs/operations/octominer/OCTOMINER1_OCTOMINER2_HARDWARE_SCAN_2026-09-14.md`
- `docs/operations/octominer/OCTO2_C1_128G_BIOS_FULL_POSTMORTEM_REPRODUCTION_AND_FOUR_GPU_HANDOFF_2026-10-08.md`
