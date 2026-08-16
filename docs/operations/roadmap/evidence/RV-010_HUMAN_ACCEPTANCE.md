# RV-010 human multimodal operator acceptance

Status: `STEWARD_ACCEPTED`

This evidence records the human-exercised browser acceptance performed by the
Steward against the live Riverview-owned operator surface at
`http://127.0.0.1:18082/`. No bearer value is recorded.

## Evidence levels

- `MACHINE_TESTED`: the bounded API, provider-neutral envelope, correlation,
  classification, artifact-reference, credential handoff, and visible browser
  surface were tested by the implementation suite and live preflight.
- `HUMAN_EXERCISED`: Pat explicitly activated the browser microphone control,
  spoke into the real microphone, reviewed the visible Windows-local
  `System.Speech` transcript, submitted it, and observed a completed local
  provider response. Pat then selected `pro Micro.png` and submitted the same
  voice-originated request with the artifact.
- `STEWARD_ACCEPTED`: Pat accepted the demonstrated path as satisfying RV-010.

## Accepted path

```text
human microphone
  -> explicit browser capture
  -> Windows-local System.Speech transcript
  -> visible transcript review
  -> authenticated Riverview session
  -> bounded reasoning request
  -> ollama:qwen3-coder:30b-qwencode-20k
  -> preserved correlation
  -> visible response
```

The combined request returned `Completed`, preserved the correlation, and
reported the artifact as `reference_only` with a browser artifact SHA-256
reference. The provider did not claim to inspect the image and requested
additional context. This is the intentional current contract: artifact
reference/provenance intake, not image-content reasoning.

The observed System.Speech transcript was imperfect but usable because it was
visible and editable before submission. This single acceptance is not a claim
of production-grade transcription accuracy.

## Explicit non-claims

- No image understanding is claimed.
- No image bytes were silently passed to the reasoning provider.
- No ambient microphone authority exists.
- No bearer token is included in this evidence.
- RV-010 acceptance does not authorize a future vision feature.
