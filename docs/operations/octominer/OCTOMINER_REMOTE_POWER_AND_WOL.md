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

## Important lessons

- A front-panel IP can be stale; verify the live address in the OS.
- WOL does not depend on the sleeping host retaining an IP address; the Magic Packet targets the NIC MAC. A stable IP is needed for reliable post-wake management/SSH.
- `ethtool -s eth0 wol g` alone is not persistent on this Hive/Ubuntu installation.
- On this systemd 249 installation, `WakeOnLan=magic` belongs in a `.link` file under `[Link]`, not in the `.network` file.
- Preserve `/etc/systemd/network/20-ethernet.network`; it is the active DHCP network definition.
- AC-loss auto-power-on and WOL are independent mechanisms and were tested independently.
