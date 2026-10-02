# Qwen3-VL-8B-Instruct Q4_K_M — RTX 3060 Ti — OctoMiner Frozen Screen

## Test identity

- Date: 2026-10-02
- Model: Qwen3-VL-8B-Instruct
- Quantization: Q4_K_M
- Vision projector: Q8_0 mmproj
- Local model path during qualification: `D:\AI_Model_Downloads\Vision_Qualification\3060TI\Qwen3-VL-8B-Instruct-Q4KM`
- Purpose: determine whether a small local vision model can provide sufficiently exact, high-confidence interpretation of an OctoMiner screen for BIOS/control work.
- Hardware: NVIDIA GeForce RTX 3060 Ti, 8 GB VRAM
- Benchmark image: `OCTO1-1080P-FROZEN.jpg`
- Benchmark SHA-256: `FB81A324F484BF613FD4FB99D128255C2D3430EC5C516DD14A614AFABE74696B`
- Benchmark hash verified unchanged before and after execution.

## Runtime

- Runtime: llama.cpp b11193
- Backend: Vulkan
- GPU: NVIDIA GeForce RTX 3060 Ti
- Model file: `Qwen3VL-8B-Instruct-Q4_K_M.gguf`
- Vision projector: `mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf`

The Windows machine initially had no suitable llama.cpp multimodal executable on the expected path. The installed winget llama.cpp package was upgraded/installed to b11193, which supplied `llama-mtmd-cli` and the associated llama.cpp command-line tools.

## Measured execution

- Process exit: 0
- Wrapper elapsed time: 124.79 s
- Benchmark SHA-256 before and after: identical

## Evaluation

- Execution status: **PASS**
- Task-quality status: **FAIL / UNQUALIFIED for BIOS-control authority**
- Observation: using the 1080p frozen benchmark substantially improved the transcription compared with lower-quality vision attempts, but the result was still not exact, complete, and dependable enough to drive BIOS-control decisions without independent confirmation.
- Qualification recorded from this campaign: `3060TI_VISION_FOR_BIOS=UNQUALIFIED`.

The complete raw transcription was not preserved in the registry source available when this durable record was created, so this entry intentionally does not reconstruct or invent it. The measured execution status and qualification outcome are preserved.

## Disposition

Qwen3-VL-8B-Instruct Q4_K_M is runnable on the RTX 3060 Ti with llama.cpp/Vulkan and is materially more useful than a model that cannot execute, but this exact tested configuration is **not qualified as the high-confidence OctoMiner BIOS screen-state authority**. Retain the configuration and result as evidence; a different quantization, projector, preprocessing method, resolution, runtime/backend, prompt, or workload should be recorded as a separate test rather than overwriting this result.
