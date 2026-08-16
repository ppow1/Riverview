# RV-010 browser operator surface

The Riverview-owned service now serves a real browser-rendered operator page at
`/`. It provides bearer entry, a text composer, a browser file picker, client-side
SHA-256 reference generation, submit/status feedback, and visible response,
correlation, and artifact-reference output.

This is a human-facing text-plus-artifact reference surface. The browser hashes
the selected file and submits only a bounded reference; the current reasoning
request does not send image bytes to the provider. Therefore image-content
understanding is NOT PROVEN and must not be implied by the visible response.
Artifact-only requests are rejected because the operator must provide an
instruction describing the requested action.

The page now offers a user-triggered, bounded local microphone capture through
the Windows `System.Speech` provider. Raw audio is discarded after
transcription, and the transcript is placed in the composer for review. This
is an actual local capture path, but RV-010 parent remains pending until Pat
performs the canonical non-keyboard interaction and the resulting evidence is
accepted. Lower-level text reasoning and artifact-reference attachment do not
constitute image understanding or parent experiential acceptance.

Observed browser classification:

- TEXT REASONING: PASS
- ARTIFACT REFERENCE ATTACHMENT: PASS
- IMAGE CONTENT UNDERSTANDING: NOT PROVEN
- ARTIFACT-ONLY REASONING: REJECTED
