# PL-0008 — Bambu P2S Physical Fabrication Capability Gap

Date: 2026-08-28
Status: PRESERVED FOLLOW-ON / NOT RESIDENT-ACCESSIBLE

## Scope

This is a bounded follow-on item from resident occupational acceptance. It does
not begin the larger Grace/Hermes/ChatGPT closed-loop project and does not add
printer control, CAD generation, slicing, or execution authority.

The Steward reports access to a Bambu Lab P2S 3D printer. A read-only forensic
inspection of the authoritative Riverview checkout and inspected predecessor
Estate assets found no authoritative Riverview resource record, printer profile,
printer-control adapter, slicer integration, STL/3MF pipeline, readiness
telemetry, Bambu/P2S credential boundary, or Cookbook operating procedure.

## Classification

| Layer | Current state | Evidence boundary |
|---|---|---|
| Resource awareness | NOT FOUND / user-reported only | No authoritative physical-resource registry record |
| Material capability | UNKNOWN | PLA suitability is not registered as Riverview evidence |
| Availability/readiness | UNKNOWN | No printer telemetry or readiness source |
| Ownership/location | Steward-reported, not registered | No durable Riverview projection |
| Control capability | NOT IMPLEMENTED | No printer transport, credentials, or control adapter |
| Design/fabrication reasoning | PARTIAL | Grace can reason over a future resource projection; no physical-resource projection is active |
| CAD/geometry generation | NOT FOUND | No resident-accessible bounded capability |
| STL/3MF generation/validation | NOT FOUND | No resident-accessible bounded capability |
| Slicing/print preparation | NOT FOUND | No resident-accessible bounded capability |
| Printer submission/control | NOT FOUND | Must remain unavailable and unclaimed |
| Monitoring/result evidence | NOT FOUND | Must remain unavailable and unclaimed |
| Roadmap/UI mentions | PROMISED/DESIGNED | Not operational capability evidence |

## Required future decomposition

1. Resource awareness: represent a Bambu P2S as an authoritative physical
   resource with explicit manufacturer/model/type/material facts and UNKNOWN
   values for unverified fields.
2. Fabrication reasoning: allow model reasoning to compare material, geometry,
   build volume, quantity, tolerance, and available resource evidence.
3. CAD/geometry generation: a separate specialist capability with bounded
   artifacts and validation.
4. Slicing/print preparation: a separate specialist capability with explicit
   printer/profile/material evidence.
5. Printer control: a separately authorized execution capability with credential
   and transport boundaries.
6. Monitoring/result: a separate operational capability for readiness, print
   state, completion, failure, and evidence.

Each layer must be proven independently. No layer implies the next layer.

## Acceptance rule

Grace must not say that she can access, control, send to, or print on the Bambu
P2S until an authoritative Riverview resource projection and corresponding
bounded capability/binding exist. Generic model knowledge about Bambu, PLA,
GitHub, CAD, or 3D printing is not institutional access.

For a future PLA request, valid behavior is:

- use authoritative physical-resource evidence if present;
- reason over suitability through the active model/package path;
- ask for legitimate domain requirements;
- prepare a governed request without claiming print execution;
- preserve UNKNOWN for unverified printer facts;
- stop at Steward authorization and execution boundaries.

Do not implement a PLA/Bambu keyword route, printer phrase route, or resource
selection state machine.
