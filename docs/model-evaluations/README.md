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
| 2026-10-02 | Qwen3-VL-8B-Instruct | Q4_K_M + Q8_0 mmproj; llama.cpp b11193/Vulkan | RTX 3060 Ti 8 GB | Vision / high-confidence interpretation of frozen OctoMiner screen | PASS | UNQUALIFIED for BIOS authority — 1080p improved transcription substantially, but not exact/complete/dependable enough | `results/2026-10-02-qwen3-vl-8b-q4km-3060ti-octominer-screen.md` |
| 2026-10-02 | Penguin-VL-8B | BF16 upstream safetensors + separate Penguin-Encoder; attempted CPU/GPU offload | RTX 3060 Ti 8 GB | Vision / high-confidence interpretation of frozen OctoMiner screen | FAIL before inference | NOT TESTED for quality — incompatible Transformers APIs blocked model loading after dependency and encoder recovery | `results/2026-10-02-penguin-vl-8b-3060ti-octominer-screen.md` |

## Design intent

This registry is not a model archive. Models can normally be downloaded again from their upstream source. What is expensive and easy to lose is our empirical knowledge: what we tried, what hardware it ran on, what configuration was required, and whether it actually solved our problem.

Future comparisons may include 3060 Ti, P100, multi-P100/split configurations, OctoMiner configurations, larger GPU combinations, different quantizations, and different runtimes. Those differences must be recorded rather than treating a model name alone as a test result.
