# RIV-UI-0017: Human operator acceptance lineage

This checkpoint applies when a component/API implementation has to be
distinguished from a real Steward-exercised operator interaction.

Record three separate states:

1. `MACHINE_TESTED` — bounded contracts and diagnostics pass.
2. `HUMAN_EXERCISED` — the actual browser, microphone, artifact control, and
   visible response were used by a person.
3. `STEWARD_ACCEPTED` — the Steward accepts that exact demonstrated path.

Do not infer human acceptance from unit tests, fixture transcription, API
requests, or a prepared procedure. Preserve imperfect-but-usable transcription
quality as a limitation rather than overstating it. Preserve artifact
`reference_only` semantics and do not claim image understanding unless the
provider demonstrably receives and uses image content.

Source: `docs/operations/roadmap/evidence/RV-010_HUMAN_ACCEPTANCE.md`.
