<!-- Version: 1.0.0 | Date: 2026-09-22 | Status: CAPTURED -->
# PL-0015 — Hermes Multimodal Vision Accuracy, Latency, and Context-Aware Follow-Up

## Parking Lot metadata

- **ID:** PL-0015
- **Idea/title:** Hermes Multimodal Vision Accuracy, Latency, and Context-Aware Follow-Up
- **Category:** Hermes / Local AI / Vision / Multimodal Architecture
- **Priority:** High
- **Originator:** Steward
- **Date captured:** 2026-09-22
- **Status:** CAPTURED
- **Explicit non-action:** This item preserves the remaining Hermes vision accuracy and optimization work. Parking it does not authorize further prompt tuning, model replacement, gateway redesign, or interruption of higher-priority Steward work.

## Executive summary

Hermes now has a working local multimodal architecture. The important architectural objective was achieved: an image can enter Hermes, be analyzed by a local vision model, and provide visual evidence to the Octominer-hosted 80B reasoning model while preserving Hermes conversation and tool behavior.

The remaining problem is narrower than the original project. A representative browser-tab counting test returned **6** when the correct answer was **7** in the integrated Hermes path, even though a direct task-focused Qwen3-VL benchmark had previously returned **7** correctly. This is now an accuracy/prompt/orchestration tuning problem rather than a missing multimodal capability.

This work is parked because the architecture is useful in its current state and continued optimization is not presently worth displacing BIOS work and other higher-priority Steward projects.

## Current proven architecture

The accepted working topology at capture time is:

```text
Hermes
  -> main OpenAI-compatible endpoint: http://localhost:8092/v1
  -> HermesVisionGateway.ps1
       -> text/reasoning: Octominer 2 llama.cpp 80B
       -> multimodal gateway vision when used: local Qwen3-VL
  -> auxiliary.vision directly to local Ollama OpenAI endpoint
       -> qwen3-vl:8b-instruct
```

Key runtime locations and identities:

- Hermes install: `A:\AI\Tools\Hermes\hermes-agent`
- Hermes config: `A:\AI\Tools\Hermes\data\config.yaml`
- Gateway: `A:\Riverview\standalone\HermesVisionGateway.ps1`
- Gateway endpoint: `http://localhost:8092/v1`
- Ollama vision endpoint: `http://localhost:11434/v1`
- Vision model: `qwen3-vl:8b-instruct`
- Octominer 2 reasoning endpoint: `http://192.168.1.162:8080/v1/chat/completions`
- Reasoning model: `Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf`
- Hermes context length: 65,536

At capture time the Windows gateway was also configured as the scheduled task `Riverview Hermes Multimodal Gateway` for restart/startup resilience.

## Work completed before parking

### Gateway and reasoning path

The gateway was brought to a known-good state supporting:

- text-only requests to the Octominer 80B model;
- image requests through local Qwen3-VL with an authoritative vision handoff to the 80B model;
- OpenAI-compatible SSE streaming;
- forwarding of `tools` and `tool_choice`;
- Hermes tool-call loops.

A text-only streaming defect was repaired by routing text completions through the same completion/SSE handling path rather than the earlier JSON-only response path.

The vision-to-reasoning handoff wording that proved reliable was intentionally specific:

```text
An upstream vision model has already read the image.

The exact text extracted from the image is:

<vision description>

Use the extracted text above to answer the user's request.
```

Earlier attempts to generalize this wording produced incorrect behavior, so future work should not casually replace the proven handoff.

### Vision model selection

The earlier `llava:7b` path was rejected after unreliable instruction following and poor reading of a controlled vision fixture.

`qwen3-vl:8b-instruct` was then tested directly and correctly read the controlled fixture text:

`VISION TEST 4729`

The complete gateway image path also returned the same exact text.

### End-to-end recovery tests

A permanent/portable multimodal self-test was built at:

`A:\Riverview\standalone\Test-HermesMultimodal.ps1`

The final portable test reached **11 PASS / 0 FAIL / OVERALL PASS**, including a real Hermes tool loop.

Portable fixture:

`A:\Riverview\standalone\test-assets\hermes-vision-test.png`

Fixture SHA256 at capture:

`2A719F00A78F3BEFDE9107570BA874FEFA91843E9CC09B99244C329F3D8FDDB3`

Portable self-test SHA256 recorded during the work:

`C23F08F6B3AC2B9705CC9B2FA3FF5BDD1984D094C27D3B91B0412A1B057CB589`

A recovery package was subsequently published to Riverview; `main` at parking capture was commit `1483101ac626675f4688d3616de1d915b7809ca5`, titled **Add repeatable Hermes multimodal gateway recovery package**.

## Latency investigation and optimization

The original integrated image path was doing substantially more work than necessary.

Observed earlier browser-log timing:

- vision preprocessing: approximately **86.8 seconds**;
- subsequent main-model request: approximately **42.8 seconds**;
- combined major model stages: approximately **129.6 seconds**.

The architecture was effectively causing unnecessary repeated 80B participation around vision preprocessing.

Hermes v0.20.5 source inspection showed support for a dedicated auxiliary vision provider. The configuration was changed to use local Qwen3-VL directly:

```yaml
auxiliary:
  vision:
    provider: custom
    model: qwen3-vl:8b-instruct
    base_url: http://localhost:11434/v1
```

A direct OpenAI-compatible test of this endpoint passed.

After that change, observed timing for the same general workflow dropped to approximately:

- vision preprocessing: **31.2 seconds**;
- final main-model stage: **18.2 seconds**;
- combined model stages: approximately **49.3 seconds**.

This established that the architecture change itself materially reduced latency.

## Discovery of the remaining vision-prompt bottleneck

Source inspection found that Hermes automatic image preprocessing used a fixed exhaustive prompt in `cli.py`:

`A:\AI\Tools\Hermes\hermes-agent\cli.py`

The function is:

`_preprocess_images_with_vision(self, text, images, ...)`

The important discovery was that the function already receives the user's current text, but the stock implementation did not use that text to focus the vision request. Instead it requested a thorough description of essentially everything visible.

A direct benchmark against the same Qwen3-VL model demonstrated the consequence:

- exhaustive Hermes-style description: roughly **20–31 seconds**, producing thousands of characters;
- task-focused prompt asking how many browser tabs were open: approximately **5.756 seconds**, answer **7**, correct;
- an over-constrained alternative prompt: approximately **5.431 seconds**, answer **6**, incorrect.

This showed both sides of the remaining problem: task-focused vision can be dramatically faster, but seemingly reasonable prompt constraints can also change visual interpretation and reduce accuracy.

## Context-aware preprocessing patch

A bounded patch was applied to:

`A:\AI\Tools\Hermes\hermes-agent\cli.py`

Backup:

`A:\AI\Tools\Hermes\hermes-agent\cli.py.before-context-aware-vision`

The patch changed automatic preprocessing so that:

- when the user supplies text, the vision prompt focuses on visual evidence relevant to that message;
- when an image arrives without accompanying text, Qwen3-VL performs concise general reconnaissance so the 80B model can use existing conversation context to infer why the image was supplied;
- exact text, numbers, errors, status indicators, code, and relevant UI state are preferentially preserved;
- exhaustive unrelated description is discouraged.

Patch verification at installation:

- old prompt remaining: **0**
- new context-aware markers present
- Python syntax check: **PASS**

This design intentionally supports three Steward workflows:

1. image plus an explicit question;
2. image plus commentary/instruction;
3. image pasted without text after the preceding conversation has established what the image is for.

The third case is particularly important: image-only submission should not cause context amnesia or force the Steward to repeat an instruction that is already evident from the conversation.

## Current integrated test result

After the context-aware patch, Hermes successfully analyzed the browser screenshot and responded without the former multi-minute delay.

For the representative question asking how many tabs were visible, the integrated response was:

`There are 6 tabs visible in the browser.`

The correct count was **7**.

This is the principal unresolved defect being parked.

The result should not be interpreted as failure of the multimodal architecture. The same local Qwen3-VL model had already returned **7** correctly in a direct task-focused benchmark. The next investigation therefore needs to compare the exact integrated preprocessing prompt/result with the successful direct benchmark and determine where the interpretation diverges.

## Desired future behavior

The intended architecture remains:

**Qwen3-VL = fast eyes; Octominer 80B = contextual brain.**

The desired normal path is:

1. Always perform a fast useful first visual pass.
2. If the user supplied a specific question/instruction, focus the first pass on evidence needed for it.
3. If the image has no accompanying text, provide concise reconnaissance rather than exhaustive narration; let the 80B use conversation history to infer intent.
4. Preserve the local image path so the 80B can request a deeper `vision_analyze` pass if the first pass is insufficient.
5. Do not make every image pay the latency cost of exhaustive visual description.
6. Do not over-constrain visual prompts in ways that manufacture false certainty or suppress legitimate visual elements.

## Questions for future investigation

When this item is promoted, begin with evidence rather than redesign.

1. Capture the exact vision prompt and Qwen3-VL response produced by the integrated 6-tab case.
2. Compare that request with the direct 7-tab benchmark request using the same screenshot/model.
3. Determine whether the error originates in Qwen3-VL's first pass, the text passed to the 80B, or the 80B's interpretation.
4. Test a small set of prompt formulations without encoding browser-tab-specific assumptions into the general vision architecture.
5. Determine whether a fast first pass plus optional targeted second pass gives better reliability than attempting one universal prompt.
6. Test the image-only conversational-continuation case explicitly.
7. Test image-plus-commentary, not only image-plus-question.
8. Decide whether deliberate `vision_analyze` deep inspection should retain a more exhaustive prompt while automatic preprocessing stays concise.
9. Measure end-to-end timing from logs; do not infer duration from the TUI's coarse status display.
10. Re-run the portable multimodal self-test after any future source/configuration change.

## Known distractions / non-causes

Hermes has repeatedly emitted a background Honcho warning involving a refused localhost:8000 connection. No evidence gathered during this work established it as the cause of the principal image latency, so it should not be used as the starting theory for this parked item without new evidence.

The extra `model.model` entry referencing a Huihui Qwen3-VL 30B abliterated model was observed in configuration, but the proven auxiliary vision path uses ordinary `qwen3-vl:8b-instruct`. Do not switch vision models merely because the unused/suspicious entry exists.

## Recovery / preservation notes

Before future work, re-read current Riverview `AI_HINTS.md` and the current Hermes recovery material rather than relying on this artifact as the only authority.

The context-aware `cli.py` modification lives under the Hermes installation rather than the Riverview repository. Before upgrading/reinstalling Hermes, preserve or reproduce that patch deliberately; an upstream update may overwrite it.

A known-good snapshot was created during the broader work under:

`A:\Riverview\standalone\known-good\2026-09-22-hermes-multimodal`

However, future work must verify whether that snapshot contains the final direct-`auxiliary.vision` configuration and final context-aware source patch before treating the snapshot as complete. Do not assume it does.

## Why it is parked now

The multimodal capability is operational enough to be useful. Continuing to optimize a one-tab counting discrepancy would consume time needed for BIOS work and other higher-priority Steward projects after this Hermes effort already expanded far beyond its intended duration.

The correct action is therefore to preserve the evidence, architecture, patches, successful tests, known defect, and next diagnostic steps so work can resume later without rediscovery.

## Promotion condition

Promote for elaboration/active work when any of the following occurs:

- vision accuracy becomes a practical blocker in normal Hermes use;
- image-only contextual continuation proves unreliable enough to interfere with work;
- latency again becomes operationally unacceptable;
- a Hermes upgrade requires deliberate reintegration of the local vision changes;
- the Steward explicitly directs resumption of multimodal accuracy/optimization work.

## Explicit non-action

Parking this item does not authorize further prompt experimentation, swapping vision models, modifying the known-good gateway, changing Octominer inference configuration, or redesigning Hermes.

When resumed, start from the captured working architecture and reproduce the **6-versus-7** discrepancy before changing anything.
