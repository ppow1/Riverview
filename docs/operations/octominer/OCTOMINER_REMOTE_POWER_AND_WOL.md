# Octominer Remote Power and Wake-on-LAN

Status: Verified procedure for OCTOMINER1; reuse as the starting procedure for OCTOMINER2.

Date verified: 2026-08-26

## Purpose

Record the verified network and remote-power configuration for Riverview-managed Octominer nodes so the procedure can be repeated on OCTOMINER2 without rediscovery.

## OCTOMINER1 verified state

- Hostname: `OCTOMINER1`
- Hardware: Octominer X12 Ultra / X12ULTRA
- BIOS observed: AMI BTCpxN01, build 2021-09-18
- OS: Ubuntu 22.04.5 LTS / Hive OS environment
- NIC: Realtek RTL8111/8168/8411 PCIe Gigabit Ethernet, driver `r8169`
- NIC MAC: `00:e0:4c:6b:05:a9`
- Reserved IPv4: `192.168.1.160`
- Gateway/DHCP server: `192.168.1.254` (AT&T/ARRIS gateway)
- SSH: `root@192.168.1.160`
- Wake-on-LAN capability reported by ethtool: `pumbg`
- Wake-on-LAN active mode: `g` (Magic Packet)
- BIOS `Restore AC Power Loss`: `Power On`

## What was verified

1. BIOS AC-loss recovery was physically tested: removing AC and restoring it caused OCTOMINER1 to boot automatically.
2. The front-panel IP display was found to be stale (`192.168.1.223`). Hive reported the actual address as `192.168.1.160`.
3. The AT&T gateway initially supplied the address dynamically. Its IP Allocation facility was used to make the OCTOMINER1 MAC/IP relationship fixed while leaving Hive configured as a DHCP client.
4. After a shutdown/boot cycle, OCTOMINER1 returned at `192.168.1.160`. Linux correctly continues to label the address `dynamic`; the reservation is enforced by the DHCP server, not by a static client configuration.
5. `ethtool eth0` reported `Supports Wake-on: pumbg` and initially `Wake-on: d`.
6. `ethtool -s eth0 wol g` enabled Magic Packet wake for the live session.
7. A real shutdown followed by a Magic Packet successfully powered OCTOMINER1 back on.
8. After boot, WOL reverted to `d`, proving the live ethtool setting was not persistent.
9. Networking was identified as `systemd-networkd`, with `/etc/systemd/network/20-ethernet.network` managing Ethernet DHCP.
10. An attempted `WakeOnLan=magic` under `[Link]` in the `.network` file was rejected by systemd-networkd 249 as an unknown key and was removed/restored from backup.
11. Persistent WOL was implemented with a dedicated systemd `.link` file matched to the physical NIC MAC.
12. After a full reboot, `ethtool eth0` reported `Wake-on: g` without a manual ethtool command, proving persistence.

## Persistent WOL configuration

File on OCTOMINER1:

`/etc/systemd/network/10-octominer1-wol.link`

Contents:

```ini
[Match]
MACAddress=00:e0:4c:6b:05:a9

[Link]
WakeOnLan=magic
```

The MAC match intentionally binds the configuration to the physical NIC rather than relying on the interface remaining named `eth0`.

To apply a newly created `.link` file without rebooting:

```bash
udevadm control --reload
udevadm trigger --verbose --settle --action=add /sys/class/net/eth0
ethtool eth0 | grep -i wake
```

Expected result:

```text
Supports Wake-on: pumbg
Wake-on: g
```

## DHCP reservation / fixed allocation

AT&T gateway path used:

`Home Network -> IP Allocation`

OCTOMINER1 mapping:

- MAC: `00:e0:4c:6b:05:a9`
- Fixed allocation: `192.168.1.160`

The client remains DHCP-configured. Do not interpret Linux output such as `scope global dynamic eth0` as evidence that the reservation failed. The gateway owns the fixed MAC-to-IP allocation.

## Remote-control model for Riverview

Riverview can use three levels of power control:

1. Normal start: send a Wake-on-LAN Magic Packet to the node MAC.
2. Normal stop: SSH to the reserved IP and perform an orderly Linux shutdown.
3. Hard recovery/start: cycle a remotely controlled AC outlet/PDU. BIOS is verified to boot automatically when AC is restored.

For OCTOMINER1, use MAC identity as the durable WOL target and `192.168.1.160` as the reserved management address.

## OCTOMINER2 repeat procedure

When OCTOMINER2 is powered up:

1. Record its hostname, actual Hive IP, and NIC MAC (`ip -br addr`, `cat /sys/class/net/eth0/address`). Do not trust a stale front-panel IP without checking Hive.
2. Confirm NIC and WOL capability with `lspci | grep -i ethernet` and `ethtool eth0 | grep -i wake`.
3. In the AT&T gateway, use `Home Network -> IP Allocation` to create a Fixed allocation for OCTOMINER2's MAC. Keep Hive as a DHCP client.
4. In BIOS, set/verify `Restore AC Power Loss = Power On` and physically test AC removal/restoration.
5. Create a dedicated `/etc/systemd/network/10-octominer2-wol.link` using OCTOMINER2's own MAC and `WakeOnLan=magic`.
6. Reload/trigger udev or reboot, then verify `Wake-on: g`.
7. Shut down normally while leaving AC connected and send a Magic Packet. Verify physical power-on.
8. After boot, verify the reserved IP returned and `Wake-on: g` remains enabled.
9. Record OCTOMINER2's final MAC, reserved IP, SSH target, and test results in this document.

## Octominer fan controller and PSU telemetry

The HiveOS Octominer controller utility is:

`/hive/opt/octofan/fan_controller_cli`

The controller was identified over USB as the Octominer `Fan-Controller` (`16c0:05dc`, manufacturer string `info@octominer.com`). On the tested controller, firmware reported as 2.7 and hardware as 1.2.

### Read-only controller inspection

Human-readable controller status:

```bash
/hive/opt/octofan/fan_controller_cli -h
```

Machine-readable controller status:

```bash
/hive/opt/octofan/fan_controller_cli -r
```

From the Windows dev machine, OCTOMINER2 can be queried over the established passwordless alias with:

```powershell
Clear-Host
ssh octo2 "/hive/opt/octofan/fan_controller_cli -h"
```

### PSU / chassis AC-power telemetry

Octofan writes recent PSU AC-input readings to files matching:

`/tmp/octofan_psu_last_power_*`

To sum all reported PSU AC-input values:

```bash
awk '{s+=$1} END {printf "Total AC power: %.0f W\n",s}' /tmp/octofan_psu_last_power_*
```

From the Windows dev machine:

```powershell
Clear-Host
ssh octo2 "awk '{s+=\$1} END {printf \"Total AC power: %.0f W\\n\",s}' /tmp/octofan_psu_last_power_*"
```

This is controller/PSU-reported aggregate AC input telemetry for the chassis. Treat it as useful operational telemetry, not as a separately calibrated wall-meter measurement.

### Direct fan PWM commands

The verified controller syntax for setting the current PWM of one fan channel is:

```text
-f <fan_no> -v <pwm>
```

The PWM value is on a `0-255` scale. Examples:

```bash
# About 50 percent PWM on fan channel 1
/hive/opt/octofan/fan_controller_cli -f 1 -v 128

# About 35 percent PWM on fan channel 1
/hive/opt/octofan/fan_controller_cli -f 1 -v 89
```

The verified syntax for changing a fan channel's startup PWM is:

```text
-d <fan_no> -v <pwm>
```

Example:

```bash
/hive/opt/octofan/fan_controller_cli -d 1 -v 89
```

The controller also exposes a maximum-RPM calibration/test operation:

```text
-t
```

and a target-RPM operation:

```text
-m <fan_no> -v <RPM>
```

### Other verified controller operations

The controller help exposed these operations:

```text
-o <x,y,flag> -v <text>      OLED output
-x                            Reset rig
-p                            Power rig down / soft power action
-b                            Enter bootloader
-bx                           Exit bootloader
-t                            Test maximum fan speed for percentage calculation
-f <fan_no> -v <pwm>          Set fan PWM
-d <fan_no> -v <pwm>          Set startup PWM
-m <fan_no> -v <RPM>          Set target RPM
-l <led_no> -v <value>        Set LED value
-w <short timeout> -v <long timeout>  Set watchdog timeout values
-s                            Watchdog reset
```

### Important fan-control behavior

HiveOS normally runs Octominer control processes including `octofan`, `autofan`, and the Octominer watchdog. Therefore a one-shot direct `-f` PWM command may be overwritten by automatic fan control. Do not assume a manual PWM command establishes a persistent minimum fan floor.

If the operational goal is "never let the chassis fans fall below X percent," inspect and modify the active HiveOS/Octofan automatic-fan policy rather than repeatedly issuing direct `-f` commands.

On the tested chassis, fans run at failsafe/high speed before the Octominer software stack takes control. During normal HiveOS operation, software lowers them. If Linux shuts down while controller/PSU auxiliary power remains present, the fans may return to full failsafe speed and remain there. The controller `-p` operation was tested and behaved like a soft chassis power-button action; it did not by itself remove controller/fan power or solve the post-shutdown full-speed fan condition.

## Important lessons

- A front-panel IP can be stale; verify the live address in the OS.
- WOL does not depend on the sleeping host retaining an IP address; the Magic Packet targets the NIC MAC. A stable IP is needed for reliable post-wake management/SSH.
- `ethtool -s eth0 wol g` alone is not persistent on this Hive/Ubuntu installation.
- On this systemd 249 installation, `WakeOnLan=magic` belongs in a `.link` file under `[Link]`, not in the `.network` file.
- Preserve `/etc/systemd/network/20-ethernet.network`; it is the active DHCP network definition.
- AC-loss auto-power-on and WOL are independent mechanisms and were tested independently.
- Direct fan PWM is not the same as a persistent automatic-fan minimum; distinguish controller commands from HiveOS `autofan` policy.
- Controller-reported PSU AC input is useful chassis telemetry but should not be represented as a calibrated wall-meter measurement.
