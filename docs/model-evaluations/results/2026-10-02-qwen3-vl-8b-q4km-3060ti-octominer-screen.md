# Qwen3-VL-8B-Instruct Q4_K_M — RTX 3060 Ti — OctoMiner Frozen Screen

## Test identity

- Date: 2026-10-02
- Model: Qwen3-VL-8B-Instruct
- Quantization: Q4_K_M
- Vision projector: Q8_0 mmproj
- Local model path during qualification: `D:\AI_Model_Downloads\Vision_Qualification\3060TI\Qwen3-VL-8B-Instruct-Q4KM`
- Purpose: determine whether a small local vision model can provide useful screenshot OCR and screen-state extraction for OctoMiner BIOS/control work.
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
- Multimodal executable: `llama-mtmd-cli`

The installed winget llama.cpp package was upgraded/installed to b11193, which supplied `llama-mtmd-cli` and the associated llama.cpp command-line tools.

## Measured execution

- Process exit: 0
- Wrapper elapsed time: 124.79 s
- Benchmark SHA-256 before and after: identical

## Evaluation

- Execution status: **PASS**
- Task-quality status: **PASS / strong screenshot OCR + screen-state extraction**
- Qualification: **MODEL 3 QUALIFIED** for the campaign's working vision role.

The model successfully read the frozen OctoMiner/HiveOS screen and recovered important visible state including:

- HiveOS command list
- connection-failure message
- `rig_id`
- server URL
- IP address `192.168.1.160`
- network configuration
- both Tesla P100 GPUs, including memory/VBIOS/power information

This was dramatically better than the earlier GOT-OCR2 result and was sufficient to select Model 3 as the working vision model and continue the BIOS campaign.

## Optimization note

llama.cpp warned that Qwen-VL needs at least 1024 image tokens for grounding accuracy and suggested:

`--image-min-tokens 1024`

The qualifying run did not include that tuning. Retest/tune later if useful, but the recorded campaign decision was explicitly **not to derail the BIOS work for this optimization**.

## Disposition

**QUALIFIED / RETAIN AND DEPLOY.**

Use Qwen3-VL-8B-Instruct Q4_K_M with the Q8_0 mmproj and llama.cpp multimodal/MTMD runtime as the selected Model 3 vision configuration for the current OctoMiner campaign. Preserve the exact runtime/configuration when deploying it. Any later tuning or materially different configuration should be recorded as a separate result rather than overwriting this qualification evidence.
