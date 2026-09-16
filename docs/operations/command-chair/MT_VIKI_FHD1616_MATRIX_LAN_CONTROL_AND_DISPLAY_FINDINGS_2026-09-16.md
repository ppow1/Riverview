# MT-VIKI FHD1616 Matrix LAN Control and Display Findings — 2026-09-16

Status: Hardware-verified operational evidence.

## Purpose

Record the exact findings from the 2026-09-16 investigation of the Command Chair HDMI matrix so future Riverview/Command Chair work does not have to rediscover its identity, network-control behavior, verified command syntax, EDID state, or role in the display architecture.

## Physical device

- Device: MT-VIKI 16x16 HDMI Matrix
- Label/model observed from physical photographs: `FHD1616 Ver. 1.3`
- Role: 16 HDMI inputs to 16 HDMI outputs; arbitrary source-to-output routing.
- The matrix is already part of the working physical video system feeding the 55-inch TCL Roku TVs.
- One 100-foot HDMI cable has already been purchased and physically tested through the matrix. It works without special cable-compensation/equalization settings. Do not diagnose or tune this working path unless a real fault appears.
- The Steward has already selected the matrix's built-in `4K30Hz 5.1` EDID preset. Do not change or re-investigate EDID without an actual requirement/problem.

## Important architectural finding: Ethernet is control, not video transport

The matrix has an Ethernet/LAN interface. Investigation established that this interface is a matrix-control path; the actual video path remains HDMI. It is not evidence of HDBaseT or HDMI-over-IP video transport.

This means the matrix can remain the deterministic physical HDMI routing backbone while Riverview/Stream Deck/Linux software controls routing over the LAN. A separate future investigation may determine whether TCL Roku/AirPlay or another LAN-video path can coexist as an additional desktop transport layer.

## Verified network identity

Matrix LAN address verified from the Camrui/Linux Daily Driver:

`192.168.1.200`

ICMP test result:

- 4 packets transmitted
- 4 received
- 0% packet loss
- RTT min/avg/max/mdev = `0.113/0.131/0.169/0.022 ms`

The matrix is therefore directly reachable on the local LAN.

## Verified TCP service

A bounded port probe tested TCP ports 23, 80, 5000, 8000, 8080, and 10000.

Result:

- 23 closed
- 80 closed
- 5000 closed
- 8000 closed
- **8080 open**
- 10000 closed

A passive `nc` connection to `192.168.1.200:8080` succeeded. The service emitted no banner.

An HTTP GET to `http://192.168.1.200:8080/` connected successfully but timed out after three seconds with zero bytes received. Therefore, on this physical FHD1616 Ver. 1.3 unit, TCP 8080 must not be treated as an ordinary HTTP/web interface. Operationally it is the raw LAN control socket used below.

## Read/query probes that produced no response

The following non-routing probes produced no response and must not be treated as verified commands for this revision:

- `Status.`
- `1?.`

Do not infer failure of LAN control from that silence; actual routing commands were subsequently proven on the same socket.

A `BeepOFF.` followed by `BeepON.` test also produced no terminal response. Because no independently observable buzzer-state verification was captured, those commands are not recorded here as hardware-verified behavior even though related HD1616-family documentation describes them.

## Hardware-verified routing commands

The Steward identified:

- Camrui/Linux Daily Driver = matrix **Input 5** for the test.
- Observed TV = matrix **Output 3**.
- Normal/restored source for Output 3 at the time of the test = **Input 3**.

The following command was sent over TCP 8080:

`5X3.`

Result: **WORKED**. Output 3 was successfully routed to Input 5 over LAN control.

The following restore command was then sent:

`3X3.`

Result: **WORKED**. Output 3 was successfully restored to Input 3 over LAN control.

Therefore the following control path is hardware-verified:

`Camrui/Linux -> Ethernet/LAN -> 192.168.1.200:8080 -> MT-VIKI FHD1616 -> HDMI routing`

The verified command form is:

`<input>X<output>.`

At minimum, the exact commands `5X3.` and `3X3.` are proven on this physical unit.

## Current architectural interpretation

Do not frame the design as HDMI matrix *versus* network video. The useful hybrid model is:

1. **Physical/recovery video layer:** machines -> HDMI -> MT-VIKI FHD1616 -> HDMI -> TVs.
2. **Matrix control layer:** Riverview / Stream Deck / Linux -> Ethernet -> `192.168.1.200:8080` -> routing commands.
3. **Possible future normal-desktop LAN-video layer:** virtual/physical displays -> encoded network transport -> TCL Roku TVs, if latency, quality, independent-display behavior, and sender support prove acceptable.

The physical HDMI path remains valuable for deterministic console access, boot/recovery/BIOS situations, and as a known-good fallback if network display transport is unavailable.

## Related display investigation state

This matrix investigation occurred while evaluating whether one Ethernet run through the attic might reduce the need for four separate 100-foot HDMI runs.

Known surrounding facts at this checkpoint:

- One 100-foot HDMI run through the matrix is already proven working.
- The TCL television examined is a TCL Roku TV model `55S451`, Roku OS 15.3.
- The TV exposes both Roku Screen Mirroring and Apple AirPlay/HomeKit settings.
- The Camrui/Linux Daily Driver has already successfully created a joined VKMS virtual monitor (`Virtual-1`) with a 4096x2160 mode available and applied.
- The Camrui's built-in Realtek RTL8821CE/`rtw88_8821ce` Wi-Fi does not expose P2P-client/P2P-GO modes, so its built-in Wi-Fi is not currently a viable Miracast/Wi-Fi-Direct sender path.
- AirPlay/LAN video remains an investigation path because it may use the normal IP network rather than requiring the garage-to-TV direct RF topology of standard Miracast.
- Raspberry Pi receiver hardware is explicitly a last-resort path, not the next step.

Do not claim yet that AirPlay/Linux provides a suitable four-screen extended desktop. That remains unproven. Required acceptance questions include interactive latency, 4K image quality, sender/encode load, and whether multiple independent displays can be delivered simultaneously.

## Operational opportunities now enabled

Because raw LAN routing is proven, future bounded Riverview/Command Chair work can implement named routes and scenes such as Dev, Camrui, OCTO1, OCTO2, full-wall, server-view, and recovery layouts without relying on the matrix IR remote or front panel.

Do not hard-code assumed input/output names until the physical 16-input/16-output map is deliberately inventoried. Only Input 5 = Camrui and the tested Output 3 relationship were explicitly identified during this session; Input 3 was the source restored to Output 3, but its semantic machine name was not established here.

## Do-not-repeat notes

- Do not re-test whether `192.168.1.200` is reachable unless network state materially changes.
- Do not re-test whether TCP 8080 is open unless network/firmware state materially changes.
- Do not treat port 8080 as HTTP on this unit.
- Do not use `Status.` or `1?.` as though they are verified query commands on this revision.
- Do not re-prove `5X3.` / `3X3.` unless diagnosing an actual regression.
- Do not tune long-HDMI equalization merely because the feature may exist; the tested 100-foot cable already works.
- Do not change the selected built-in 4K30Hz 5.1 EDID preset without an actual requirement.

## Checkpoint conclusion

The MT-VIKI FHD1616 Ver. 1.3 is not merely a manual HDMI switch in the Command Chair architecture. It is a LAN-addressable 16x16 physical HDMI routing fabric. Its verified control endpoint is `192.168.1.200:8080`, and actual routing was successfully changed and restored from the Camrui/Linux Daily Driver using raw TCP commands. Preserve the matrix as the known-good physical video backbone while evaluating complementary LAN-based display transport separately.