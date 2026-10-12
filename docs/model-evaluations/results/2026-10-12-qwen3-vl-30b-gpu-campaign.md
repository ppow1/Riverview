# October 12, 2026 — Qwen3-VL-30B text-only GPU campaign

**Status:** FINISHED 2026-10-12 19:12:17 EDT; monitor last updated 19:15:56. **Qualification:** text-only inference throughput, load readiness and concurrency baseline; NOT vision or customer-support answer-quality qualification.

## Source and scope

- Host: OCTOMINER2 (SSH alias `octo1`).
- Original run directory: `/root/qwen30b-gpu-campaign/run-20261012-175106`.
- Monitor: 726 events; 19 GPU subsets × two slot counts (4 and 8) = 38 configurations.
- Hardware: RTX 4090 24GB, RTX 3060 Ti 8GB, four Tesla P100 16GB.
- Model identified by campaign as Qwen3-VL-30B, used in **text-only** mode. The original launcher supplied in the conversation identifies model file `/opt/model-library/vision/Qwen3-VL-30B-A3B/Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.i1-IQ3_XS.gguf`, projector `Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.mmproj-Q8_0.gguf`, and binary `/opt/llama.cpp/build-octo1-0.4.1-dev/bin/llama-server`; model hash, runtime build revision, exact deployed controller source, and full raw logs still require collection from the host.
- Results: 36 load-ready, two load failures (3060 Ti alone at both slot counts). Completion does not mean all concurrency tests passed.

## Representative measurements

Numbers are observed approximate generation speed per request at N=1, and aggregate generated tokens per wall second at N=8; **these are different metrics**. Aggregate numbers refer to 8-slot tests unless otherwise stated.

| GPUs | N=1 per-request generation | N=8 aggregate | Load readiness | Notes |
|---|---:|---:|---:|---|
| RTX 4090 only | ~107 tok/s | ~192 tok/s | 69.18–74.12s | 8 slots successful |
| RTX 4090 + 1 P100 | ~82 tok/s | 193.10–227.83 tok/s | 46.07–46.12s | 8 slots successful; replicate variability |
| RTX 4090 + 4 P100 | ~48 tok/s | 102.02–109.97 tok/s | 59.10–60.10s | 8 slots successful |
| RTX 3060 Ti only | — | — | FAILED | Both slot counts failed load |
| RTX 3060 Ti + 1 P100 | ~56 tok/s | 101.78–102.28 tok/s **at 4 slots** | 30.06–30.50s | 8-slot N=5 and N=8 failed |
| RTX 4090 + RTX 3060 Ti | ~85 tok/s (4 slots) | ~142 tok/s **at 4 slots** | 68.63–69.11s | 8-slot N=8 failed; inspect logs |
| Single P100 | ~50 tok/s | ~127 tok/s (approx., across repeated 8-slot tests) | 6.452–7.012s | Prime on-demand candidate; verify real cold start |
| 2 P100 | — | ~85–101 tok/s | 35.50–35.56s | Load successful |
| 3 P100 | — | — | 45.07s | Load successful |
| 4 P100 | — | — | 50.08–50.09s | Load successful |
| RTX 4090 + RTX 3060 Ti + 4 P100 | ~48 tok/s | ~84 tok/s **at 4 slots** | 60.14–61.12s | 8-slot N=5 and N=8 failed |

## Observations and caveats

1. The RTX 4090 alone is the fastest observed single-request worker (~107 tok/s). Adding slower GPUs for one split model frequently **reduces** performance, despite increasing total VRAM.
2. A single P100 showed unusually low reported `load_ready` time (~6–7s). This is **not proof** of process-cold model load from storage or of full GPU residency. Confirm quantization, mmap/page cache, CPU offload, GPU VRAM allocation, service restart and readiness criteria.
3. Many eight-slot configurations involving the 3060 Ti fail when simultaneous requests rise to five or eight. Four-slot configurations can queue eight requests and often succeed. Root cause is **unknown**; do not label it OOM without server/journal evidence.
4. This test does not measure prompt ingestion, time-to-first-token, real conversational latency, memory isolation, retrieval quality, customer-support accuracy or vision performance.
5. The launcher source is available in the conversation, but original results.jsonl, server logs, runtime binary version, service configuration, and model hash have not been collected from the host. They remain on the source host until separately collected. This document does **not** claim their archival.

## Follow-up: single-P100 retest (discuss before executing)

- Capture exact model identity, GGUF metadata/quantization, checksum, runtime flags and GPU/CPU offload placement.
- Distinguish warm service response, service-restart readiness, process cold load and OS-page-cache-cold startup.
- Record GPU VRAM, RAM, disk reads, readiness and first-token latency; stream tokens.
- Repeat single-client and 2/4/8-client loads with genuine multi-turn customer-support prompts and independent sessions; compare a single P100 against separate P100 workers.
- Preserve raw JSONL, logs, scripts, monitor and hashes in the same evidence style as October 11.

**Disposition:** RETAIN as text-only performance baseline; RETEST single P100; investigate 3060 Ti eight-slot failures; do not qualify customer-service deployment yet.
