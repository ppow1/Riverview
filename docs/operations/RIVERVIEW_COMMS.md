# Riverview Comms

Version: 0.10.0

Riverview Comms is the named ChatGPT application surface for the existing
Riverview read-only MCP model. It uses Streamable HTTP for application
registration and exposes the same fixed tools/resources as the local stdio
relay. PostgreSQL remains authoritative operational state.

The local entrypoint is `python -m riverview.mcp.http_server`. It binds only to
loopback (`127.0.0.1`, by default on port 11825) and serves `/mcp`. The
source-controlled `config/riverview-comms-ingress.Caddyfile.example` follows
the Comms8 Blue boundary: exact `/mcp` POST/OPTIONS and `/healthz` GET paths,
256 KiB request bound, bearer authentication from service environment, and a
loopback upstream. A hosted ChatGPT connection requires an approved HTTPS
ingress with authentication; the local service does not bypass that boundary
or contain credentials.

Generate the non-secret runtime manifest with:

```powershell
.venv\Scripts\python.exe tools\riverview_comms_manifest.py
```

The manifest is written to `A:\Riverview\runtime\comms\manifest.json` unless
`RIVERVIEW_RUNTIME_ROOT` is explicitly set. The application identity is
`Riverview Comms`, distinct from Estate Comms8 and IONOGE Comms9.

The application is read-only. It does not expose arbitrary SQL, filesystem,
shell/process execution, browser control, writes, credentials, secrets, or
Undercurrent data. Conversation text does not create authority.

## Provenance and deployment boundary

Estate Comms8 Blue was the primary provenance implementation. Its candidate
ingress uses a named HTTPS endpoint, exact `/mcp` and `/healthz` routes, a
service-environment bearer credential, a loopback upstream, bounded body size,
and a candidate/tunnel/health acceptance sequence. Its application registration
was a separate ChatGPT workspace/admin action. Those credentials, upstream,
runtime directories, business tools, browser worker, and tunnel are not reused
by Riverview. IONOGE Comms9 and other Estate Comms8 surfaces were secondary
comparison material only.

The Blue lifecycle also confirms that transport discovery (`initialize`,
`tools/list`) is distinct from authoritative mailbox lifecycle. Riverview Comms
is intentionally read-only, so it exposes no create/claim/ack/respond/resolve
operations; mailbox lifecycle remains PostgreSQL/River-owned and is projected
through the existing bounded read model.

The final ChatGPT-side acceptance must show that the designated conversation can
enumerate `Riverview Comms` and retrieve bounded PostgreSQL-backed position and
mailbox projections. A local service start alone is not acceptance.
