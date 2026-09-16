# Camrui Linux Virtual Display / VKMS Findings — 2026-09-16

Status: Hardware/runtime-verified investigation checkpoint.

## Purpose

Preserve exactly what was learned while investigating additional displays on the Camrui Ubuntu/Linux Daily Driver. This document separates the now-proven **virtual display creation** capability from the still-unproven **transport of that desktop to a physical television**.

## Daily Driver display environment

The Camrui is the current Linux Daily Driver under investigation for a four-display Command Chair desktop.

Verified graphics/session context during this investigation:

- Ubuntu/Linux
- GNOME Shell 46.0
- Wayland session
- `XDG_CURRENT_DESKTOP=ubuntu:GNOME`
- Intel HD Graphics 500, PCI ID `[8086:5a85]`
- i915 driver
- two native HDMI outputs
- no USB-C port
- kernel `6.17.0-35-generic`

Physical display state observed before VKMS:

- `HDMI-2`: 3840x2160 at +0+0
- `HDMI-1`: 1920x1080 at +3840+0

The 1920x1080 state on HDMI-1 was believed to be associated with the existing HDMI-matrix path and was not selected for investigation at this checkpoint.

## Failed USB-C HDMI adapter path

The Plugable `USBC-HDMI` adapter was tested through USB-A-to-USB-C sleeves because the Camrui has no USB-C port.

Observed USB identity/state:

- Realtek Billboard device
- USB ID `0bda:2172`
- `lsusb -t` showed `Class=Billboard`, no active graphics driver, and 12M/full-speed behavior
- no new DRM display device appeared

The same behavior occurred on another physical USB-A port.

Conclusion: this particular adapter depends on USB-C DisplayPort Alternate Mode. A passive USB-A-to-USB-C sleeve cannot manufacture the required DisplayPort lanes. Installing another operating system does not change that electrical limitation. This adapter is not a viable Camrui display-expansion path through USB-A.

## Miracast / built-in Wi-Fi finding

Camrui built-in Wi-Fi:

- Realtek RTL8821CE 802.11ac PCIe `[10ec:c821]`
- Linux driver `rtw88_8821ce`

`iw list` exposed these interface modes:

- IBSS
- managed
- AP
- AP/VLAN
- monitor

It did **not** expose `P2P-client` or `P2P-GO`.

Conclusion: the current built-in RTL8821CE/rtw88 Linux path does not expose the Wi-Fi Direct/P2P capability required for the standard Miracast sender topology. Do not spend time installing GNOME Network Displays on this exact built-in Wi-Fi path unless a P2P-capable Wi-Fi device/driver is introduced.

This finding applies to the current Miracast transport path; it does **not** prevent Linux from creating virtual displays.

## GNOME/Mutter investigation

GNOME portal services were active, including `xdg-desktop-portal` and `xdg-desktop-portal-gnome`.

Mutter D-Bus interfaces included:

- `org.gnome.Mutter.DisplayConfig`
- `org.gnome.Mutter.RemoteDesktop`
- `org.gnome.Mutter.ScreenCast`
- `org.gnome.Mutter.ServiceChannel`

DisplayConfig exposed monitor-configuration operations such as `ApplyMonitorsConfig`, but the inspected interface did not expose an obvious direct create/add-virtual-monitor method suitable for the intended task.

`grdctl` existed. GNOME Remote Desktop was disabled/inactive at this point, and its inspected command surface did not provide the straightforward virtual-monitor creation path being sought.

## VKMS discovery

DRM inspection established:

- Intel i915 DRM device was `card1`
- `card1-HDMI-A-1` connected
- `card1-HDMI-A-2` connected
- VKMS kernel module existed at `/lib/modules/6.17.0-35-generic/kernel/drivers/gpu/drm/vkms/vkms.ko.zst`
- VKMS was initially not loaded

The module was then loaded **temporarily** with `modprobe vkms`.

No persistent boot/module configuration was intentionally added at this checkpoint.

## VKMS result — virtual display creation PROVEN

After loading VKMS, the DRM topology gained:

- `card0`
- `card0-Virtual-1`
- `card0-Writeback-1`

Intel i915 remained `card1` with its two physical HDMI connectors.

Connector state showed:

- `card0-Virtual-1`: **connected**
- `card0-Writeback-1`: unknown
- both Intel HDMI connectors: connected

GNOME immediately recognized the VKMS connector as a third joined display. In GNOME Settings -> Displays it appeared as display **#3, Unknown Display**.

The initial `xrandr` view showed `Virtual-1` at 1024x768, but Mutter reported a substantially larger mode set for the virtual connector, including:

- **4096x2160 @ 60 Hz**
- 2560x1600
- 1920x1080
- additional lower modes

The Steward selected **4096x2160** for display #3 and applied it successfully. GNOME then showed the virtual display as a full-size 4K-class joined desktop region.

Therefore the important conclusion is:

> The Camrui can create and use a genuine joined 4K-class virtual monitor under the existing Ubuntu/GNOME/Wayland environment without a physical display adapter.

The **virtual-display creation problem is solved for one additional display**.

## What VKMS does NOT solve

VKMS creates desktop/display space in the Linux graphics stack. It does not by itself put those pixels onto a television.

The remaining problem is transport/receiver presentation, for example:

`GNOME virtual display -> capture/encode -> network transport -> TV receiver -> physical panel`

That transport must be evaluated independently for:

- interactive latency
- 4K image quality
- encode/decode load
- stability
- independent extended-desktop behavior rather than simple mirroring
- ability to support more than one additional display simultaneously

Do not confuse proven VKMS virtual-display creation with proven network-TV display transport.

## Second virtual display / four-screen target

The Command Chair target is four displays. At this checkpoint, one VKMS virtual connector/display is proven.

Do **not** assume a second independent VKMS connector is already available. The default module instance observed here created one `Virtual-1` connector. A second virtual monitor may require another VKMS device/configuration mechanism (potentially configfs depending on kernel support), but that has not yet been tested and accepted.

Therefore current status is:

- two physical Camrui HDMI displays: existing
- third display via VKMS `Virtual-1`: **PROVEN**
- fourth independent display: **NOT YET PROVEN**

## TCL / network-display context

The physical TCL Roku television examined during the surrounding display investigation was identified as model `55S451`, Roku OS 15.3. Its settings expose Roku Screen Mirroring and Apple AirPlay/HomeKit functionality.

Standard Miracast remains unattractive for the Camrui's built-in Wi-Fi because the current Linux RTL8821CE driver does not expose P2P modes.

AirPlay/LAN transport remains worth investigating because it may use the ordinary IP network and therefore potentially fit the intended physical topology:

`Camrui Ethernet -> LAN/switch infrastructure -> TCL Ethernet/network -> TV`

However, Linux-to-Roku AirPlay as a low-latency independent extended desktop has **not** been proven. Do not document it as an accepted solution yet.

A Raspberry Pi or other dedicated receiver remains a last-resort option rather than the preferred next step.

## HDMI matrix relationship

The separate MT-VIKI FHD1616 investigation proved that the HDMI matrix is LAN controllable at `192.168.1.200:8080`, while video itself remains HDMI. The matrix can therefore remain the deterministic physical/recovery-video backbone even if a network desktop transport is later accepted for normal operation.

The architecture should not be framed as virtual/network displays versus the HDMI matrix. A hybrid design is possible:

1. physical HDMI/matrix path for deterministic video, BIOS/boot/recovery, and fallback;
2. LAN control of matrix routes from Riverview/Stream Deck/Linux;
3. optional network transport of virtual desktops to TVs if the remaining acceptance tests succeed.

See `docs/operations/command-chair/MT_VIKI_FHD1616_MATRIX_LAN_CONTROL_AND_DISPLAY_FINDINGS_2026-09-16.md`.

## Persistence status

VKMS was deliberately loaded temporarily for proof-of-capability. Do not assume it survives reboot.

Do not make the VKMS module persistent until the display architecture is settled or the Steward explicitly chooses to make the proven virtual-display path part of normal Daily Driver startup.

## Do-not-repeat notes

- Do not re-investigate whether VKMS exists on this kernel; it does.
- Do not re-prove whether GNOME accepts `Virtual-1`; it does.
- Do not re-prove whether the virtual connector can expose/apply a 4096x2160 mode; it can and it was applied.
- Do not treat the Plugable `USBC-HDMI` adapter as USB graphics; it requires USB-C DP Alt Mode and is not usable through the tested USB-A sleeves.
- Do not treat the current built-in RTL8821CE Linux Wi-Fi path as Miracast-ready; P2P-client/P2P-GO were absent.
- Do not claim a fourth/second VKMS virtual monitor until it is actually created and accepted.
- Do not claim AirPlay/network-TV transport is solved merely because the TV exposes AirPlay settings.
- Do not make VKMS persistent without a deliberate architecture decision.

## Checkpoint conclusion

The investigation separated two problems that had previously been entangled. **Linux virtual display creation is now proven**: the Camrui can add a joined 4096x2160 VKMS desktop under GNOME/Wayland. The remaining engineering problem is how to transport one or more such virtual desktops to the physical TCL Roku TVs with acceptable latency, image quality, stability, and compute cost. That transport problem should be resumed from this checkpoint rather than rediscovering the VKMS work.