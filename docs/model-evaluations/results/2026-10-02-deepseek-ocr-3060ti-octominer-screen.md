# DeepSeek-OCR — RTX 3060 Ti — OctoMiner Frozen Screen

## Test identity

- Date: 2026-10-02
- Model: DeepSeek-OCR
- Local model path: `D:\AI_Model_Downloads\Vision_Qualification\3060TI\DeepSeek-OCR`
- Purpose: determine whether a small local OCR/vision model can provide high-confidence interpretation of an OctoMiner screen for BIOS/control work.
- Hardware: NVIDIA GeForce RTX 3060 Ti, 8 GB VRAM
- Benchmark image: `OCTO1-1080P-FROZEN.jpg`
- Benchmark SHA-256: `FB81A324F484BF613FD4FB99D128255C2D3430EC5C516DD14A614AFABE74696B`
- Benchmark hash unchanged before/after inference.

## Successful runtime

Isolated environment:

- Python: 3.12.6
- Torch: 2.6.0+cu118
- TorchVision: 0.21.0+cu118
- Transformers: 4.46.3
- CUDA: 11.8
- GPU: NVIDIA GeForce RTX 3060 Ti

Initial pip install selected CPU-only Torch/TorchVision. Replacing those packages from the PyTorch CUDA 11.8 index produced the working CUDA environment. The upstream example specifies FlashAttention 2; this Windows qualification used `_attn_implementation="eager"` instead and did not install FlashAttention.

The first inference attempt loaded the model but failed before inference because an empty `output_path` was supplied and the model's `infer()` implementation unconditionally calls `os.makedirs(output_path)`. Supplying a real output directory fixed that invocation error; no model files were changed.

## Benchmark configuration

- Prompt/mode: `Free OCR.`
- base_size: 640
- image_size: 640
- crop_mode: False
- attention: eager
- This corresponds to the model README's documented Small resolution, with eager attention substituted for FlashAttention 2.

## Measured successful execution

- Python exit: 0
- Total wrapper elapsed: 127.06 s
- Model load: 10.1 s
- Inference: 113.5 s
- VRAM free before load: 6.973 GB
- VRAM free after reported: 0.0 GB; treat as an observation requiring caution rather than a standalone proof of actual post-run availability.

Runtime emitted compatibility warnings including model type/configuration warnings, an uninitialized `model.vision_model.embeddings.position_ids` weight warning, attention-mask/pad-token warnings, and deprecated cache/RoPE API warnings. These are material limitations of this exact tested stack and should be considered when interpreting the result.

## Representative output

The transcription recognized a Linux/root terminal context and produced fragments including:

- `root@ubuntu:/# /bin/bash`
- `root@ubuntu:/# ls -lrt`
- directory names such as `/etc`, `/usr`, `/var`, `/home`, `/root`, `/usr/local`

It then generated a long sequence of repetitive directory-listing-like text with dates, permissions, and malformed `ubuntu:/root` fragments that was not trustworthy as a literal transcription of the benchmark screen.

## Evaluation

- Execution status: **PASS**
- Task-quality status: **FAIL for this configuration/workload**
- Relative observation: output was more structurally coherent than the GOT-OCR2 result on the same frozen benchmark, but it still introduced substantial unsupported/hallucinated content and was far too slow for the intended high-confidence screen/control loop.

## Disposition

Do not use this exact DeepSeek-OCR configuration as the screen-state authority for the OctoMiner BIOS campaign. Do not generalize this result to every DeepSeek-OCR configuration: this test specifically covers RTX 3060 Ti 8 GB, Small 640x640, crop disabled, eager attention, and the frozen OctoMiner benchmark. A future FlashAttention, different resolution/crop mode, preprocessing pipeline, or different workload is a separate test.
