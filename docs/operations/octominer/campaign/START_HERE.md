# OCTOMINER 1 BIOS CAMPAIGN — START HERE

## Purpose

This directory is the durable GitHub recovery point for the OCTOMINER 1
Multi-P100 BIOS Automation Campaign.

Do not reconstruct this campaign from chat history or memory.

## Authoritative Local Working Repository

On the DEV workstation:

T:\OctoMiner_BIOS_Campaign\repo

The local campaign repository is the active working copy.

This Riverview directory is a durable recovery/reference checkpoint.

## Mandatory Reground Procedure

Before designing or executing the next campaign test:

1. Go to:

   T:\OctoMiner_BIOS_Campaign\repo

2. Run:

   python controller\build_reground_packet.py

3. Read:

   REGROUND_PACKET.md

4. Treat the campaign documents and recorded evidence as authoritative.

Conversational memory is not a substitute for campaign grounding.

## Governing Document

APPROVED_PROPOSAL.md

This defines the campaign objective, architecture, roles, interfaces,
contracts, seams, evidence requirements, roadmap, and definition of finished.

## Core Campaign Records

- APPROVED_PROPOSAL.md
- REGROUND_CONTRACT.md
- REGROUND_PACKET.md
- CAMPAIGN_STATE.md
- PROVEN_FACTS.md
- PROVEN_NOT_WORKING.md
- LESSONS_LEARNED.md
- OPEN_QUESTIONS.md

## Reground Builder

The active builder is:

T:\OctoMiner_BIOS_Campaign\repo\controller\build_reground_packet.py

A checkpoint copy is stored here as:

build_reground_packet.py

## Control / Observation Architecture

Control path:

DEV / campaign controller
    -> PiKVM
    -> USB HID
    -> OCTOMINER1

Independent visual observation path:

OCTOMINER1 HDMI
    -> video1 capture
    -> DEV
    -> machine perception / evidence

OCTOMINER1 SSH is an operating-system diagnostic and telemetry path.
It is not a substitute for independent visual proof.

## Critical Rule

A command being accepted is not proof that the intended physical or BIOS
state change occurred.

Action and observation must remain independently verifiable.

## GitHub Location

Repository:

ppow1/Riverview

Path:

docs/operations/octominer/campaign/

If the local T: campaign location is ever lost or forgotten, begin here.
