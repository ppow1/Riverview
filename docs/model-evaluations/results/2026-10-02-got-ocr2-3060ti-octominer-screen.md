# GOT-OCR2 — RTX 3060 Ti — OctoMiner Frozen Screen

## Test identity

- Date: 2026-10-02
- Model: GOT-OCR2
- Local model path during test: `D:\AI_Model_Downloads\Vision_Qualification\3060TI\GOT-OCR2`
- Purpose: determine whether a small local vision/OCR model can provide very-high-confidence interpretation of an OctoMiner screen/screenshot for autonomous/assisted BIOS work.
- Hardware: NVIDIA GeForce RTX 3060 Ti, 8 GB VRAM
- Benchmark image: `OCTO1-1080P-FROZEN.jpg`
- Benchmark SHA-256: `FB81A324F484BF613FD4FB99D128255C2D3430EC5C516DD14A614AFABE74696B`
- Benchmark hash verified unchanged before and after inference.

## Runtime that successfully executed

The model required an isolated compatibility environment rather than the machine's current global Python stack.

- Python: 3.10.11
- NumPy: 1.26.4
- Torch: 2.0.1+cu118
- TorchVision: 0.15.2+cu118
- Transformers: 4.37.2
- tiktoken: 0.6.0
- verovio: 4.3.1
- CUDA available: True
- GPU: NVIDIA GeForce RTX 3060 Ti

Earlier attempts exposed compatibility/dependency issues including missing `verovio`, incompatibility with the newer Transformers cache API, and NumPy 2.x incompatibility with the selected Torch/TorchVision stack. The final isolated environment executed successfully.

## Measured execution

- Python exit: 0
- Wrapper elapsed time: 6.7 s
- Model load time: 2.30 s
- Inference time: 1.88 s
- VRAM free before reported by test: 7,486,832,640 bytes
- VRAM free after reported as 0; treat this particular post-test measurement as suspect/unverified rather than proof of literal zero free VRAM.

## Raw transcription

`Furstron-f∩╝êf)┬╖force1rgstup,re-enterIDandpassword,URlUsitional 11:59`

The UTF-8 rerun was necessary because the first successful inference produced Unicode that the Windows CP1252 console could not print. That first print failure was an output-encoding problem, not an inference failure.

## Evaluation

- Execution status: **PASS**
- Task-quality status: **FAIL**
- Result: substantial corruption, missing structure, and incomplete/garbled recognition. Some fragments resembling `force`, `re-enter ID and password`, `URL`, and `11:59` were recovered, but the output is not suitable for the required high-confidence screen-state interpretation.

## Disposition

Do not select GOT-OCR2 as the current vision/OCR authority for the OctoMiner BIOS-screen use case based on this test. Preserve the result so future model searches do not repeat this qualification under the same conditions. A materially different preprocessing pipeline, runtime, prompt/mode, or workload would constitute a separate test rather than overwriting this result.
