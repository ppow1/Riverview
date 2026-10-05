# SNAIL Handoff — 2026-10-04

This document is the authoritative transition from the historical infrastructure
qualification checkpoint to SNAIL v1.0. Historical campaign records remain evidence and
are not rewritten by this handoff.

## Reconciled campaign position

* **Infrastructure qualification is complete.** DEV hosts the authority and flight recorder;
  Octo2 hosts the disposable Qwen3-Next 80B worker.
* **Candidate C0 is the currently booting baseline.** No supplied evidence establishes a later
  baseline, and no SNAIL-controlled Candidate C1 mutation has begun.
* **Independent observation is proven:** OCTO1 HDMI → video1 → DEV `latest.jpg`.
* **PiKVM HID is proven:** its control path can cause an independently observed OCTO1 console
  change. API acceptance alone is not proof of delivery.
* **DEV/RTX 3060 Ti vision exists, but BIOS-grade complete transcription is
  HARDWARE-UNQUALIFIED.** Original frames remain the authoritative visual evidence.
* **Octo2 monitoring/recovery states exist.** Only boot-ID change proves reboot; transient
  unreachability does not. The worker is stateless and replaceable.
* **Physical OCTO1 power/reset and recovery from a detached PiKVM USB link remain dependent on
  the human Steward** until a separate qualification proves otherwise.

## Acceptance boundary

SNAIL v1.0 is **QUALIFIED FOR OCTO1 BIOS CAMPAIGN PLANNING**. It must not mutate or flash C1,
invoke stock recovery, reset, or power-cycle OCTO1 under this qualification. The next allowed
step is an evidence-based C1 planning proposal packaged for Steward/external review.

## Epistemic rule

OBSERVED evidence is stored immutably. DERIVED conclusions cite evidence IDs. HYPOTHESIS items
remain unproven. Corrections are new append-only events. Continuation comes from durable state,
checkpoints, events, and evidence—never worker conversational memory.
