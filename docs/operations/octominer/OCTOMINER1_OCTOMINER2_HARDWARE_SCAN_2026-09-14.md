# OCTOMINER1 / OCTOMINER2 Hardware Control Scan — 2026-09-14

Status: **Post-recovery physical identity and CPU/RAM control baseline.**

Purpose: preserve the hardware scan used to establish that restored physical OCTOMINER1 is operating normally relative to physical OCTOMINER2 and prevent stale HiveOS hostnames from being mistaken for physical machine identity.

## Physical identity is MAC-authoritative

### OCTOMINER1

- Physical management NIC MAC: `00:e0:4c:6b:05:a9`
- IP during this validation: `192.168.1.160`
- Board: Octominer X12 Ultra
- DMI board revision observed after recovery: `Ver:1.52`
- Chipset observed during firmware work: Intel B250
- Software hostname after recovery: `OCTOMINER2` — **stale/wrong identity; do not use it to identify the chassis**

### OCTOMINER2

- Physical management NIC MAC: `00:e0:4c:53:9e:5e`
- IP during this validation: `192.168.1.162`
- Board: Octominer X12 Ultra
- DMI board revision: `1.12`
- Software hostname also reported `OCTOMINER2`

Operational rule: identify the two physical chassis by MAC address first. DHCP addresses and HiveOS hostname/worker configuration may be stale or duplicated.

## CPU comparison

Both machines reported:

- Intel Core i5-6500 @ 3.20 GHz
- 4 physical cores / 4 logical CPUs
- comparable cache topology
- CPUs operating near the expected ~3.2 GHz range during the validation scan
- `performance` CPU frequency governor

No material CPU configuration difference was found that would explain a recovery-related performance loss on OCTOMINER1.

## Memory comparison

Both machines reported:

- 16 GiB system RAM
- 2 x 8 GiB DIMMs
- DDR3-1600 configuration
- dual-channel population/layout

No material RAM population/configuration difference was found between the machines during the control scan.

## Reproducible 15-second CPU control benchmark

A deterministic benchmark was created because the exact implementation of the historical 15-second pi benchmark that produced `14,880` decimal places could not be recovered.

Current benchmark identifier:

`CHUDNOVSKY_DECIMAL_15S_V1`

Script:

`/root/octominer-pi-15s.py`

SHA-256:

`543464ff9b5646f6133c1d058e68ba3394cc627cc32498ced449bf55a99e07c0`

The **exact same script** was used on both physical machines.

### OCTOMINER1 result

- Completed decimal places: `6000`
- Last completed calculation: `14.158793 s`

### OCTOMINER2 control result

- Completed decimal places: `6000`
- Last completed calculation: `14.161248 s`

Conclusion: under this exact reproducible CPU/RAM workload, restored physical OCTOMINER1 and physical OCTOMINER2 are effectively identical. The historical `14880` value is retained only as an unknown-method historical reference and must not be compared numerically with this new benchmark.

## Firmware relationship

OCTOMINER2 is a control machine, not a firmware donor.

Earlier full SPI reads established that OCTOMINER2's BIOS build differs materially from OCTOMINER1 even though they are closely related X12 Ultra systems. The Intel flash descriptor layout was common, but the BIOS contents/build dates and compressed firmware structures differ.

Therefore:

- use OCTOMINER2 for behavioral, hardware, topology, and performance comparisons;
- do not use its full BIOS image as OCTOMINER1's restoration source;
- OCTOMINER1's canonical stock source remains `OCTOMINER1-BIOS-5.12-2021-09-18.bin`.

## Recovery acceptance significance

This scan was performed after the EFI FPT BIOS-region stock restoration on OCTOMINER1. Together with successful HiveOS boot and stable SSH, the matching CPU/RAM configuration and matching benchmark result are strong functional evidence that the machine has recovered from the catastrophic 372/384-GiB firmware behavior.

For the complete firmware recovery procedure, hashes, FPT commands, and next multi-P100/MMIO investigation plan, see:

`docs/operations/octominer/OCTOMINER1_FPT_EFI_BIOS_RECOVERY_AND_MULTI_P100_MMIO_PLAN_2026-09-14.md`
