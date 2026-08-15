# RIV-UI-0012 — Authenticated voice/remote channel

The bounded local acceptance channel requires an explicit bearer, correlation,
closed classification, and local provider. It never opens an ambient microphone,
persists bearer material, or exposes execution authority.

Recovery is to reject the request, inspect only bounded identity/classification
metadata, and retry through the authenticated local contract.
