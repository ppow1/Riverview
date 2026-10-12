# October 12 — Qwen3-VL-30B IQ3_XS single P100 retest

**Host:** OCTOMINER2; **GPU:** Tesla P100-PCIE-16GB, UUID `GPU-ace423ce-ae61-803e-0734-a907283efe54`.

**Run:** `/root/qwen30b-p100-retest/run-20261012-193725`. Campaign finished 19:41:02 EDT. Source archive supplied in conversation: `riverview-qwen30b-p100-retest.tar.gz` (23 KB). **Source archive is NOT yet committed to GitHub; do not mistake this record for the raw logs.** Original 38-config source archive supplied: `riverview-qwen30b-20261012-original.tar.gz` (337 KB); also NOT yet committed.

## Direct observations from uploaded `results.jsonl`

- First process restart readiness: **7.16 seconds** (`process_cold_4slots`); **OS file cache NOT cleared**.
- GPU0 after readiness: **13,716 MiB occupied**, 2,554 MiB free. Other GPUs remained essentially idle (~8–14 MiB each), indicating the worker ran on the designated P100; inspect detailed llama-server logs for GPU layer placement.
- Eight-slot concurrency N=8, repetition 1: **1,280 tokens in 11.568 seconds = 110.655 aggregate tok/s**, 0/8 request failures. Individual request generation ~14.13–15.11 tok/s.
- Eight-slot concurrency N=8, repetition 2: **1,280 tokens in 8.950 seconds = 143.018 aggregate tok/s**, 0/8 failures. Individual request generation ~18.86 tok/s.
- Synthetic prompt: `Explain transformer inference, attention, KV caching, and autoregressive token generation in technical detail.`; 160 maximum output tokens; 4 and 8 server slots; context configured to 8192 tokens.

## Qualification

**RETAIN as performance evidence; NOT qualified for customer-support quality, true storage-cold startup, or 16K/32K context.** Repeat with realistic multi-turn customer-support prompts, long contexts, token-streaming first-token timing, OS-cache controls, and GPU/CPU memory and layer allocation capture.

## Raw evidence preservation gap

The archives were successfully uploaded into the ChatGPT conversation, but the available GitHub connector supports text file creation and Git objects, not direct transfer of these local binary tar.gz files. The archives must still be pushed via a host with GitHub access or another binary-capable upload workflow. Do not claim raw evidence is in GitHub until verified there.
