<!-- Version: 1.0.0 | Date: 2026-08-23 | Purpose: bounded Stream Deck operator profile handoff. -->

# Riverview Stream Deck Initial Operator Profile

This is the first Riverview-owned three-control profile. It is separate from
the Estate Stream Deck profile and does not modify Estate files.

## Native installation

The installed Stream Deck version uses ProfilesV3. A native profile is a
bare-UUID directory ending in `.sdProfile`, with a root `manifest.json` and a
page manifest under `Profiles/<page UUID>/manifest.json`. The repository
source for the installed profile is:

`config/stream_deck/native_profile/`

The Riverview action plugin source is:

`tools/powershell/stream_deck/riverview-native-plugin/`

The native plugin invokes the existing PowerShell wrapper and implements the
same single/double/long timing convention locally. It does not reuse or
modify the Estate plugin. On this workstation the installed native locations
are `%APPDATA%\Elgato\StreamDeck\ProfilesV3\<Riverview UUID>.sdProfile` and
`%APPDATA%\Elgato\StreamDeck\Plugins\com.riverview.operator.sdPlugin`.

After installation, restart Stream Deck and confirm the profile selector shows
`Riverview` with exactly `RIVERVIEW RUNTIME`, `QUEST DEV`, and `QUEST CAST`.
Switching between Estate and Riverview is a required native-app acceptance
test; repository tests cannot prove physical profile switching or button
presses.

Definition:

`config/stream_deck/Riverview-Initial-Operator-Profile.json`

Action layer:

`tools/powershell/stream_deck/Invoke-RiverviewStreamDeckControl.ps1`

The definition and native page map each key to a bounded PowerShell action.
The native plugin passes `single`, `double`, or `long` to the wrapper after
the established 400 ms double-tap and approximately 1.25 s long-press
thresholds.

| Key | Single tap | Double tap | Long press (~1.25 s) |
|---|---|---|---|
| RIVERVIEW RUNTIME | Ensure the unified Runtime Supervisor | Ensure and open/raise Operator UI | Stop through the existing lifecycle owner |
| QUEST DEV | Discover/ensure authorized Quest ADB | Ensure and launch/raise existing left-eye engineering mirror | Stop only the Riverview-owned mirror and disconnect its wireless transport |
| QUEST CAST | Inspect/ensure Meta casting path | Launch/raise verified Meta casting path | Stop only a Riverview-owned casting process |

## Runtime boundary

Runtime delegates to `tools/powershell/runtime/Start-RiverviewRuntimeSupervisor.ps1`
and `Stop-RiverviewRuntimeSupervisor.ps1`/the installed scheduled task. It
never launches individual Python services. The Operator UI target is the
existing local `http://127.0.0.1:18082/` surface.

## Quest Dev boundary

The action discovers ADB from the known local installation or PATH, searches
current authorized wireless devices and mDNS, and then checks authorized USB
Quest devices. If USB is the only transport, it reads the current headset
Wi-Fi address and establishes session-level ADB TCP on port `5555`, then
prefers the resulting current `<ip>:5555` serial. It never embeds the prior
Quest TLS serial or port. The existing launcher remains the source of the
current crop, wake, watchdog, and scrcpy settings:

`runtime/quest-observability/Quest-LeftEyeMirror.ps1`

Failures are reported with distinct classes for ADB discovery, authorization,
wireless establishment, and live-view launch. Quest Dev does not stop or
disconnect Quest Cast.

## Quest Cast boundary

The current workstation exposes `Meta Quest Developer Hub` in Start Apps, but
inspection did not identify a verified local Meta casting executable, URI, or
automation command. Quest Cast therefore reports a precise blocked state and
does not pretend that casting launched. It does not touch ADB or the Quest Dev
mirror. If a future verified Meta casting path is installed, only the bounded
cast wrapper needs to be extended.

## Reports and recovery

Each action emits JSON, saves a nonsecret report under
`%LOCALAPPDATA%\Riverview\StreamDeck\reports`, and attempts clipboard copy.
The report includes state, control, gesture, transport/serial where relevant,
failure class, and the exact owned-session boundary.

Run a control directly for local validation:

```powershell
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File A:\Riverview\repo\tools\powershell\stream_deck\Invoke-RiverviewStreamDeckControl.ps1 -Control quest-dev -Gesture single
```

Hardware-dependent acceptance still requires Pat to verify Stream Deck timing,
Quest ADB/live-view behavior, and any later Meta casting installation.
