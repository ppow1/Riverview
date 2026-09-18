<!--
File: docs/hardware/gpu/OCTOMINER_THREE_NODE_COMPUTE_AND_DISPLAY_DECOUPLING_2026-09-18.md
Version: 1.0.0
Date: 2026-09-18
Status: Milestone / verified capability and expansion topology
-->

# Riverview Milestone — Three-Device Compute Topology and RTX 4090 Display Decoupling

**Event date:** 2026-09-18  
**Status:** Major infrastructure milestone  
**Purpose:** Record the successful decoupling of workstation display output from the RTX 4090 and the resulting expansion path from a two-node GPU pool to three independently usable compute devices.

## Verified display-decoupling milestone

A USB-to-dual-4K display adapter was installed on the Windows development environment and worked immediately when connected to a small test monitor.

This verifies the critical architectural point:

- the workstation's display requirement no longer depends on the RTX 4090;
- the RTX 4090 can therefore be returned to OCTOMINER1 as a dedicated compute accelerator;
- the four-display workstation can remain operational without using the RTX 4090 for display output.

The intended four-display arrangement is:

- two displays driven by the Linux daily-driver system;
- two displays driven from the development machine through the HDMI matrix / USB display arrangement;
- keyboard/mouse switching used to move active control between systems.

This removes the previous practical blocker that forced the RTX 4090 to serve both desktop display and compute roles.

## 80B compute result that motivated the change

During the recent OCTOMINER1 experiment, the node was configured with:

- RTX 4090 24 GB
- Tesla P100 16 GB
- Tesla P100 16 GB

The approximately 80B-parameter MoE workload repeatedly achieved approximately **50 tokens/sec** inference performance.

The result demonstrated that the RTX 4090 plus the two P100s are useful together as a heterogeneous large-model inference configuration, rather than the P100s being merely legacy spare accelerators.

The relevant previously recorded evidence is:

- `docs/hardware/gpu/OCTOMINER_TWO_NODE_96GB_LOCAL_AI_MILESTONE_2026-09-16.md`
- `docs/operations/octominer/QWEN3_NEXT_80B_HERMES_ENDURANCE_AND_STATE_INTEGRITY_TEST_2026-09-16.md`

## New three-device expansion capability

The development machine can now be treated as a potential **third independent compute device**.

The important clarification is that the development-machine P100 expansion was previously blocked by the RTX 4090's role in driving the four-display workstation. The USB display adapter removes that dependency.

This creates a new topology:

1. **OCTOMINER1** — primary high-performance heterogeneous compute node.
2. **OCTOMINER2** — independent secondary compute node.
3. **Development machine** — now capable of becoming a third compute appliance, including the option to install two additional Tesla P100 16 GB cards.

The two additional P100s would add **32 GB of physical VRAM** to the available compute hardware when installed in the development machine.

The development-machine P100 installation is an **extension now enabled by the display-decoupling milestone**; it is not being recorded as an already-installed configuration.

## BIOS-work strategy enabled by the three-device topology

The new topology changes how the OCTOMINER1 BIOS/MMIO problem can be worked.

Before this milestone, taking an Octominer out of service for BIOS investigation reduced the available compute pool.

With the development machine available as a third compute device, one Octominer can be taken out of the active compute loop for BIOS recovery, firmware experimentation, PCIe/MMIO/BAR investigation, and validation while the other two compute devices remain usable.

This makes the BIOS problem substantially easier to work on operationally because the system under test does not have to remain part of the production compute pool.

The intended sequence is:

1. establish the development machine as a third compute appliance when the additional two P100s are acquired/available;
2. take one Octominer offline for the BIOS/MMIO work;
3. solve and validate the BIOS/PCIe allocation problem;
4. once a BIOS-fixed Octominer can reliably support the additional P100 capacity, move the two P100s from the development machine into that repaired Octominer if another pair of P100s is not yet affordable;
5. thereby concentrate an additional **32 GB VRAM** into the BIOS-fixed Octominer for large models whose weights can be split across multiple GPUs.

The two P100s are therefore not merely an expansion of the development machine. They are also a **portable expansion resource** that can temporarily provide a third compute node and later become the additional VRAM capacity for a BIOS-fixed Octominer.

## Large-model capacity implication

Two additional P100s contribute:

- 16 GB + 16 GB
- **32 GB additional physical VRAM**

When moved into a BIOS-fixed Octominer, this can enable model configurations that require more aggregate GPU memory than the current two-P100 configuration provides, including larger models split across multiple GPUs.

The architecture should continue to treat GPU memory on separate physical machines as separate pools. The 32 GB becomes part of a larger contiguous-on-one-node pool only after the P100s are physically installed in the same BIOS-capable Octominer.

## Strategic topology

This milestone establishes a more flexible progression:

**Current verified two-node pool**

- OCTOMINER1
- OCTOMINER2

**Newly enabled three-device topology**

- OCTOMINER1
- OCTOMINER2
- Development machine with optional 2x P100 expansion

**Post-BIOS expansion path**

- BIOS-fixed OCTOMINER with the two additional P100s
- second independent Octominer
- development machine available in its normal workstation role or later independently expanded as hardware/budget permits

The key architectural benefit is **reconfigurability**: compute capacity can be redistributed between the development machine and the Octominers as the BIOS/MMIO problem is solved and as additional P100s become affordable.

## Relationship to the BIOS/MMIO project

This milestone does not claim that the BIOS/MMIO problem is solved.

It records that the display and compute architecture now provides a practical way to isolate an Octominer for that work without sacrificing the entire local compute capability.

The authoritative BIOS/MMIO work remains documented in:

- `docs/operations/octominer/OCTOMINER1_FPT_EFI_BIOS_RECOVERY_AND_MULTI_P100_MMIO_PLAN_2026-09-14.md`
- `docs/operations/octominer/OCTOMINER1_OCTOMINER2_HARDWARE_SCAN_2026-09-14.md`

## Milestone conclusion

**VERIFIED:** The USB-to-dual-4K display adapter successfully decouples the four-display workstation from the RTX 4090.

**VERIFIED:** The RTX 4090 can therefore return to OCTOMINER1 as a dedicated compute GPU while the four-display workstation remains usable through the Linux daily driver plus development-machine/HDMI-matrix display path.

**VERIFIED:** OCTOMINER1 demonstrated approximately 50 tokens/sec on the approximately 80B MoE workload with 4090 + 2x P100.

**NEW CAPABILITY ENABLED:** The development machine can now serve as a third independent compute device and can be expanded with two additional P100s.

**NEW OPERATIONAL CAPABILITY ENABLED:** One Octominer can be removed from the active compute pool for BIOS/MMIO work while compute remains available on the other Octominer and the development-machine compute appliance.

**FUTURE EXPANSION PATH:** After the BIOS problem is solved, the two development-machine P100s can be moved into the repaired Octominer, adding **32 GB physical VRAM** to that node and enabling larger multi-GPU model splits.

The durable architectural interpretation is that the hardware pool is no longer constrained to a fixed two-node arrangement. It is now a reconfigurable set of compute resources that can be temporarily redistributed around the BIOS/MMIO work and later concentrated where the additional VRAM is most valuable.
