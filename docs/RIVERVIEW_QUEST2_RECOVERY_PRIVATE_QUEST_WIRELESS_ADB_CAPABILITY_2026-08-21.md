# Riverview Quest 2 Recovery, Private Quest, and Wireless ADB Capability

**Date:** 2026-08-21  
**Purpose:** Durable recovery record and capability inventory for the recovered Meta Quest 2 spatial endpoint, including Private Quest, Meta Horizon, Android Platform Tools/ADB, Meta Quest Developer Hub, MetaVR CLI, Wi-Fi/BLE provisioning, controllerless NUX recovery, hand tracking, and verified wireless ADB access from the Riverview workstation.

**Future retrieval search terms:** Quest 2 recovery, Meta Quest headset, Private Quest, controllerless Quest setup, Skip NUX, NUX complete, hand tracking, Meta Horizon, Meta Quest Developer Hub, MQDH, MetaVR, hzdb, Android Platform Tools, adb pair, adb connect, wireless ADB, Quest 2 Hollywood, Riverview VR, Estate VR, spatial endpoint.

> This record intentionally does **not** contain the Quest DeviceKey/device secret, Meta access tokens, Wi-Fi password, temporary ADB pairing PINs, or account credentials. Those values must not be committed to GitHub. Private IP addresses and observed ephemeral ports are recorded only as diagnostic examples; future sessions must re-query current values before connecting.

## Executive summary

A previously working Quest 2 had been stored for a long period and initially presented a repeated Meta/infinity-logo boot loop. Recovery established that the headset itself remained viable. After charging from a proper powered USB source, it reached the factory onboarding flow, but both original Touch controllers were unusable for setup. One controller produced no useful response and the other only a white LED; neither entered a usable pairing state.

The headset was recovered without replacement controllers. The successful path was:

1. Charge the deeply discharged headset from a powered charger rather than a low-current PC USB port.
2. Enter Quest USB Update Mode with **Volume Down + Power** and verify the recovery menu.
3. Pair the headset to the **Meta Horizon** iPhone app and configure Wi-Fi.
4. Register the Meta account for developer access.
5. Install Windows Android Platform Tools and prove the Quest recovery environment appears to `adb devices` as `sideload`.
6. Install Meta Quest Developer Hub and MetaVR CLI for diagnostics; these did not by themselves bypass initial setup.
7. Install **Private Quest 1.3** on an Amazon Fire HD 8 (7th generation) and connect to the Quest over Bluetooth Low Energy.
8. Recover the existing Quest DeviceKey/device secret with `DeviceSecretExtractor.exe`, transfer the 64-character value locally to the Fire tablet, and configure that value in Private Quest. The secret itself is deliberately omitted from this repository.
9. Use Private Quest **Init -> Skip NUX**. Private Quest subsequently reported `NUX completed`.
10. Reboot the Quest. It passed the controller-pairing onboarding screen and entered the normal Quest environment.
11. Use gaze selection plus Volume Up as a temporary controllerless input method, then enable Quest hand tracking. Hand tracking was verified working.
12. Enable ADB/developer access, use Private Quest to expose wireless-debugging pairing information, pair Windows ADB to the Quest, authorize wireless debugging in-headset, and establish a real `_adb-tls-connect._tcp` endpoint.
13. Verify full wireless ADB shell access from Windows.
14. Save a known-good Quest baseline under `C:\Users\wille\Documents\Quest2-Recovery`.

This adds a new Riverview operational capability: the Windows workstation can now manage the Quest 2 wirelessly over ADB without relying on the original Touch controllers or a persistent USB cable.

## 1. Headset identity and recovered operating state

Verified hardware/software observations:

- Device: **Meta Quest 2**
- Android product/model reported by ADB: `Quest_2`
- Android device codename: `hollywood`
- Android major version reported by `getprop ro.build.version.release`: **14**
- Private Quest also identifies the platform as Quest 2 / Hollywood.
- Hand tracking is working after recovery.
- The original Touch controllers remain nonessential to current operation and should not be treated as a prerequisite for Estate/Riverview spatial use.

Recovery menu reached with:

- Headset fully powered off
- Hold **Volume Down**
- Hold **Power** while continuing to hold Volume Down

Observed USB Update Mode options included:

- Boot Device
- Device Info
- Factory Reset
- Sideload Update
- Switch Boot Slot
- Power Off

No future session should switch boot slots or factory-reset the headset casually; the working recovered state should be preserved.

## 2. Controllerless interaction

During factory onboarding, the Quest displayed the five-digit headset pairing-code screen and controller activation/pull-tab animation. Gaze could identify UI elements, but normal onboarding remained controller-gated.

After NUX bypass and reboot, controllerless navigation worked using:

- **Head gaze** to position the cursor
- **Volume Up** to select

Hand tracking was then enabled in the Quest UI and verified operational. The exact menu naming can vary by firmware; the recovered headset exposed hand/gesture-related movement/tracking settings and ultimately displayed usable tracked hands.

For future Estate use, hand tracking is the preferred primary interaction path unless an application specifically requires Touch-controller input.

## 3. Meta Horizon mobile app

Platform used:

- iPhone
- **Meta Horizon** app

Capabilities verified during recovery:

- Meta account login and email verification
- Pairing the Quest 2 to the Meta account using the five-digit pairing code displayed in-headset
- Supplying Wi-Fi configuration to the headset while normal onboarding was blocked
- Inspecting registered controller records
- Exposing Headset Settings and Developer Mode controls

Important behavior observed:

- Pairing the Horizon app to the headset did **not** by itself bypass the controller-gated NUX flow.
- The app could successfully configure Wi-Fi even while the Quest was stuck on controller onboarding.
- Developer Mode UI state in the phone app and live headset state were not always immediately synchronized. A reboot and subsequent ADB/authorization work were required before usable wireless ADB became available.

Meta Horizon should therefore be treated as a useful provisioning/account tool, not the only recovery path.

## 4. Private Quest 1.3

### Host device

Private Quest was installed on:

- Amazon Fire HD 8, 7th generation
- Fire OS / Android-derived platform
- Bluetooth Low Energy available

Package used:

- `private_quest_1_3.apk`
- Obtained from the VRComm Private Quest distribution after the original 4PDA attachment path returned HTTP 404.

### Why it mattered

Private Quest could discover and control the Quest over BLE before ordinary PC ADB management was available. It became the critical controllerless bootstrap/recovery utility.

Observed Private Quest tabs/capabilities included:

- **Control**
- **Config**
- **Wi-Fi**
- **Cast**
- **Init**

Observed Control capabilities included:

- MTP on/off
- passthrough controls
- Guardian reset
- view reset
- reboot device
- ADB start/info controls
- device Status
- Version
- Capabilities
- External Battery
- PIN status
- OTA status

Observed Config capabilities included:

- set time
- OTA update control
- crash-report controls
- device theme
- device PIN management
- managed-mode level controls

Observed Wi-Fi capabilities included:

- enable/disable
- status
- scan
- connect
- manual connection fields supporting None / EAP / WPA / WEP

Observed Cast capabilities included casting/status controls.

Observed Init capabilities included:

- Set Device Key
- Skip Apps
- Skip Apps Download
- NUX Complete
- Skip Safety Warnings
- Oculus/Meta token fields
- combined token controls
- Retail / Default initialization controls
- **Skip NUX**
- Factory Reset

### Security boundary

Private Quest DeviceKey, Meta tokens, pairing PINs, Wi-Fi passwords, and other credentials are **not** repository documentation. Do not put them in GitHub, logs, screenshots intended for publication, or ordinary River resources.

The working Quest DeviceKey was recovered separately and injected into Private Quest only to authenticate the already-claimed headset. `Generate` must not be used casually on the recovered device.

## 5. DeviceSecretExtractor

A community utility named `DeviceSecretExtractor.exe` was used because Private Quest initially failed connection with:

`Error 105: Device auth error`

The installed/downloaded candidate was inspected before execution:

- Filename: `DeviceSecretExtractor.exe`
- Size: **6,297,600 bytes**
- SHA-256: `BE40D916E814CD24E0030C6CBA3F0BA5D30A45F449299CC8286F7FB23C87708C`
- Authenticode: **NotSigned**
- File Description: `DeviceSecretExtractor`
- Product: `DeviceSecretExtractor`
- Company metadata: `DeviceSecretExtractor`
- File version: `1.0.0.0`
- Microsoft Defender custom scan completed without reporting a detection during this investigation.

The utility produced a **64-character device secret**. The secret is intentionally omitted here.

A temporary plaintext copy was created locally as:

`C:\Users\wille\Downloads\QuestDeviceKey.txt`

That file was copied to the Fire tablet only to avoid manually typing the long secret into Private Quest. Future cleanup should remove unnecessary plaintext secret copies after the recovery state is confidently preserved.

## 6. NUX bypass and recovery result

Once the correct existing DeviceKey was configured in Private Quest, the previous Device Auth Error disappeared and the full device-control interface became available.

Under **Init**, Private Quest exposed `Skip NUX`. The successful sequence was:

1. Authenticated Private Quest connection established.
2. `Skip NUX` invoked once.
3. Private Quest subsequently reported **NUX completed**.
4. Quest rebooted through Private Quest.
5. Headset booted past the controller-pairing onboarding flow into a normal Quest environment.

Do not repeatedly invoke Skip NUX on a healthy configured headset. This is a recovery/bootstrap operation, not an ordinary startup step.

## 7. Android Platform Tools / ADB

Windows Android Platform Tools were downloaded and extracted under:

`C:\Users\wille\Downloads\platform-tools-latest-windows\platform-tools`

Key executables:

- `adb.exe`
- `fastboot.exe`

### Recovery-mode capability verified

With Quest USB Update Mode -> Sideload Update selected, Windows reported:

`<Quest serial>    sideload`

through:

`adb devices`

This proves a controller-independent recovery transport exists even when normal Android ADB is unavailable.

In sideload recovery mode, `adb shell` returned `error: closed`, which is expected for the restricted sideload transport. `fastboot devices` was empty because the headset was not in fastboot mode.

### Wireless ADB capability verified

After NUX completion, developer/ADB enablement, wireless pairing, and in-headset authorization, Windows successfully established:

`connected to 192.168.1.159:42013`

Observed working connection during this investigation:

- Quest private LAN IP: `192.168.1.159`
- Successful ADB TLS pairing port observed earlier: `35869`
- Another later pairing service port observed: `33175`
- Successful ADB connect port: `42013`

These ports are **ephemeral**. Pairing PINs are also temporary and are deliberately omitted. Never assume these ports will remain valid after reboot, Wi-Fi changes, or ADB service restart.

`adb devices -l` subsequently reported both a direct TCP endpoint and the mDNS service, with:

- product: `hollywood`
- model: `Quest_2`
- device: `hollywood`

`adb mdns services` showed the transition from only `_adb-tls-pairing._tcp` during partial setup to a working `_adb-tls-connect._tcp` service after headset authorization.

Verified shell queries:

```powershell
.\adb.exe -s 192.168.1.159:42013 shell getprop ro.product.model
.\adb.exe -s 192.168.1.159:42013 shell getprop ro.product.device
.\adb.exe -s 192.168.1.159:42013 shell getprop ro.build.version.release
```

Verified results:

- `Quest 2`
- `hollywood`
- `14`

### Resulting Riverview capability

The workstation can now, subject to current ADB authorization and connectivity:

- run shell diagnostics on the Quest;
- inspect Android system properties;
- enumerate installed packages;
- install APKs wirelessly;
- launch/stop applications through Android tooling;
- push files to the headset;
- pull files from the headset;
- capture logs;
- gather screenshots through ADB-capable workflows;
- reboot the headset;
- inspect battery/system services;
- automate repeatable Quest diagnostics without Touch controllers;
- use USB recovery sideload as a separate fallback path if normal Android ADB is unavailable.

## 8. Meta Quest Developer Hub (MQDH)

Installed Windows application:

`C:\Program Files\Meta Quest Developer Hub\Meta Quest Developer Hub.exe`

Observed MQDH user-data directory from the running process command line:

`C:\Users\wille\AppData\Roaming\odh`

MQDH features visible in the application include device management, device actions, logs, metrics, file management, casting, screenshots/video, package/application deployment, and related developer tooling.

During recovery, MQDH could not initially manage the Quest because the headset was not through NUX/developer authorization. Its local LevelDB device map was empty during that state. It should now be reconsidered as a higher-level management UI because wireless ADB is functioning.

Relevant local MQDH storage observed:

- `C:\Users\wille\AppData\Roaming\odh\Local Storage\leveldb`
- `C:\Users\wille\AppData\Roaming\odh\odh.log`
- `C:\Users\wille\AppData\Roaming\odh\odh.log.old`

Do not treat MQDH cache files as authoritative device secrets.

## 9. MetaVR CLI / Horizon Debug Bridge tooling

Meta's current CLI was invoked through Node/npm using:

`npx -y metavr`

Environment verified during recovery:

- Node.js: `v24.13.1`
- npm: `11.8.0`
- MetaVR/hzdb runtime observed in verbose logging: `hzdb/1.3.2.2.2+windows`

Useful command families exposed by MetaVR included:

- `auth`
- `adb`
- `app`
- `capture`
- `device`
- `files`
- `input`
- `log`
- `perf`
- `shell`
- `ui`
- `window`
- `device setup`

The BLE setup surface explicitly exposed:

- `device setup scan`
- `device setup connect`
- `device setup dev-mode`
- `device setup interactive`

MetaVR successfully discovered the Quest over BLE, but the recovered headset initially rejected the BLE HELLO handshake with:

`crypto error: signature verification failed`

Even after MetaVR authentication succeeded, that error persisted. MetaVR therefore served as useful diagnostics but was **not** the successful recovery mechanism. Private Quest supplied the working BLE/bootstrap route.

## 10. Meta Quest Software Update Tool / recovery observations

Meta's browser-based Quest Software Update Tool could see the Quest 2 through WebUSB and showed the headset as paired, but it did not successfully initiate an update during this investigation.

The headset's USB Sideload Update path itself was independently proven functional through ADB enumeration. Do not manually sideload arbitrary firmware ZIPs; future firmware recovery should use an authenticated/signed Meta-supported package source and positive model/build verification.

Private Quest later reported OTA state fields, including OTA available/ready during status inspection. Those observations were not used to force an update.

## 11. Known-good recovery baseline on Windows

A post-recovery baseline was saved locally at:

`C:\Users\wille\Documents\Quest2-Recovery`

Files saved:

- `getprop.txt`
- `packages.txt`
- `battery.txt`

These were generated from the healthy wireless ADB connection with:

- complete Android system properties (`getprop`)
- installed package inventory (`pm list packages`)
- battery service state (`dumpsys battery`)

This GitHub document is the durable pointer to that local evidence. The local evidence directory is **not** committed to GitHub and must not be assumed to exist on another workstation.

## 12. Recovery-state observations worth remembering

Private Quest status inspection during recovery reported useful state including:

- Wi-Fi enabled/configured/connected
- Meta/Horizon logged in
- primary and secondary controllers configured but not connected
- OTA available and ready
- PIN not configured/locked
- ADB state
- Developer Mode state
- NUX complete
- factory provision type

An important diagnostic distinction was observed:

- A wireless ADB **pairing** endpoint can exist while the real ADB **connect** endpoint is absent.
- During that state, `adb pair` could succeed but `adb devices` remained empty and mDNS exposed only `_adb-tls-pairing._tcp`.
- After ADB enablement and the in-headset wireless-debugging authorization was accepted, Private Quest produced a nonzero connect port and `_adb-tls-connect._tcp` became available.

Future troubleshooting should inspect the pairing service and connect service separately instead of assuming a successful pair means `adbd` is ready for shell traffic.

## 13. Current capability boundary for Riverview

Riverview now has a verified **Quest 2 spatial endpoint management capability** consisting of:

1. Meta Horizon account/device provisioning from iPhone.
2. Private Quest BLE/bootstrap management from the Fire HD 8.
3. Controllerless NUX recovery capability.
4. Working hand-tracking-only Quest operation.
5. USB recovery/sideload detection through Android Platform Tools.
6. Verified wireless ADB pairing and shell access from Windows.
7. MetaVR CLI available for Meta-native Quest development/device operations.
8. MQDH installed for higher-level device actions once device authorization is available.
9. A known-good local diagnostic baseline under `C:\Users\wille\Documents\Quest2-Recovery`.

This capability is particularly relevant to the Estate/Riverview spatial-world direction: the Quest can now be treated as a manageable client endpoint rather than a controller-dependent standalone appliance.

## 14. Sensitive values and cleanup

Do **not** commit or reproduce in ordinary documentation:

- Quest DeviceKey/device secret
- Meta/Oculus access tokens
- Meta password/account recovery information
- Wi-Fi password
- temporary ADB pairing PINs

The local plaintext `QuestDeviceKey.txt` was created for transfer convenience. Once the recovered state has been stable and the key has been retained in whatever approved protected mechanism is appropriate, remove unnecessary plaintext copies from the Windows Downloads folder and Fire tablet.

The DeviceSecretExtractor binary is an unsigned community utility. Preserve its SHA-256 above for provenance checks if it is retained, and do not assume another same-named download is identical.

## 15. Quick future recovery checklist

If a future conversation is told that the Quest 2 was previously recovered for Riverview, it should locate this document first, then:

1. Confirm the Quest boots into Home and hand tracking works.
2. Confirm Wi-Fi connection and current IP rather than assuming `192.168.1.159` remains current.
3. Run `adb devices -l` and `adb mdns services` on the workstation.
4. If the existing wireless connection is live, use it; do not re-pair unnecessarily.
5. If only `_adb-tls-pairing._tcp` exists, inspect Private Quest ADB status and obtain a new pairing endpoint/PIN, then approve wireless debugging in-headset.
6. If normal ADB is unavailable, USB Update Mode -> Sideload Update remains a separate proven recovery transport.
7. Do not regenerate the Private Quest DeviceKey, factory-reset, switch boot slots, or overwrite provisioning state unless a specifically diagnosed failure requires it.
8. Use `C:\Users\wille\Documents\Quest2-Recovery` as the local known-good baseline reference on the current workstation.

## 16. Follow-on opportunities

Now that wireless ADB is verified, future bounded work can evaluate:

- reconnecting MQDH to the now-authorized headset;
- persistent scripts to discover the Quest through mDNS and avoid hard-coded ports;
- a Riverview adapter for read-only Quest health/status collection;
- automated Quest screenshot/log capture for diagnostics;
- controlled APK deployment for Estate spatial clients;
- casting/streaming integration;
- hand-tracking-first Estate UI experiments;
- monitoring Quest availability/capacity as a registered spatial endpoint;
- documenting recovery of wireless ADB after headset/router reboot;
- replacement facial-interface/foam cushion selection as a physical-maintenance item.

These opportunities are not automatically authorized implementation work; this document records the capability now available and the recovery evidence supporting it.
