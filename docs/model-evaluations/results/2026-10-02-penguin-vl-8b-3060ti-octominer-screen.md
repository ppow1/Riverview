# Penguin-VL-8B — RTX 3060 Ti — OctoMiner Frozen Screen

## Test identity

- Date: 2026-10-02
- Model: Tencent Penguin-VL-8B
- Architecture: `PenguinVLQwen3ForCausalLM` / model type `penguinvl_qwen3`
- Local model path: `D:\AI_Model_Downloads\Vision_Qualification\3060TI_EXPERIMENTAL\Penguin-VL-8B`
- Downloaded model payload: 25 repository files, 4 safetensor shards, approximately 16.132 GB
- Purpose: determine whether Penguin-VL-8B can provide high-confidence interpretation of an OctoMiner screen for BIOS/control work on the RTX 3060 Ti using CPU/GPU offload where required.
- Hardware: NVIDIA GeForce RTX 3060 Ti, 8 GB VRAM
- Benchmark image: `OCTO1-1080P-FROZEN.jpg`
- Benchmark SHA-256: `FB81A324F484BF613FD4FB99D128255C2D3430EC5C516DD14A614AFABE74696B`
- Benchmark hash remained unchanged throughout the attempted runs.

## Packaging and dependencies discovered

Penguin-VL-8B is not self-contained. Its configuration references a separate vision encoder repository:

- `tencent/Penguin-Encoder`
- Local encoder downloaded during qualification: `D:\AI_Model_Downloads\Vision_Qualification\3060TI_EXPERIMENTAL\Penguin-Encoder`
- Encoder payload observed after clone: 9 top-level files, including `model.safetensors`, approximately 0.822 GB

The encoder repository was confirmed publicly reachable with `git ls-remote`. An online Transformers lookup nevertheless returned HTTP 401 because the local Hugging Face OAuth token was expired, so the encoder was cloned directly and the benchmark harness redirected `config.vision_encoder` to the local encoder path without modifying the downloaded Penguin-VL-8B model files.

## Environment work required

An isolated Python 3.12 environment was created for Penguin. Missing processor dependencies discovered and installed included:

- OpenCV (`cv2`, provided by `opencv-python`)
- decord 0.6.0
- ffmpeg Python bindings
- imageio 2.38.0

The initially installed Transformers 5.18.0 was incompatible with Penguin's custom processor: `PenguinVLQwen3Processor._get_arguments_from_pretrained()` implements the older method signature and failed when Transformers supplied an additional positional processor argument.

Transformers was therefore pinned to 4.57.3. That allowed processor initialization to progress and model construction to begin.

## Final attempted execution

Execution mode: local Penguin-VL-8B plus local Penguin-Encoder, BF16 with intended automatic CPU/GPU placement/offload.

Final attempt observations:

- Python exit: 1
- Wrapper elapsed time: 9.1 s
- CUDA available: True
- GPU: NVIDIA GeForce RTX 3060 Ti
- VRAM free before load: 6.973 GB
- VRAM total: 7.999 GB
- Original encoder reference: `tencent/Penguin-Encoder`
- Local encoder substitution was accepted and the loader reported: `Detected nested encoder keys in checkpoint, adding key mapping for vision_encoder`
- Model load then failed before inference with: `TypeError: PreTrainedModel._load_pretrained_model() got an unexpected keyword argument 'offload_state_dict'`

This exposed a second Transformers API compatibility mismatch: the older Transformers generation needed by Penguin's processor did not match the API expected by Penguin's custom model loader.

## Evaluation

- Execution status: **NOT QUALIFIED — SOFTWARE COMPATIBILITY FAILURE**
- Task-quality status: **NOT TESTED**
- No inference/transcription was produced, so this result must not be interpreted as evidence that Penguin's vision quality is good or bad.
- The qualification campaign stopped here rather than expanding into another compatibility-development effort, because the immediate goal was comparative model qualification for the BIOS campaign.

## Disposition

Do not select this exact Penguin-VL-8B Windows/RTX-3060-Ti stack for the current BIOS campaign. Preserve the model as an experimental candidate if desired, but any future attempt should begin from this compatibility record rather than repeating dependency discovery. A future known-good Penguin runtime, container, Linux environment, patched upstream release, or different Transformers combination would be a separate test and should receive its own result file.
