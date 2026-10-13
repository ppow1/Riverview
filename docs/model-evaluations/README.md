# Model Evaluation Registry

**CURRENT DEFAULT STARTUP REFERENCE:** [CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md](../../CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md). Read this before modifying any model launcher, GPU assignment, or service. The validated 32K/8-slot vision profile is **not yet confirmed deployed**.

Purpose: preserve what models we actually tested, on what hardware/runtime, for what task, and how they performed so future model selection starts from measured local evidence instead of repeating downloads and qualification work.

## Operating rule

One test run = one result file in `results/`. Do not grow one giant append-only history file. Individual result files are the durable evidence; this README is the human-readable index and can be regenerated/rebuilt from those files if it becomes large.

Before recommending or downloading a model for a task, search this directory for prior tests of that model, family, quantization, hardware class, and task.

A new result should record, when known:

- model family and exact model/variant
- quantization / precision
- source repository
- test date
- purpose / workload
- hardware topology (GPU model/count and relevant split)
- runtime and important versions
- benchmark/input identity and hash when applicable
- load time, inference time, VRAM observations when measured
- raw or representative output
- execution status
- task-quality assessment
- limitations / anomalies
- setup/compatibility work required to make the model execute, or the blocker if it never executed
- disposition: retain, retest/tune, not useful for this workload, or not qualified

## Current results

| Date | Model | Variant | Hardware | Purpose | Execution | Task result | Result file |
|---|---|---|---|---|---|---|---|
| 2026-10-13 | Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated | i1-IQ3_XS + Q8_0 mmproj, F16 KV | Single P100 16GB (GPU0) | 32K context, 8-way text and image inference; 64K failure modes | **PASS 32K / FAIL 64K** | Text 8/8 at 3336 input tokens; vision 8/8 correct 128×128 images; 144 MiB min free VRAM; 64K F16/Q8 CUDA OOM; production rollout not yet confirmed | [Detailed October 13 trials](results/2026-10-13-huihui-p100-startup-baseline.md) |\n| 2026-10-12–13 | Huihui-Qwen3-VL-30B-A3B | i1-IQ3_XS + Q8_0 mmproj | 19 GPU subsets, then single P100 | 38-config throughput campaign and repeated startup | 36/38 load-ready; single P100 repeat PASS | 8-slot P100 aggregate 110.655–143.018 tok/s in short synthetic runs; original raw host evidence not all in GitHub | [38 configurations](results/2026-10-12-qwen3-vl-30b-gpu-campaign.md), [P100 retest](results/2026-10-12-qwen3-vl-30b-single-p100-retest.md) |\n| 2026-10-02 | GOT-OCR2 | downloaded safetensors model | RTX 3060 Ti 8 GB | OCR / high-confidence interpretation of frozen OctoMiner screen | PASS | FAIL — severely corrupted/incomplete transcription | `results/2026-10-02-got-ocr2-3060ti-octominer-screen.md` |
| 2026-10-02 | DeepSeek-OCR | Small 640x640, no crop, eager attention | RTX 3060 Ti 8 GB | OCR / high-confidence interpretation of frozen OctoMiner screen | PASS | FAIL for tested configuration — recognized terminal context but hallucinated substantial content; 113.5 s inference | `results/2026-10-02-deepseek-ocr-3060ti-octominer-screen.md` |
| 2026-10-02 | Qwen3-VL-8B-Instruct | Q4_K_M + Q8_0 mmproj; llama.cpp b11193/Vulkan | RTX 3060 Ti 8 GB | Vision / screenshot OCR + OctoMiner screen-state extraction | PASS | **QUALIFIED — strong screenshot OCR + screen-state extraction; selected Model 3 working vision configuration; 124.79 s** | `results/2026-10-02-qwen3-vl-8b-q4km-3060ti-octominer-screen.md` |
| 2026-10-02 | Penguin-VL-8B | BF16 upstream safetensors + separate Penguin-Encoder; attempted CPU/GPU offload | RTX 3060 Ti 8 GB | Vision / high-confidence interpretation of frozen OctoMiner screen | FAIL before inference | NOT TESTED for quality — incompatible Transformers APIs blocked model loading after dependency and encoder recovery | `results/2026-10-02-penguin-vl-8b-3060ti-octominer-screen.md` |
| 2026-10-12 | Qwen3-VL-30B | Exact quantization/hash not captured in monitor | RTX 4090 / RTX 3060 Ti / 1–4× P100 (19 subsets × 4/8 slots) | Text-only inference speed, startup and 1–8 request concurrency | 36 load PASS; 2 load FAIL | **Performance baseline only; not customer-support or vision qualified**. 4090 alone ~107 single / ~192 eight-way aggregate; single P100 ~50 single and 6.45–7.01s reported load; 3060 Ti alone failed to load; 8-slot 3060 Ti mixtures fail at N≥5 | [38-config campaign](results/2026-10-12-qwen3-vl-30b-gpu-campaign.md) |
| 2026-10-11 | Qwen3-Next-80B-A3B-Instruct | Q4_K_M GGUF | RTX 4090 / RTX 3060 Ti / 4× P100 (11 GPU subsets) | Inference generation throughput, loading, 1–4 request concurrency | 9 load PASS; 2 load timeouts | **Performance baseline, not task-quality qualification**; B3 44.58 tok/s single and 70.419 aggregate four-way; D1 32.25 single and 54.82 four-way | [initial A-series](results/2026-10-11-qwen3-next-80b-gpu-campaign-initial.md), [UUID-corrected B/C/D](results/2026-10-11-qwen3-next-80b-gpu-campaign-uuid.md) |

### October 12, 2026 — Qwen3-VL-30B text-only GPU campaign

- [Full campaign performance record](results/2026-10-12-qwen3-vl-30b-gpu-campaign.md)
- Source host evidence: `/root/qwen30b-gpu-campaign/run-20261012-175106` (not yet transferred to GitHub).
- **Next investigation:** repeat single-P100 startup with actual process cold starts, cache control, VRAM/CPU-offload capture and realistic multi-turn support sessions.


### October 11, 2026 — 80B GPU performance campaign

- [Interactive performance visual](assets/2026-10-11-80b-benchmark-visual.html) (HTML source; open in a browser to view)
- [Generation-sorted results CSV](assets/2026-10-11-80b-results-sorted.csv)
- [Exact observed launch commands, methodology and evidence capture gaps](2026-10-11-80b-reproducibility.md)
- [Original A-series run record](results/2026-10-11-qwen3-next-80b-gpu-campaign-initial.md)
- [UUID-corrected B/C/D run record](results/2026-10-11-qwen3-next-80b-gpu-campaign-uuid.md)

**Best measured single-request generation:** A3 45.86 tok/s (concurrency 2 failed). **Best four-way aggregate:** B3 70.419 tok/s (4090 + 2 P100). **P100-only four-way:** D1 54.82 tok/s (4 P100). The tests do not qualify reasoning quality. The original binary ZIP and full host logs still require transfer; this registry does not falsely represent those uncollected bytes as committed.

### Current campaign vision selection (October 2 historical qualification; not the October 13 Grace vision default)

**Qwen3-VL-8B-Instruct Q4_K_M is the qualified Model 3 selection for the current OctoMiner campaign.** The qualifying configuration used llama.cpp b11193/Vulkan with the Q8_0 mmproj on the RTX 3060 Ti. The run completed successfully in 124.79 seconds and recovered substantial, correct screen state from the frozen HiveOS/OctoMiner benchmark.

Optimization remains available: llama.cpp recommended `--image-min-tokens 1024` for Qwen-VL grounding accuracy. This was not required for the qualification decision and should not block the BIOS campaign.

## Design intent

This registry is not a model archive. Models can normally be downloaded again from their upstream source. What is expensive and easy to lose is our empirical knowledge: what we tried, what hardware it ran on, what configuration was required, and whether it actually solved our problem.

Future comparisons may include 3060 Ti, P100, multi-P100/split configurations, OctoMiner configurations, larger GPU combinations, different quantizations, and different runtimes. Those differences must be recorded rather than treating a model name alone as a test result.


### October 13, 2026 — Huihui 30B final single-P100 context and vision qualification

- [Canonical Riverview AI model startup/loading configuration](../../CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md) — startup target, exact paths, GPU UUID, live verification, and deployment status.
- [Full Huihui P100 validation chronology](results/2026-10-13-huihui-p100-startup-baseline.md) — 8K baseline; 32K startup; 64K F16 and Q8 failures; rejected overlong 6847-token prompts; corrected 8-way text pass; 8-way image pass and sampled GPU memory.
- **Validated candidate:** `-c 32768 -np 8` on GPU0 P100. **Not verified as deployed**. The last inspected production launcher was `-c 8192 -np 4`.
- **Scope warning:** Vision success used 128×128 synthetic PNGs and 1405-token requests, with only 144 MiB free at sampled peak. Larger images, full-slot multimodal load and endurance are not qualified.
- The older October 2 Qwen3-VL-8B Model 3 BIOS-screen qualification remains historical and is not the current Huihui Grace vision service.
