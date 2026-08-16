# RIV-UI-0016: Artifact reference versus content-understanding boundary

This checkpoint applies when a browser or API request carries an artifact
reference but the reasoning provider receives no artifact bytes or inspectable
content. A successful text response is not evidence that an image was seen.

Required distinction:

- `TEXT REASONING: PASS` means the provider answered the text instruction.
- `ARTIFACT REFERENCE ATTACHMENT: PASS` means provenance/hash/reference data
  survived intake.
- `IMAGE CONTENT UNDERSTANDING: NOT PROVEN` means no inspectable image input or
  content-specific evidence was established.
- `ARTIFACT-ONLY REASONING: REJECTED` means the bounded request requires an
  instruction and did not infer intent from the file.

Recovery is to inspect the actual provider envelope and visible operator
behavior. Label references as reference-only, keep classification/provenance,
and do not promote a human experiential or multimodal gate from component/API
tests. A content-understanding claim requires a provider path that demonstrably
receives and uses the artifact content.

Source: `src/riverview/operator/openwebui.py`; Cookbook entry: `RIV-UI-0016`.
