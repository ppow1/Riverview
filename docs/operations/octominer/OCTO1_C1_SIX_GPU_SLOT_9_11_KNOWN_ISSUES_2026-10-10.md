# OCTO1 C1-128G — Six-GPU enumeration and slot 9/11 known issues (2026-10-10)

## Status and scope
Operator-reported hardware testing on OCTOMINER1 after successful C1-128G SPI BIOS recovery. **Working six-GPU enumeration is reported, not yet a sustained six-GPU inference or stress-test qualification.** Do not interpret successful enumeration as proof all remaining slots can be populated concurrently.

## Confirmed reported six-GPU population
- NVIDIA GeForce RTX 4090 ×1 — 24 GB nominal VRAM.
- NVIDIA GeForce RTX 3060 Ti ×1 — 8 GB nominal VRAM.
- NVIDIA Tesla P100 ×4 — 16 GB nominal VRAM each, 64 GB combined.
- **Total: 6 GPUs; 96 GB nominal aggregate VRAM** (24 + 8 + 4×16). Aggregate VRAM is not a unified contiguous memory pool; split-model inference and independent worker allocations require suitable software and available VRAM after overhead.
- Operator reports boot, recognition and enumeration of all six simultaneously on OCTO1. A complete contemporaneous six-GPU `nvidia-smi -L` output, workload validation, and stability duration have **not** yet been captured in this record.

## Physical slot observations
| Slot | Operator-reported behavior | Working disposition |
|---|---|---|
| 5 | P100 boots and detects | Usable in individual test |
| 6 | P100 boots and detects | Usable in individual test |
| 7 | P100 boots and detects | Usable in individual test |
| 8 | P100 boots and detects; RTX 3060 Ti also reported working | Usable in individual test |
| 9 | P100 boots/enumerates, then machine locks after ~30 seconds; 3060 Ti detected but malfunctioned | **Known issue — avoid for now** |
| 10 | RTX 3060 Ti works | Usable in individual test |
| 11 | P100 prevents successful boot; RTX 3060 Ti also failed | **Known issue — avoid for now** |
| 1–4, 12 | No individual slot qualification documented here | Unknown; do not infer pass/fail |

**Cross-machine observation:** Operator additionally reports OCTOMINER2 had an issue with an RTX 3060 Ti in physical slot 11. This is a report of similar symptoms on another board, **not** proof of a common root cause.

## Diagnostic interpretation and constraints
- Slot 9 and slot 11 should be tracked as **suspect slot/link/firmware paths**, not declared physically defective. Candidate causes include per-root-port speed/link training, riser/slot electrical issues, and resource/driver initialization. No root cause is confirmed.
- PCIe device detection (`lspci`) does not imply successful NVIDIA driver initialization (`nvidia-smi`). Earlier OCTO1 observation: 4090 and 3060 Ti both visible to `lspci`, but only 4090 visible to `nvidia-smi` in that specific slot arrangement.
- No further BIOS patching is required to document this finding. Preserve working C1 BIOS and stable slot layout.
- Current practical workaround: **avoid physical slots 9 and 11**; use demonstrated working placements and verify all GPUs with `nvidia-smi -L`.
- Simultaneous maximum slot population remains **unknown**; six is the operator-reported working count, not a demonstrated upper bound.

## Follow-up qualification
1. Capture `nvidia-smi -L`, `nvidia-smi --query-gpu=index,name,memory.total,pci.bus_id --format=csv`, `lspci -nn | grep -i nvidia`, and `lspci -tv` on the six-GPU configuration.
2. Capture `dmesg` PCIe AER/NVRM/Xid errors, GPU link speeds, and runtime stability under a representative concurrent workload.
3. Record physical-slot-to-PCIe-root-port mappings using single-GPU moves only when convenient; compare slot 9 and 11 with a known-good slot using unchanged riser, power and GPU where possible.
4. If investigating failures, compare Auto/Gen1/Gen2/Gen3 root-port link settings without disturbing the proven working six-GPU configuration until a recovery path is ready.

## Related
- OCTO1 C1-128G SPI recovery and CPU qualification record: `docs/operations/octominer/OCTO1_C1_128G_SPI_RECOVERY_AND_CPU_QUALIFICATION_2026-10-10.md` (PR #10 at time of writing).
