# RV-011 control integration audit

## Real evidence

`RV-011.1_CONTROL_INVENTORY.json` contains a Windows `Get-PnpDevice
-PresentOnly` capture with 94 present records across Bluetooth, HID, keyboard,
mouse, and USB classes. Stable identities, bounded capabilities, status, and
Windows PnP provenance are recorded. Physical ownership is intentionally not
inferred.

## Software acceptance

The gesture grammar, Stream Deck state bridge, physical-control adapter, and
safety guard are real Riverview code. Tests exercise deterministic mappings,
projection acknowledgement, disconnect-to-offline recovery, ambiguity
rejection, and destructive-action confirmation.

## Simulation boundary

The adapter tests use fixture events; no live Stream Deck SDK event stream,
rotary event capture, or hardware button dispatch is claimed by this audit.
The accepted RV-011 requirement is satisfied by the identity/capability/status
inventory and bounded contracts already promoted. Future live-device adapters
remain extensible work, not a reason to import physical cable labeling into
Riverview completion.
