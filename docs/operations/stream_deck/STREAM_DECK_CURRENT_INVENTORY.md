# Stream Deck Current Inventory

Captured from the live installed Stream Deck configuration on 2026-08-24T10:09:49-04:00. This is a snapshot, not a substitute for re-inventory: Pat’s manual edits make the installed configuration under `C:\\Users\\wille\\AppData\\Roaming\\Elgato\\StreamDeck\\ProfilesV3` the runtime truth.

## Capture scope

- Stream Deck application: 7.5.1.22901
- Installed root: `C:\Users\wille\AppData\Roaming\Elgato\StreamDeck`
- Profiles root: `C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\ProfilesV3`
- Backup root: `C:\Users\wille\AppData\Roaming\Elgato\StreamDeck-Backups`
- Physical device: model `20GAT9902`, UUID string `@(1)[4057/143/A00NA32533KHWX]`
- Profiles discovered: 7
- Profiles applicable to the physical device: 6
- Active pages discovered: 17
- Occupied keys captured: 243

The excluded installed profile is the `Default Profile` with UUID `3733aa16-1f06-4c1b-913c-2b6cf44d653b`, device model `AI Stream Deck`; it is retained in the inventory but is not part of the physical-device profile ring.

## Complete discovered profile inventory

| Display name | UUID | Physical applicable | Device model | Active pages | Occupied keys | Native profile directory |
|---|---|---:|---|---:|---:|---|
| Windows Shutdown Menu XL | 09a1eef6-a278-4adb-8a88-4b78702db3ee | yes | 20GAT9902 | 1 | 9 | C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\ProfilesV3\09A1EEF6-A278-4ADB-8A88-4B78702DB3EE.sdProfile |
| Default Profile | 3733aa16-1f06-4c1b-913c-2b6cf44d653b | no | AI Stream Deck | 1 | 0 | C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\ProfilesV3\3733AA16-1F06-4C1B-913C-2B6CF44D653B.sdProfile |
| Riverview | 7c0c9d36-8b7f-4d71-9d45-2b6b1c05d0a1 | yes | 20GAT9902 | 1 | 7 | C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\ProfilesV3\7C0C9D36-8B7F-4D71-9D45-2B6B1C05D0A1.sdProfile |
| Roku2 | 9c576814-c3e0-4d5b-9b5d-dda437f9a89a | yes | 20GAT9902 | 10 | 118 | C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\ProfilesV3\9C576814-C3E0-4D5B-9B5D-DDA437F9A89A.sdProfile |
| WinToolsXL | b5b58f76-aea8-4822-b0d8-f51525c44692 | yes | 20GAT9902 | 1 | 32 | C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\ProfilesV3\B5B58F76-AEA8-4822-B0D8-F51525C44692.sdProfile |
| Estate Operations v0.5 Plugin | d4abffcd-7bde-4db7-856b-b26823e1780b | yes | 20GAT9902 | 1 | 29 | C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\ProfilesV3\D4ABFFCD-7BDE-4DB7-856B-B26823E1780B.sdProfile |
| Default Profile | f40cbb56-817f-48c5-908f-a9e5f9eec0a8 | yes | 20GAT9902 | 2 | 48 | C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\ProfilesV3\F40CBB56-817F-48C5-908F-A9E5F9EEC0A8.sdProfile |

## Physical profile ring as currently installed

The six applicable profiles are numbered from the current installed ring, starting at Riverview and following the currently installed NEXT target:

| 1 | Riverview | 7c0c9d36-8b7f-4d71-9d45-2b6b1c05d0a1 | d4abffcd-7bde-4db7-856b-b26823e1780b | f40cbb56-817f-48c5-908f-a9e5f9eec0a8 |
| 2 | Default Profile | f40cbb56-817f-48c5-908f-a9e5f9eec0a8 | 7c0c9d36-8b7f-4d71-9d45-2b6b1c05d0a1 | 9c576814-c3e0-4d5b-9b5d-dda437f9a89a |
| 3 | Roku2 | 9c576814-c3e0-4d5b-9b5d-dda437f9a89a | f40cbb56-817f-48c5-908f-a9e5f9eec0a8 | b5b58f76-aea8-4822-b0d8-f51525c44692 |
| 4 | WinToolsXL | b5b58f76-aea8-4822-b0d8-f51525c44692 | 9c576814-c3e0-4d5b-9b5d-dda437f9a89a | 09a1eef6-a278-4adb-8a88-4b78702db3ee |
| 5 | Windows Shutdown Menu XL | 09a1eef6-a278-4adb-8a88-4b78702db3ee | b5b58f76-aea8-4822-b0d8-f51525c44692 | d4abffcd-7bde-4db7-856b-b26823e1780b |
| 6 | Estate Operations v0.5 Plugin | d4abffcd-7bde-4db7-856b-b26823e1780b | 09a1eef6-a278-4adb-8a88-4b78702db3ee | 7c0c9d36-8b7f-4d71-9d45-2b6b1c05d0a1 |

Ring validation at capture: **passes** for the six applicable profiles. The audit rule is: every profile must have valid PREVIOUS and NEXT targets, following NEXT from the start must visit every applicable profile exactly once and return to start, following PREVIOUS must do the same, and PREVIOUS(NEXT(i)) plus NEXT(PREVIOUS(i)) must return to i. This document records the result; it does not modify the installed configuration.

### Navigation/action coordinates

| Profile | UUID | PROFILE PREVIOUS coordinate/target | PROFILE NEXT coordinate/target | PAGE PREVIOUS coordinates | PAGE NEXT coordinates |
|---|---|---|---|---|---|
| Windows Shutdown Menu XL | 09a1eef6-a278-4adb-8a88-4b78702db3ee | 7,1 -> b5b58f76-aea8-4822-b0d8-f51525c44692 | 7,2 -> d4abffcd-7bde-4db7-856b-b26823e1780b | none | none |
| Riverview | 7c0c9d36-8b7f-4d71-9d45-2b6b1c05d0a1 | 7,1 -> d4abffcd-7bde-4db7-856b-b26823e1780b | 7,2 -> f40cbb56-817f-48c5-908f-a9e5f9eec0a8 | 5,3 | 7,3 |
| Roku2 | 9c576814-c3e0-4d5b-9b5d-dda437f9a89a | 7,1 -> f40cbb56-817f-48c5-908f-a9e5f9eec0a8; 7,1 -> f40cbb56-817f-48c5-908f-a9e5f9eec0a8; 7,1 -> f40cbb56-817f-48c5-908f-a9e5f9eec0a8; 7,1 -> f40cbb56-817f-48c5-908f-a9e5f9eec0a8; 7,1 -> f40cbb56-817f-48c5-908f-a9e5f9eec0a8; 7,1 -> f40cbb56-817f-48c5-908f-a9e5f9eec0a8; 7,1 -> f40cbb56-817f-48c5-908f-a9e5f9eec0a8; 7,1 -> f40cbb56-817f-48c5-908f-a9e5f9eec0a8; 7,1 -> f40cbb56-817f-48c5-908f-a9e5f9eec0a8; 7,1 -> f40cbb56-817f-48c5-908f-a9e5f9eec0a8 | 7,2 -> b5b58f76-aea8-4822-b0d8-f51525c44692; 7,2 -> b5b58f76-aea8-4822-b0d8-f51525c44692; 7,2 -> b5b58f76-aea8-4822-b0d8-f51525c44692; 7,2 -> b5b58f76-aea8-4822-b0d8-f51525c44692; 7,2 -> b5b58f76-aea8-4822-b0d8-f51525c44692; 7,2 -> b5b58f76-aea8-4822-b0d8-f51525c44692; 7,2 -> b5b58f76-aea8-4822-b0d8-f51525c44692; 7,2 -> b5b58f76-aea8-4822-b0d8-f51525c44692; 7,2 -> b5b58f76-aea8-4822-b0d8-f51525c44692; 7,2 -> b5b58f76-aea8-4822-b0d8-f51525c44692 | 5,3, 5,3, 5,3, 5,3, 5,3, 5,3, 5,3, 5,3, 5,3, 5,3 | 7,3, 7,3, 7,3, 7,3, 7,3, 7,3, 7,3, 7,3, 7,3, 7,3 |
| WinToolsXL | b5b58f76-aea8-4822-b0d8-f51525c44692 | 7,1 -> 9c576814-c3e0-4d5b-9b5d-dda437f9a89a | 7,2 -> 09a1eef6-a278-4adb-8a88-4b78702db3ee | none | none |
| Estate Operations v0.5 Plugin | d4abffcd-7bde-4db7-856b-b26823e1780b | 7,1 -> 09a1eef6-a278-4adb-8a88-4b78702db3ee | 7,2 -> 7c0c9d36-8b7f-4d71-9d45-2b6b1c05d0a1 | 5,3 | 7,3 |
| Default Profile | f40cbb56-817f-48c5-908f-a9e5f9eec0a8 | 7,1 -> 7c0c9d36-8b7f-4d71-9d45-2b6b1c05d0a1; 7,1 -> 7c0c9d36-8b7f-4d71-9d45-2b6b1c05d0a1 | 7,2 -> 9c576814-c3e0-4d5b-9b5d-dda437f9a89a; 7,2 -> 9c576814-c3e0-4d5b-9b5d-dda437f9a89a | 5,3, 5,3 | 7,3, 7,3 |

Current capture confirms Pat’s manual change on **Windows Shutdown Menu XL**: its profile controls are at manifest coordinates `7,1` (previous) and `7,2` (next). This snapshot must be treated as authoritative over earlier Riverview-generated inventories.

Native `com.elgato.streamdeck.profile.rotate` actions are explicit Switch Profile actions with a target UUID; they are not intrinsically previous/next. The labels and target assignment create the ring.

## Per-profile physical grids

These grids include every active page and every occupied key captured from the live manifests. Action UUIDs are included so a future repair can distinguish profile navigation, page navigation, and plugin/system actions.

### Windows Shutdown Menu XL — 09a1eef6-a278-4adb-8a88-4b78702db3ee

Device: 20GAT9902; applicable to physical 20GAT9902: yes; active pages: 1.

#### Page 95b37824-35a0-4391-9891-b90fc32620b9 (9 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | · | · | · | · | Lock [com.elgato.streamdeck.multiactions.routine] | · | Sleep [com.elgato.streamdeck.multiactions.routine] | ·
R2 | · | · | · | Confirm [com.elgato.streamdeck.multiactions.routine] | Shut / Down / Menu [com.elgato.streamdeck.system.hotkey] | Cancel [com.elgato.streamdeck.multiactions.routine] | · | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | · | · | · | · | Reboot [com.elgato.streamdeck.multiactions.routine] | · | Sign Out [com.elgato.streamdeck.multiactions.routine] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | · | · | · | ·
```


### Default Profile — 3733aa16-1f06-4c1b-913c-2b6cf44d653b

Device: AI Stream Deck; applicable to physical 20GAT9902: no; active pages: 1.

#### Page 25082b33-9860-4486-99d4-537f1be87a0b (0 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | · | · | · | · | · | · | · | ·
R2 | · | · | · | · | · | · | · | ·
R3 | · | · | · | · | · | · | · | ·
R4 | · | · | · | · | · | · | · | ·
```


### Riverview — 7c0c9d36-8b7f-4d71-9d45-2b6b1c05d0a1

Device: 20GAT9902; applicable to physical 20GAT9902: yes; active pages: 1.

#### Page 7c0c9d36-8b7f-4d71-9d45-2b6b1c05d0a1 — Riverview (7 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | RIVERVIEW / RUNTIME [com.riverview.operator.runtime] | QUEST / DEV [com.riverview.operator.quest-dev] | QUEST / CAST [com.riverview.operator.quest-cast] | · | · | · | · | ·
R2 | · | · | · | · | · | · | · | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | · | · | · | · | · | · | · | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | · | ◀ PAGE [com.elgato.streamdeck.page.previous] | · | PAGE ▶ [com.elgato.streamdeck.page.next]
```


### Roku2 — 9c576814-c3e0-4d5b-9b5d-dda437f9a89a

Device: 20GAT9902; applicable to physical 20GAT9902: yes; active pages: 10.

#### Page b9a23f77-64be-4b84-885b-7715bd89b421 (30 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | DeepFLive / Banana [com.elgato.streamdeck.system.open] | OBS / Banana [com.elgato.streamdeck.system.open] | Voicemeet. / Banana [com.elgato.streamdeck.system.open] | / / EQ / [com.elgato.streamdeck.system.open] | Recording / (68) [com.elgato.streamdeck.soundboard.playaudio] | Recording / (88) [com.elgato.streamdeck.soundboard.playaudio] | Recording / (93) [com.elgato.streamdeck.soundboard.playaudio] | Recording / (95) [com.elgato.streamdeck.soundboard.playaudio]
R2 | cam / [com.elgato.obsstudio.transitionstudio] | Start / [com.elgato.streamdeck.multiactions.routine] | Stop / [com.elgato.streamdeck.multiactions.routine] | Modify Setting [com.barraider.vmmodify] | grab / [com.elgato.obsstudio.screenshot] | on / [com.funky.rokuremotejs.poweron] | off / [com.funky.rokuremotejs.poweroff] | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | center [com.vivremotion.mousecontrol.plugin] | · | Alor [com.funky.rokuremotejs.app] | RST [com.barraider.wintools.shutdown] | Google / Chrome [com.elgato.streamdeck.system.close] | Ping [com.barraider.wintools.ping] | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | Mute/Unmute [com.barraider.vmmicrophone] | Mute/Unmute [com.barraider.vmmicrophone] | · | Shutdown/Restart Co... [com.barraider.wintools.shutdown] | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```

#### Page 6f8d0d99-26f2-4912-bde2-2ddce28e5017 (8 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | · | DeepFaceL. [com.elgato.streamdeck.system.open] | · | · | · | · | · | ·
R2 | · | · | · | · | · | · | · | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | · | · | · | · | · | · | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```

#### Page 5d1d0b05-de3c-472a-aeac-e37730e3df6a (10 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | · | OBS [com.elgato.streamdeck.system.open] | · | · | · | · | · | ·
R2 | · | cam / [com.elgato.obsstudio.transitionstudio] | grab / [com.elgato.obsstudio.screenshot] | · | · | · | · | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | · | · | · | · | · | · | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```

#### Page cadecac0-1555-4170-a5d7-64b5ba83c8ef (20 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | · | Voicemeet. / Banana [com.elgato.streamdeck.system.open] | / / EQ / [com.elgato.streamdeck.system.open] | · | Recording / (68) [com.elgato.streamdeck.soundboard.playaudio] | Recording / (88) [com.elgato.streamdeck.soundboard.playaudio] | Recording / (93) [com.elgato.streamdeck.soundboard.playaudio] | Recording / (95) [com.elgato.streamdeck.soundboard.playaudio]
R2 | · | · | · | · | · | Mute/Unmute [com.barraider.vmmicrophone] | Mute/Unmute [com.barraider.vmmicrophone] | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | Mute/Unmute [com.barraider.vmmicrophone] | Mute/Unmute [com.barraider.vmmicrophone] | · | Mute/Unmute [com.barraider.vmmicrophone] | Mute/Unmute [com.barraider.vmmicrophone] | Mute/Unmute [com.barraider.vmmicrophone] | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```

#### Page 58bdd141-6aba-4f83-90d2-a11d1896b898 (14 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | · | · | · | · | Roku / LVRM [com.elgato.streamdeck.profile.openchild] | Roku1 [com.elgato.streamdeck.profile.openchild] | Roku3 [com.elgato.streamdeck.profile.openchild] | Roku5 [com.elgato.streamdeck.profile.openchild]
R2 | · | · | · | · | Roku6 [com.elgato.streamdeck.profile.openchild] | Roku2 / [com.elgato.streamdeck.profile.openchild] | / Roku 4 / [com.elgato.streamdeck.profile.openchild] | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | · | · | · | · | · | · | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```

#### Page 1b95aa5d-dad3-457b-9cbe-61591b813446 (7 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | · | · | · | · | · | · | · | ·
R2 | · | · | · | · | · | · | · | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | · | · | · | · | · | · | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```

#### Page 7cf5b04b-0d96-4bfb-b781-f458a57b9e2f (7 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | · | · | · | · | · | · | · | ·
R2 | · | · | · | · | · | · | · | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | · | · | · | · | · | · | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```

#### Page 5d4175eb-c85a-4aa6-9d29-226f00ea3660 (7 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | · | · | · | · | · | · | · | ·
R2 | · | · | · | · | · | · | · | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | · | · | · | · | · | · | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```

#### Page 652d9c7c-722a-4f0e-bfc7-d139da8f71d6 (7 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | · | · | · | · | · | · | · | ·
R2 | · | · | · | · | · | · | · | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | · | · | · | · | · | · | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```

#### Page 77eb0147-f6ca-48f6-9587-a6b8ebea047a (8 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | · | · | · | · | · | · | · | ·
R2 | · | · | · | · | · | · | · | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | · | · | · | · | · | fold1 / [com.elgato.streamdeck.profile.openchild] | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```


### WinToolsXL — b5b58f76-aea8-4822-b0d8-f51525c44692

Device: 20GAT9902; applicable to physical 20GAT9902: yes; active pages: 1.

#### Page 7799adf2-9733-48e7-a3ba-b9caec4d91b8 (32 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction]
R2 | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction] | Display Action [com.barraider.wintools.displayaction]
```


### Estate Operations v0.5 Plugin — d4abffcd-7bde-4db7-856b-b26823e1780b

Device: 20GAT9902; applicable to physical 20GAT9902: yes; active pages: 1.

#### Page 6d1d0d91-30ec-4c1f-9861-0b99a784cc75 — Estate Operations (29 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | Estate Repository S... [com.estate.statusbridge.estate] | Estate Safe Sync [com.estate.statusbridge.estate.sync] | CueMastery Reposito... [com.estate.statusbridge.cuemastery] | CueMastery Safe Sync [com.estate.statusbridge.cuemastery.sync] | Work Packages Pending [com.estate.statusbridge.workpackages] | Validation Status [com.estate.statusbridge.validation] | Operational Readine... [com.estate.statusbridge.readiness] | Estate Runtime Status [com.estate.statusbridge.runtime]
R2 | Start Estate Surfaces [com.estate.statusbridge.surfaces.start] | Start Resident Gateway [com.estate.statusbridge.resident_gateway.start] | Start Office of Ste... [com.estate.statusbridge.office.start] | Start Open WebUI [com.estate.statusbridge.open_webui.start] | Start SillyTavern [com.estate.statusbridge.sillytavern.start] | Start TextGen [com.estate.statusbridge.textgen.start] | Start ComfyUI [com.estate.statusbridge.comfyui.start] | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | CPU [com.ez.sho-metrics.cpu] | GPU1 Compute and VR... [com.estate.statusbridge.gpu.gpu1] | · | Stop Estate Surfaces [com.estate.statusbridge.surfaces.stop] | Restart Estate Surf... [com.estate.statusbridge.surfaces.restart] | Estate Service Health [com.estate.statusbridge.health] | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | Memory [com.ez.sho-metrics.memory] | GPU2 Compute and VR... [com.estate.statusbridge.gpu.gpu2] | · | · | HOME [com.elgato.streamdeck.page.goto] | Ã¢â€”â‚¬ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE Ã¢â€“Â¶ [com.elgato.streamdeck.page.next]
```


### Default Profile — f40cbb56-817f-48c5-908f-a9e5f9eec0a8

Device: 20GAT9902; applicable to physical 20GAT9902: yes; active pages: 2.

#### Page a5e504d5-bf3d-4db8-8d15-611a100afafb — Four Monitor Wall (27 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | Operator Deck M1 To... [com.estate.statusbridge.operator_deck.slot.m1_top_left] | Operator Deck M1 To... [com.estate.statusbridge.operator_deck.slot.m1_top_right] | Operator Deck M2 To... [com.estate.statusbridge.operator_deck.slot.m2_top_left] | Operator Deck M2 To... [com.estate.statusbridge.operator_deck.slot.m2_top_right] | Operator Deck Undo [com.estate.statusbridge.operator_deck.undo] | Operator Deck Clear... [com.estate.statusbridge.operator_deck.clear_selection] | Operator Deck Selec... [com.estate.statusbridge.operator_deck.select_active] | ·
R2 | Operator Deck M1 Bo... [com.estate.statusbridge.operator_deck.slot.m1_bottom_left] | Operator Deck M1 Bo... [com.estate.statusbridge.operator_deck.slot.m1_bottom_right] | Operator Deck M2 Bo... [com.estate.statusbridge.operator_deck.slot.m2_bottom_left] | Operator Deck M2 Bo... [com.estate.statusbridge.operator_deck.slot.m2_bottom_right] | CODEX / DESK [com.estate.statusbridge.operator_deck.codex_desk] | · | · | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | Operator Deck M3 To... [com.estate.statusbridge.operator_deck.slot.m3_top_left] | Operator Deck M3 To... [com.estate.statusbridge.operator_deck.slot.m3_top_right] | Operator Deck M4 To... [com.estate.statusbridge.operator_deck.slot.m4_top_left] | Operator Deck M4 To... [com.estate.statusbridge.operator_deck.slot.m4_top_right] | · | · | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | Operator Deck M3 Bo... [com.estate.statusbridge.operator_deck.slot.m3_bottom_left] | Operator Deck M3 Bo... [com.estate.statusbridge.operator_deck.slot.m3_bottom_right] | Operator Deck M4 Bo... [com.estate.statusbridge.operator_deck.slot.m4_bottom_left] | Operator Deck M4 Bo... [com.estate.statusbridge.operator_deck.slot.m4_bottom_right] | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```

#### Page 954b847d-05c4-4dc3-ad66-2e586f5bdca2 — Mixed Placement (21 occupied keys)

Manifest coordinates use `column,row`; the following is shown as physical rows 1–4 and columns 1–8. `·` is empty.

```text
R1 | Operator Deck Shape... [com.estate.statusbridge.operator_deck.shape.full] | Operator Deck Shape... [com.estate.statusbridge.operator_deck.shape.top] | Operator Deck Desti... [com.estate.statusbridge.operator_deck.monitor.m1] | Operator Deck Desti... [com.estate.statusbridge.operator_deck.monitor.m2] | Operator Deck Undo [com.estate.statusbridge.operator_deck.undo] | Operator Deck Clear... [com.estate.statusbridge.operator_deck.clear_selection] | Operator Deck Selec... [com.estate.statusbridge.operator_deck.select_active] | Operator Deck Retur... [com.estate.statusbridge.operator_deck.return]
R2 | Operator Deck Shape... [com.estate.statusbridge.operator_deck.shape.left] | Operator Deck Shape... [com.estate.statusbridge.operator_deck.shape.right] | Operator Deck Desti... [com.estate.statusbridge.operator_deck.monitor.m3] | Operator Deck Desti... [com.estate.statusbridge.operator_deck.monitor.m4] | · | RESTORE / CODEX [com.elgato.streamdeck.system.open] | · | ◀ PROFILE [com.elgato.streamdeck.profile.rotate]
R3 | Operator Deck Shape... [com.estate.statusbridge.operator_deck.shape.bottom] | · | · | · | · | · | Operator Deck Voice... [com.estate.statusbridge.operator_deck.dictation] | PROFILE ▶ [com.elgato.streamdeck.profile.rotate]
R4 | · | · | · | · | HOME [com.elgato.streamdeck.page.goto] | ◀ PAGE [com.elgato.streamdeck.page.previous] | Page Indicator [com.elgato.streamdeck.page.indicator] | PAGE ▶ [com.elgato.streamdeck.page.next]
```



## Interpretation and freshness

This inventory is durable evidence of the machine state at capture time. Stream Deck edits, profile imports, plugin updates, or manual button movement can make it stale. Before changing installed state, re-scan ProfilesV3, compare profile UUIDs/pages/occupied positions/navigation targets, and create a fresh backup under `C:\\Users\\wille\\AppData\\Roaming\\Elgato\\StreamDeck-Backups`.
