<!-- Version: 1.0.0 | Date: 2026-08-20 | Status: CAPTURED -->
# PL-0003 — Eight-P100 SXM2 Server for 32B Inference Capacity

## Parking Lot identity

- ID: PL-0003
- Category: Local AI / Compute Capacity / Resident Runtime Architecture
- Priority: Strategic
- Originator: Steward
- Date captured: 2026-08-20
- Status: CAPTURED

## Idea

Preserve and later investigate the possibility of acquiring an approximately eight-GPU Tesla P100 SXM2 server as a low-cost Riverview compute expansion platform, with particular attention to whether pairs of P100 SXM2 GPUs can host the Steward's existing 32B local model entirely in GPU memory and provide acceptable interactive latency while also enabling multiple concurrent/background Riverview workers.

A candidate fully populated 8x P100 SXM server has been observed at approximately $1,400 plus roughly $100 shipping. The attraction is that it is already assembled as a working GPU server: acquisition could convert the hardware problem largely into an inference/runtime/topology learning problem rather than requiring construction of another multi-GPU machine.

This is an investigation candidate, not an acquisition authorization.

## Current observed baseline

The current development machine contains an RTX 4090 and a Tesla P100 PCIe 16 GB.

The same 32B model has materially different subjective behavior on those devices:

- RTX 4090: interactive generation is fast enough that responses arrive approximately as fast as or faster than the Steward can comfortably read them; turn-by-turn interaction remains responsive.
- Current P100: the model works and is useful for unattended/overnight work, but interactive generation is noticeably laggy; subjectively, a sentence may be read several times before the next sentence completes.
- The current development host has reached its practical GPU expansion limit, so additional compute requires another unit/server.

A major unresolved question is whether the current single-P100 experience is dominated by the P100's raw generation capability or by the 32B model exceeding 16 GB VRAM and therefore requiring partial CPU/system-RAM offload.

## Proposed 8x P100 use pattern

Do not assume that eight P100s make one inference stream eight times faster.

The potentially useful Riverview configurations include:

- eight independent smaller/background GPU workers when models fit one P100 each;
- four independent 32B workers, each using a directly connected pair of 16 GB P100 SXM2 GPUs;
- fewer larger workers using four or more GPUs where model/context requirements justify it;
- background/overnight workloads on the P100 server while the current RTX 4090 remains available for highly responsive interactive work.

For the current 32B model, the particularly interesting hypothesis is 2x P100 SXM2 per instance. Roughly splitting transformer layers/weights across two GPUs could provide 32 GB aggregate physical VRAM capacity and potentially keep the model entirely off CPU RAM. With layer/model parallelism, each GPU retains its assigned weights locally and only required activations/synchronization cross the GPU interconnect; the full model does not need to be transferred between GPUs for every generated token.

If this works well enough, an 8x server could plausibly provide four simultaneous 32B-class Riverview inference workers rather than one exceptionally fast worker.

## Why the SXM2/NVLink topology matters

The candidate server's exact make/model and GPU topology must be identified before predicting performance or purchasing.

P100 SXM2 systems can provide NVLink connectivity, but an eight-GPU server must not be treated as a generic fully connected 128 GB GPU. Physical peer topology determines which GPU pairs have direct/optimal communication paths and therefore which GPUs should be assigned together for a two-GPU 32B worker.

Future investigation must obtain the exact server model and its NVLink/NVLink-switch topology, CPU platform, PCIe topology, system RAM, storage, networking, power requirements, cooling condition, and supported software stack.

## Pre-purchase performance-estimation experiment

A central reason to preserve this idea is that Riverview can estimate how a dual-P100 SXM2 32B worker will *feel* before purchasing the server.

Use the current RTX 4090 and PCIe P100 as calibrated measurement points rather than relying only on generic Internet benchmarks.

### Step 1 — Freeze the exact model workload

Record:

- exact 32B model/model file;
- quantization and model format;
- model file/weight size;
- inference runtime and version;
- context size;
- GPU-offload configuration;
- prompt used for the benchmark;
- prompt-token count;
- generated-token count;
- sampling/settings needed to make repeated tests comparable.

### Step 2 — Measure the RTX 4090 baseline

Run the fixed workload on the RTX 4090 and capture at minimum:

- prompt-processing tokens/second;
- generation tokens/second;
- time to first token;
- total wall-clock generation time;
- VRAM usage;
- system-RAM usage attributable to inference;
- GPU utilization and memory activity where available.

The RTX 4090 measurement becomes the subjective and numerical reference for the already-known 'fast enough/faster than reading' interactive experience.

### Step 3 — Measure the current P100 baseline

Run the identical workload on the current P100 and capture the same metrics, plus:

- exact number/proportion of model layers resident on the P100;
- exact layers/weights remaining on CPU/system RAM;
- P100 VRAM occupancy;
- CPU/system-RAM occupancy;
- PCIe/offload behavior if observable.

This determines whether the current poor interactive experience is principally a Pascal/P100 compute limitation or is being heavily penalized by CPU offload because the complete 32B model cannot fit in 16 GB.

### Step 4 — Construct the dual-SXM2 model

Using the measured model/layer sizes, calculate how the same model would partition across two 16 GB P100 SXM2 GPUs.

Determine:

- whether the complete model plus required runtime/KV-cache allocation fits across the pair at the desired context;
- approximate layer allocation per GPU;
- local HBM2 traffic per generated token;
- expected activation/synchronization traffic across NVLink;
- whether the server topology provides a direct/optimal NVLink path for each intended pair;
- likely runtime compatibility and multi-GPU partitioning strategy.

Do not estimate dual-P100 performance by simply multiplying single-P100 tokens/second by two.

### Step 5 — Predict an interactive speed range

Combine the measured single-P100 efficiency, known CPU-offload penalty, model memory footprint, SXM2 local-memory bandwidth, expected NVLink boundary cost, and runtime overhead to derive a conservative/expected/optimistic tokens-per-second range for one 2x P100 SXM2 32B worker.

Express the result both numerically and as a normalized speed index, for example:

- RTX 4090 measured interactive baseline = 100;
- current P100 measured = X;
- predicted 2x P100 SXM2 fully GPU-resident = Y range.

The purpose is not to claim benchmark precision without hardware. The purpose is to determine whether the likely dual-P100 experience falls into a useful subjective class: irritating interactive latency, acceptable agent/conversational latency, or background-only throughput.

### Step 6 — Reproduce the predicted feel on the RTX 4090

If the runtime permits controlled throttling or an equivalent pacing mechanism, deliberately constrain/pacer-limit the RTX 4090's generation output to the predicted dual-P100 tokens/second range.

Then interact with the 32B model at that rate.

This converts an abstract estimate such as '12 tokens/sec' into the practical purchase question: 'Would this response cadence be comfortable enough for the way Riverview will use these workers?'

If direct GPU throttling would alter model behavior or introduce misleading execution characteristics, use output/token pacing solely as a subjective latency simulator and keep it clearly separate from the hardware performance benchmark.

## Evaluation outputs for a future purchase decision

Before acquisition, produce a comparison containing at least:

- measured current P100 performance;
- measured RTX 4090 performance;
- predicted 2x P100 SXM2 performance range;
- predicted number of simultaneous 32B workers on the eight-GPU topology;
- expected aggregate generation throughput;
- interactive usability assessment;
- tokens/sec per dollar;
- useful concurrent workers per dollar;
- estimated power draw and power/cooling implications;
- runtime/software compatibility risks;
- server noise, electrical, cooling, networking, and physical-placement requirements;
- alternative hardware at then-current prices, including newer high-VRAM GPUs and alternative used datacenter accelerators.

The purchase analysis should distinguish **latency** from **throughput**. A server that is slower than the 4090 for one conversation may still be highly valuable if it can sustain four independent 32B workers or many background jobs without consuming the 4090.

## Why it is worth preserving

Riverview is expected to require more local inference capacity than the current development machine can physically host. A complete eight-GPU server at approximately $1,500 delivered could represent unusually inexpensive aggregate VRAM and concurrent compute capacity.

The existing P100's slow subjective performance makes an uninformed purchase risky, but the current hardware also provides the instrumentation needed to reduce that uncertainty before purchase. The proposed calibrated benchmark can answer much of the important question without owning the candidate server.

This makes the concept worth preserving even though engineering capacity is not currently available to perform the investigation.

## Why it is parked now

The Steward cannot presently spare the engineering time required to benchmark the current model, characterize the candidate server topology, evaluate runtime compatibility, and produce a defensible acquisition comparison.

The idea is valuable but is not on Riverview's current execution path. Investigating it now would divert engineering effort from higher-priority active work.

## Promotion condition

Promote for elaboration when one or more of the following becomes true:

- the Steward is actively considering purchase of the 8x P100 SXM2 server or a materially similar machine;
- Riverview reaches the point where current local GPU capacity is a direct blocker to multi-resident or background workloads;
- engineering capacity is available for the controlled 4090/P100 benchmark without disrupting current roadmap work;
- a time-sensitive hardware listing makes a pre-purchase qualification worthwhile; or
- the Steward explicitly directs that this compute-capacity investigation begin.

Promotion means begin the bounded benchmark/acquisition investigation. It does not itself authorize hardware purchase or implementation into Riverview production.

## Explicit non-action

Do not, merely because this item exists:

- purchase the candidate server or any GPU;
- interrupt current Riverview engineering work to benchmark it;
- install or replace inference runtimes;
- alter GPU drivers or current working GPU configuration;
- move existing resident workloads to the P100;
- assume eight P100 GPUs provide one unified 128 GB VRAM pool;
- assume all eight SXM2 GPUs have equivalent/direct NVLink connectivity;
- assume two P100s will provide twice the single-P100 generation speed;
- promote this item to the Ready Bench without Steward approval and the required elaboration.

## Relationship to other Parking Lot work

PL-0002, Alternative Local AI Inference Runtime Paths, is related because runtime choice can materially affect multi-GPU model partitioning, quantization support, P100 compatibility, latency, and throughput.

This item is narrower: it preserves a concrete compute-acquisition hypothesis and the pre-purchase experiment needed to evaluate it. It does not select an inference runtime and does not supersede PL-0002.
