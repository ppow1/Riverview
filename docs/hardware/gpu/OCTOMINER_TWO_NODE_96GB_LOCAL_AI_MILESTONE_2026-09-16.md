<!--
File: docs/hardware/gpu/OCTOMINER_TWO_NODE_96GB_LOCAL_AI_MILESTONE_2026-09-16.md
Version: 1.0.1
Date: 2026-09-16
Status: Historical milestone / configuration superseded 2026-10-26
-->
# Riverview Milestone — Two-Node 96 GB Local AI Compute Pool

> **Historical topology snapshot:** The 2026-09-16 measurements and demonstrated
> workloads below are retained as useful history. The OCTOMINER2 GPU layout and
> 96 GB current-pool description are superseded as of 2026-10-26: OCTOMINER2 now
> has one Tesla P100 16 GB, and the additional GPUs described here were moved to
> OCTOMINER1. See [`OCTOMINER2_CURRENT_CONFIGURATION_2026-10-26.md`](../../operations/octominer/OCTOMINER2_CURRENT_CONFIGURATION_2026-10-26.md)
> before making current allocation or scheduling decisions.

**Event date:** 2026-09-16  
**Status:** Major local-compute milestone  
**Purpose:** Preserve the demonstrated value, topology, acquisition economics, and practical capability of the Steward's current Octominer/GPU pool.

## Milestone

On 2026-09-16, Riverview demonstrated that a heterogeneous local GPU node consisting of one RTX 4090 24 GB plus two Tesla P100 16 GB cards can run `Qwen3-Next-80B-A3B-Instruct-Q4_K_M` at approximately 45-50 generated tokens/sec during real interactive and agent workloads.

This result materially changes the value assessment of the existing hardware. The P100s are not merely spare legacy accelerators; when paired with the RTX 4090 under llama.cpp they function as inexpensive VRAM/capacity extenders that allow a 46 GB 80B MoE model to run at practical interactive speed.

The second Octominer remains independently useful and creates a two-node compute pool even before the BIOS/MMIO problem is solved.

## Current practical topology

### OCTOMINER1 — high-performance node

Temporary tested GPU population:

- RTX 4090 24 GB
- Tesla P100 16 GB
- Tesla P100 16 GB

Physical VRAM on node: **56 GB**.

Demonstrated workload:

- `Qwen3-Next-80B-A3B-Instruct-Q4_K_M`
- GGUF size approximately 48.4 GB
- 65,536 configured context during the Hermes test
- repeated direct generation approximately 49-50 t/s
- very-large-context Hermes-driven generation approximately 44-49 t/s

The 4090 is not intended to remain permanently installed in OCTOMINER1; it returns to the development machine after testing. This milestone records what the topology can do when assembled.

### OCTOMINER2 — independent secondary node

Current intended/verified GPU layout:

- RTX 3060 Ti 8 GB
- Tesla P100 16 GB
- Tesla P100 16 GB

Physical VRAM on node: **40 GB**.

This second node is independently schedulable. It can host smaller or different local models, background reasoning jobs, coding workers, vision models, embeddings/reranking, batch work, and Riverview auxiliary workloads without competing with the primary interactive node.

## Aggregate compute pool

Across the currently owned GPU set:

- RTX 4090: 24 GB
- RTX 3060 Ti: 8 GB
- 4 x Tesla P100: 64 GB

Aggregate physical GPU memory across machines: **96 GB**.

This is **not** a single contiguous 96 GB memory pool. The useful operational interpretation is two independently schedulable pools when configured as above:

- 56 GB high-performance heterogeneous node
- 40 GB secondary/background node

The value comes from parallelism and flexible placement, not from pretending separate machines share one address space.

## Acquisition economics

Historical acquisition cost supplied by the Steward:

- RTX 4090: **$2,200**, purchased approximately three years earlier and already heavily used before this expansion
- two Octominer systems together: **$300**
- four Tesla P100 16 GB cards: approximately **$80 each delivered**, approximately **$320 total**
- RTX 3060 Ti: **$0 incremental**, included with the Octominers

Total historical acquisition cost of the GPU/Octominer pool: approximately **$2,820**, before minor cables/adapters.

More important for expansion economics: the RTX 4090 was already owned and productive. The recent incremental cost that created the two-node multi-GPU infrastructure was therefore approximately **$620** for the two Octominers plus four P100s, with the 3060 Ti included.

## Why this matters

The relevant comparison is not raw resale value or theoretical FP performance. The important demonstrated fact is that the existing hardware can run a large 80B MoE model interactively at roughly 45-50 t/s while also leaving a second independent 40 GB node available for parallel work.

This places the practical local-AI capability in the same broad usage class as modern multi-thousand-dollar personal AI workstations, while preserving CUDA compatibility and reusing hardware already owned.

The architecture also provides something a single appliance does not: two independent machines that can be scheduled separately and reconfigured as needs change.

## Current limitation: BIOS/MMIO

The current layout is constrained by the Octominer BIOS/MMIO/BAR allocation problem. The long-term goal remains to support more than two P100s reliably on a single Octominer where useful.

Until that problem is solved, the two-node 56 GB / 40 GB split is a practical operating configuration rather than a dead end.

The second Octominer therefore remains strategically valuable even under the present firmware constraint.

## Future experiments enabled by this milestone

PROPOSED, not yet accepted:

1. Re-test heterogeneous scaling after the BIOS/MMIO problem is solved, including 4090 + 3x P100 and 4090 + 4x P100 where hardware allocation permits.
2. Measure how model-layer placement changes generation speed and prompt-ingestion speed across 4090/P100 mixes.
3. Test larger context configurations such as 128K before attempting the model's advertised 262K training context.
4. Use OCTOMINER2 as a background-worker node while the 4090 remains in the development machine.
5. Build Riverview scheduling around two independent local inference nodes rather than treating all GPU memory as one pool.

## Related evidence

- `docs/operations/octominer/QWEN3_NEXT_80B_HERMES_ENDURANCE_AND_STATE_INTEGRITY_TEST_2026-09-16.md`
- `docs/hardware/gpu/p100-expansion-2026-09-03/README.md`
- `docs/operations/octominer/OCTOMINER1_OCTOMINER2_HARDWARE_SCAN_2026-09-14.md`
- `docs/operations/octominer/OCTOMINER1_FPT_EFI_BIOS_RECOVERY_AND_MULTI_P100_MMIO_PLAN_2026-09-14.md`

## Milestone conclusion

**VERIFIED:** The Steward has assembled a low-cost, heterogeneous local AI compute pool with 96 GB aggregate physical GPU memory across two Octominer nodes, and the tested 56 GB 4090 + 2x P100 configuration can run an 80B MoE model at practical interactive speed near 50 t/s.

**VERIFIED:** The second Octominer provides an independent 40 GB GPU pool using the 3060 Ti + 2x P100 layout, preserving useful parallel compute while the BIOS/MMIO work remains unresolved.

**STRATEGIC IMPLICATION:** The existing hardware is significantly more capable and economically valuable for Riverview than its component resale prices suggest. Future architecture should treat it as a small local AI cluster rather than as a collection of spare GPUs.
