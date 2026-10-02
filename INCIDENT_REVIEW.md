# Incident Review — Model 3 Qualification Registry Contradiction

**Date:** 2026-10-02  
**Status:** Open for later review  
**Purpose:** Preserve what was observed, what went wrong, what is known, and what is not known. This document intentionally does **not** prescribe governance changes or a final response. The incident should be reconsidered later when there is more distance from the event.

## Executive summary

During the OctoMiner BIOS campaign, four candidate vision models were tested on an RTX 3060 Ti against a frozen 1080p OctoMiner/HiveOS benchmark image. Model 3, Qwen3-VL-8B-Instruct Q4_K_M with a Q8_0 multimodal projector running under llama.cpp b11193/Vulkan, completed successfully and produced substantially better screenshot OCR and screen-state extraction than the earlier candidates.

At the time of the test, the result was explicitly evaluated as **PASS / strong screenshot OCR + screen-state extraction**, and the explicit campaign decision was that **Model 3 was qualified**. The assistant stated that it would record that result.

Later, when the model-evaluation registry was consulted, the durable registry entry instead described the same Model 3 result as **UNQUALIFIED for BIOS authority**. There was no intervening failed retest, changed benchmark, changed runtime, changed hardware, revised acceptance criterion, qualification-revocation decision, or other observed event that justified changing the qualification from QUALIFIED to UNQUALIFIED.

The contradiction was caught by the Steward from memory and by scrolling back to the original test discussion. The primary evidence showed that the Steward's recollection was correct and the registry was wrong.

The incorrect registry and Model 3 result file were subsequently corrected on GitHub. The corrected registry identifies Model 3 as the qualified working vision selection for the current OctoMiner campaign.

The central concern is not merely that an incorrect summary was produced. The assistant participated in the test, interpreted the evidence, explicitly made the qualification decision, stated that it would record that decision, wrote the durable record, and later relied on its own incorrect durable record to contradict the original correct decision. The same system therefore participated in every major stage of the information chain in which the contradiction was introduced and later trusted.

## Context

The OctoMiner BIOS campaign had reached a point where the existing vision path was not considered adequate for the intended work. Four candidate models were evaluated so that a better local vision model could be selected for use with the RTX 3060 Ti and later integrated into the Hermes/80B orchestration and closed-loop PiKVM/video test rig.

The model-evaluation registry under `docs/model-evaluations/` was created specifically to preserve empirical test knowledge so future work would not repeat downloads, qualification work, or rely on conversational memory.

The registry therefore had a high-trust role: it was intended to be the durable representation of what had actually been tested and decided.

## Model 3 test result as originally established

The relevant candidate was:

- Model: Qwen3-VL-8B-Instruct
- Quantization: Q4_K_M
- Vision projector: Q8_0 mmproj
- Runtime: llama.cpp b11193
- Backend: Vulkan
- Hardware: NVIDIA RTX 3060 Ti, 8 GB
- Benchmark: frozen 1080p OctoMiner/HiveOS screen
- Process exit: 0
- Wrapper elapsed time: 124.79 seconds

The model successfully recovered substantial visible state from the benchmark, including the HiveOS command list, connection-failure information, rig ID, server URL, IP address `192.168.1.160`, network configuration, and information for both Tesla P100 GPUs including memory/VBIOS/power data.

The contemporaneous evaluation was explicitly:

- **PASS / strong screenshot OCR + screen-state extraction**
- **Model 3 is qualified**

An optimization note was also recorded: llama.cpp recommended `--image-min-tokens 1024` for improved Qwen-VL grounding accuracy. That optimization was explicitly treated as something that could be tested later and **not** as a reason to derail or block the BIOS work.

## What the durable registry later said

When the registry was consulted later in the same working session, its Model 3 row stated in substance that execution passed but the model was:

**UNQUALIFIED for BIOS authority**

The corresponding result record also carried the incorrect unqualified disposition.

This directly contradicted the qualification decision made from the test evidence.

## Why this was not a legitimate state transition

No evidence has been identified that would support the transition:

`QUALIFIED -> UNQUALIFIED`

Specifically, between the qualification decision and discovery of the incorrect registry entry, there was no identified:

- failed Model 3 retest;
- changed benchmark image;
- changed benchmark hash;
- changed model configuration that was being treated as the same qualification result;
- changed hardware relevant to the recorded test;
- newly discovered output defect sufficient to revoke the qualification;
- revised acceptance criterion;
- explicit qualification revocation;
- campaign decision declaring Model 3 unsuitable.

The team continued to Model 4 because the four-model evaluation was being completed, not because Model 3 had failed.

Therefore, based on the evidence reviewed during this incident, there is no known evidentiary or logical chain that explains the durable record changing from the explicit QUALIFIED decision to UNQUALIFIED.

## How the incident was discovered

Later, while returning to the campaign work, the assistant initially began reasoning from an older Qwen/Ollama vision stack. The Steward stopped that path and directed the assistant to the model-evaluation registry under the Riverview documentation.

The assistant retrieved the registry and found the incorrect UNQUALIFIED entry. It then made a second serious error: it treated that derived registry entry as authoritative and told the Steward that the Steward's recollection that Model 3 had qualified was inconsistent with the registry.

The Steward then produced the contemporaneous conversation/test evidence showing that Model 3 had explicitly been declared qualified.

Reviewing that evidence established that the registry, not the Steward's recollection, was wrong.

## Assistant failure during retrieval

The incident therefore contains two distinct failures:

### 1. Recording failure

A correct observed result and explicit qualification decision were transformed into an incorrect durable status.

The assistant was involved in the testing, interpretation, qualification decision, and creation of the durable record. The incorrect value was not inherited from an unrelated third-party source.

### 2. Retrieval/reasoning failure

When the incorrect durable summary was later retrieved, the assistant trusted it over the primary evidence and over the Steward's correct recollection instead of recognizing the conflict and tracing it back to the underlying test result.

This amplified the original recording error and temporarily made the corrupted derived record appear more authoritative than the event it was supposed to summarize.

## Integrity evidence did not protect semantic correctness

During the broader campaign workflow, hashes and Git commit identifiers were used to provide integrity and provenance evidence.

This incident demonstrates an important limitation of that evidence: a SHA or commit can prove that a particular byte sequence was written and preserved, but it does not prove that the semantic content of those bytes accurately represents the decision that was supposed to be recorded.

In this case, integrity evidence could have faithfully protected an already incorrect semantic value.

That distinction is important because the workflow can otherwise create a strong appearance of verification even when the error occurred before hashing or committing.

## Why the incident is concerning

The concern is broader than the words QUALIFIED and UNQUALIFIED.

The two states were binary and materially opposed, which made this instance comparatively easy to recognize once the original evidence was inspected. A similar silent mutation could theoretically involve any critical project fact, such as:

- enabled versus disabled;
- source versus destination;
- read versus write;
- OctoMiner 1 versus OctoMiner 2;
- before versus after;
- an IP address;
- a drive letter;
- a BIOS value;
- a hardware assignment;
- a pass/fail result;
- a command target.

The Steward's concern is therefore not simply whether this particular registry entry has been corrected. The concern is how such a contradiction can be detected reliably without requiring the Steward to manually reread and verify every durable record written by the assistant.

That question remains open.

## What is known about the cause

The exact mechanism that caused the qualification value to change is **not known**.

It would be inappropriate to claim that the incident was caused by context compression, subscription tier, summarization, model configuration, memory behavior, or any other specific mechanism without evidence tracing the generation of the incorrect record.

What can be said from the evidence is:

1. The primary Model 3 test succeeded.
2. The contemporaneous interpretation was positive.
3. The explicit decision was QUALIFIED.
4. The assistant stated that the result would be recorded.
5. The later durable registry/result record said UNQUALIFIED.
6. No intervening evidence or decision justifying revocation has been identified.
7. The assistant later trusted the incorrect derived record and initially contradicted the correct original result.
8. The Steward detected the inconsistency.
9. The primary evidence was re-examined and confirmed the original QUALIFIED decision.
10. The GitHub registry was corrected.

Anything beyond those points about the internal cause remains hypothesis rather than established fact.

## Potential consequence if it had not been caught

The exact downstream consequence cannot be known because the incident was caught before the campaign proceeded on the false status.

However, the incorrect registry had already influenced the assistant's reasoning. On retrieval, the assistant used the UNQUALIFIED entry to conclude that none of the four tested models had qualified and began steering away from deploying Model 3.

Had the Steward not challenged that conclusion, the project could have unnecessarily repeated model evaluation, pursued a less suitable model, continued troubleshooting Model 4, reverted to an older inadequate vision path, or otherwise made subsequent technical decisions from a false premise.

The more general risk is that a similarly incorrect durable fact in a less obvious domain might propagate farther before being noticed.

## Corrective action already completed

The immediate factual record was corrected on GitHub.

The Model 3 result now records:

- execution PASS;
- task-quality PASS / strong screenshot OCR + screen-state extraction;
- **MODEL 3 QUALIFIED**;
- disposition **QUALIFIED / RETAIN AND DEPLOY**.

The model-evaluation registry README now identifies Qwen3-VL-8B-Instruct Q4_K_M as the qualified Model 3 selection for the current OctoMiner campaign and preserves the tested llama.cpp b11193/Vulkan + Q8_0 mmproj configuration.

The final registry correction commit reported during the incident was:

`935576af6637ccf6ccb3b5fef72ff54e09b3d76c`

This correction repairs the immediate project fact. It does not by itself resolve the larger reliability concern raised by the incident.

## Deferred questions for later review

No decision on these questions is being made in this incident document. They are preserved for later consideration:

- How was the incorrect UNQUALIFIED value generated from an explicitly QUALIFIED decision?
- Can the exact turn or artifact-generation step that introduced the contradiction be reconstructed?
- Was the error introduced in the individual result record, the index, or both at the same generation step?
- What other durable records produced in the same period may warrant targeted comparison against their primary evidence?
- What level of independent verification is appropriate for company-critical facts without requiring the Steward to manually audit every assistant-written artifact?
- How should integrity hashes and Git commits be interpreted when semantic correctness must also be established?
- Is this incident isolated, or does it share a common failure pattern with other recent cases where the assistant appeared to stop the evidence chain too early or select a derived fact over primary evidence?
- Is there any evidence that the user's recent change from a Business subscription to Plus is relevant? At present, no causal connection has been established and one should not be assumed.

## Review posture

This document is intentionally a factual incident record rather than a governance proposal.

The Steward explicitly chose to defer major decisions until later rather than react while frustrated by the event. No broader architectural, governance, subscription, or workflow decision should be inferred from the existence of this document.

When this incident is revisited, the review should begin from the primary Model 3 test evidence, the original qualification statement, the erroneous registry version if recoverable from Git history, the corrected registry, and the relevant Git commits. The goal should be to distinguish demonstrated facts from hypotheses about why the contradiction occurred.
