# RV-010 final multimodal acceptance action

The deterministic environment is ready. Pat's only required action is:

1. Open `http://127.0.0.1:18082` (the Riverview-owned authenticated Open WebUI endpoint).
2. Submit the phrase `bounded multimodal acceptance` using the completed local
   voice/transcription path.
3. Attach or reference `RV-013.5_SYNTHETIC_RESTORE_FIXTURE.json` through RV-010.4; it contains metadata only and no secret.
4. Confirm the response preserves the request correlation and references the
   accepted artifact.
5. Confirm the bounded notification/status projection records the completion.

No shell, SQL, browser automation, protected payload, or ambient microphone is
required.
