# Model Evaluation Registry

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
| 2026-10-02 | GOT-OCR2 | downloaded safetensors model | RTX 3060 Ti 8 GB | OCR / high-confidence interpretation of frozen OctoMiner screen | PASS | FAIL — severely corrupted/incomplete transcription | `results/2026-10-02-got-ocr2-3060ti-octominer-screen.md` |
| 2026-10-02 | DeepSeek-OCR | Small 640x640, no crop, eager attention | RTX 3060 Ti 8 GB | OCR / high-confidence interpretation of frozen OctoMiner screen | PASS | FAIL for tested configuration — recognized terminal context but hallucinated substantial content; 113.5 s inference | `results/2026-10-02-deepseek-ocr-3060ti-octominer-screen.md` |
| 2026-10-02 | Qwen3-VL-8B-Instruct | Q4_K_M + Q8_0 mmproj; llama.cpp b11193/Vulkan | RTX 3060 Ti 8 GB | Vision / screenshot OCR + OctoMiner screen-state extraction | PASS | **QUALIFIED — strong screenshot OCR + screen-state extraction; selected Model 3 working vision configuration; 124.79 s** | `results/2026-10-02-qwen3-vl-8b-q4km-3060ti-octominer-screen.md` |
| 2026-10-02 | Penguin-VL-8B | BF16 upstream safetensors + separate Penguin-Encoder; attempted CPU/GPU offload | RTX 3060 Ti 8 GB | Vision / high-confidence interpretation of frozen OctoMiner screen | FAIL before inference | NOT TESTED for quality — incompatible Transformers APIs blocked model loading after dependency and encoder recovery | `results/2026-10-02-penguin-vl-8b-3060ti-octominer-screen.md` |
| 2026-10-11 | Qwen3-Next-80B-A3B-Instruct | Q4_K_M GGUF | RTX 4090 / RTX 3060 Ti / 4× P100 (11 GPU subsets) | Inference generation throughput, loading, 1–4 request concurrency | 9 load PASS; 2 load timeouts | **Performance baseline, not task-quality qualification**; B3 44.58 tok/s single and 70.419 aggregate four-way; D1 32.25 single and 54.82 four-way | [initial A-series](results/2026-10-11-qwen3-next-80b-gpu-campaign-initial.md), [UUID-corrected B/C/D](results/2026-10-11-qwen3-next-80b-gpu-campaign-uuid.md) |

| 2026-10-12 | InternVL3-78B | Q4_K_M + Q8_0 mmproj; llama.cpp CUDA | 4× P100 + RTX 4090 + RTX 3060 Ti | Engineering drawing + visual-canon proportions | PASS at 4K; 16K vision OOM | **FAIL / NOT QUALIFIED — did not perform requested five-part proportional analysis; 4K context truncates conversations** | [result](results/2026-10-12-internvl3-78b-q4km-six-gpu-vision.md) |

### October 11, 2026 — 80B GPU performance campaign

- [Interactive performance visual](assets/2026-10-11-80b-benchmark-visual.html) (HTML source; open in a browser to view)
- [Generation-sorted results CSV](assets/2026-10-11-80b-results-sorted.csv)
- [Exact observed launch commands, methodology and evidence capture gaps](2026-10-11-80b-reproducibility.md)
- [Original A-series run record](results/2026-10-11-qwen3-next-80b-gpu-campaign-initial.md)
- [UUID-corrected B/C/D run record](results/2026-10-11-qwen3-next-80b-gpu-campaign-uuid.md)

**Best measured single-request generation:** A3 45.86 tok/s (concurrency 2 failed). **Best four-way aggregate:** B3 70.419 tok/s (4090 + 2 P100). **P100-only four-way:** D1 54.82 tok/s (4 P100). The tests do not qualify reasoning quality. The original binary ZIP and full host logs still require transfer; this registry does not falsely represent those uncollected bytes as committed.

### Current campaign vision selection

**Qwen3-VL-8B-Instruct Q4_K_M is the qualified Model 3 selection for the current OctoMiner campaign.** The qualifying configuration used llama.cpp b11193/Vulkan with the Q8_0 mmproj on the RTX 3060 Ti. The run completed successfully in 124.79 seconds and recovered substantial, correct screen state from the frozen HiveOS/OctoMiner benchmark.

Optimization remains available: llama.cpp recommended `--image-min-tokens 1024` for Qwen-VL grounding accuracy. This was not required for the qualification decision and should not block the BIOS campaign.

## Design intent

This registry is not a model archive. Models can normally be downloaded again from their upstream source. What is expensive and easy to lose is our empirical knowledge: what we tried, what hardware it ran on, what configuration was required, and whether it actually solved our problem.

Future comparisons may include 3060 Ti, P100, multi-P100/split configurations, OctoMiner configurations, larger GPU combinations, different quantizations, and different runtimes. Those differences must be recorded rather than treating a model name alone as a test result.
