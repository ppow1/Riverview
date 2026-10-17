# Riverview SSH Standard

Status: Canonical operational SSH convention for the Windows development machine and managed Riverview machines.

**File Revision:** 1.0.1
**Updated:** 2026-10-17 — record verified Camrui access and distinguish the Windows SSH client from the Camrui-hosted Codex execution environment. The predecessor contained literal `\n` separators rather than Markdown line breaks; its text was preserved and normalized for readability.
**Predecessor SHA-256:** `230307b57b442dab0c5156222ec5c9e026c4522291fa6bfb177fd21ff180a896`

## Purpose

Riverview uses one consistent OpenSSH client pattern from the Windows development machine:
- Use a named Host alias in C:\Users\wille\.ssh\config.
- The alias maps to the machine's verified IP/hostname.
- Specify the intended SSH user explicitly.
- Specify the intended private IdentityFile.
- Set IdentitiesOnly yes so authentication uses the configured identity rather than unrelated keys offered by an SSH agent.
- Keep ServerAliveInterval 30 and ServerAliveCountMax 3 for managed nodes unless a documented host-specific reason requires otherwise.
- Normal operation is simply ssh <alias>.
- Remote commands use ssh <alias> "<command>".
- The private key is never copied into the repository, documentation, chat, logs, or diagnostic output.

OpenSSH documents IdentityFile as the client authentication identity and IdentitiesOnly yes as restricting authentication to configured identity/certificate files rather than additional agent identities.

## Verified implementation

### OCTOMINER1

Verified 2026-09-21.

Windows SSH config:

```text
Host octo1
    HostName 192.168.1.160
    User root
    IdentityFile C:/Users/wille/.ssh/octominer1_nopass
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

Normal connection:

```powershell
Clear-Host
ssh octo1
```

Verified key-authentication result:
- Windows OpenSSH 9.5p2 selected octominer1_nopass.
- The OctoMiner1 SSH server accepted the key.
- Authentication completed using publickey.
- The remote command executed as root.
- Remote hostname reported OCTOMINER1.
- Exit status was 0.

This is the authoritative current state. The older statement that octominer1_nopass was rejected by OCTOMINER1 is superseded and must not be used for recovery decisions.

Do not change OCTOMINER1 SSH configuration merely to make it resemble an older historical state. The current client-side convention and public-key authentication are already working.

### OCTOMINER2

Verified current configuration:

```text
Host octo2
    HostName 192.168.1.162
    User root
    IdentityFile C:/Users/wille/.ssh/octominer1_nopass
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

Normal connection:

```powershell
Clear-Host
ssh octo2
```

Remote command pattern:

```powershell
Clear-Host
ssh octo2 "nvidia-smi"
```

The same Windows private identity is used for OCTOMINER1 and OCTOMINER2. This is intentional and verified.

### Camrui

Verified from the Windows development workstation on 2026-10-17 with noninteractive public-key authentication:

```powershell
Clear-Host
ssh.exe -o BatchMode=yes camrui "hostname; whoami; pwd"
```

Observed output: hostname `admin1-Default-string`, account `admin1`, working directory `/home/admin1`, exit code `0`. The documented target is `192.168.1.155`; the Camrui OS independently reports that address on `eno1`.

The working alias and identity remain managed by Windows OpenSSH configuration at `C:\Users\wille\.ssh\config`. The exact `IdentityFile` value was not included in the verified command output and is not visible from the Camrui-hosted Linux execution environment. Do not infer, copy, or replace the Windows key. To inspect its non-secret effective mapping on Windows, run:

```powershell
ssh.exe -G camrui | Select-String '^(user|hostname|identityfile|identitiesonly|stricthostkeychecking) '
```

The Codex execution environment for this commissioning session is itself the Camrui Linux host: hostname `admin1-Default-string`, account `admin1`, and local interface `eno1` at `192.168.1.155`. It uses the local host shell and checkout; it does not SSH back to itself and does not import the Windows private key.

## Required standard for additional Riverview machines

The same client-side connection format is to be established for:
- PiKVM / PiCam recovery controller
- Windows development machine when accessed remotely
- future Riverview-managed Linux/Windows nodes

Each machine gets its own descriptive SSH alias. Do not rely on remembering raw IP addresses for normal operations.

Template:

```text
Host <alias>
    HostName <verified-ip-or-hostname>
    User <verified-user>
    IdentityFile C:/Users/wille/.ssh/<verified-private-key>
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

Normal use:

```powershell
Clear-Host
ssh <alias>
```

Remote command:

```powershell
Clear-Host
ssh <alias> "<command>"
```

## Provisioning rule

Before adding a machine to the standard:
1. Verify the physical machine identity and current IP/hostname.
2. Verify SSH is enabled and reachable.
3. Generate or select the intended ED25519 key on the Windows development machine.
4. Install only the corresponding public key into the remote user's authorized-key store.
5. Add the host alias to C:\Users\wille\.ssh\config.
6. Test normal alias-based login with IdentitiesOnly yes.
7. Record the successful authentication evidence in the appropriate operational document.
8. Preserve any existing working fallback access until the new path is independently verified.

Do not assume the same private key should be reused on every machine merely because it is used by both OctoMiners. Key reuse is an explicit provisioning decision; the standard is the connection format, not mandatory key reuse.

## Current pending hosts

The following hosts are required to be brought into this convention, but their exact SSH address/user/key mapping must be verified before documentation claims them as operational:
- PiKVM / PiCam
- Windows development machine

Once each host is verified, add its exact Host block here and to the Windows SSH configuration. Do not invent IP addresses, usernames, or key filenames.

## Recovery principle

If an SSH alias fails:
1. Inspect the Windows SSH configuration first.
2. Confirm the target IP/hostname and physical identity.
3. Run a read-only verbose authentication test.
4. Determine which identity was offered and whether the server accepted it.
5. Only then modify remote authorized_keys, sshd configuration, or client configuration.
6. Preserve at least one verified recovery path before removing or changing another.

For diagnostic output captured for Riverview work, prefer the established PowerShell clipboard-capture convention so the complete result can be pasted into the engineering session without leaving a noisy terminal transcript.

## Current canonical aliases

| Host | Alias | Address | User | Identity | Status |
|---|---|---|---|---|---|
| OCTOMINER1 | octo1 | 192.168.1.160 | root | octominer1_nopass | Verified |
| OCTOMINER2 | octo2 | 192.168.1.162 | root | octominer1_nopass | Verified |
| Camrui | camrui | 192.168.1.155 | admin1 | Existing Windows OpenSSH alias identity; exact `IdentityFile` path not observed by Codex | Verified from Windows; local Codex execution is on Camrui |
| PiKVM / PiCam | TBD | TBD | TBD | TBD | Provision/verify |
| Windows dev machine | TBD | TBD | TBD | TBD | Provision/verify |
