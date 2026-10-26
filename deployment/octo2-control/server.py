#!/usr/bin/env python3
"""Riverview OCTO Control v0.6.3 — multi-instance and managed workload control."""
import io, json, os, subprocess, time, urllib.request, zipfile
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import instance_manager as instances
import managed_services as managed

ROOT=Path("/opt/riverview-octo-control")
MODELS=json.loads((ROOT/"models.json").read_text())
TOKEN=(ROOT/"control.token").read_text().strip()
STATE=ROOT/"state.json"
LLAMA="/opt/llama.cpp/build/bin/llama-server"
UNIT="riverview-llama.service"
FANCLI="/hive/opt/octofan/fan_controller_cli"
FAN_CHANNELS=(0,2,4,6,8)
FAN_PRESETS={"off":0,"quiet":96,"normal":160,"maximum":255}
VERSION="0.6.3"
HERMES="/usr/local/bin/hermes"
HERMES_HOME="/mnt/octo-models-stage/hermes"
MONITOR=Path("/mnt/octo-models-stage/riverview-octo-monitor")
MONITOR_CURRENT=MONITOR/"current.json"
MONITOR_HISTORY=MONITOR/"load-history.json"
MONITOR_EVENTS=MONITOR/"events.jsonl"
MONITOR_SAMPLES=MONITOR/"telemetry.jsonl"

API_HELP_MD=r'''# Riverview OCTO Control API Help

Controller help version: `0.6.3`

Authoritative dated repository reference:
`docs/operations/octominer/RIVERVIEW_OCTO_CONTROL_FEATURES_AND_API_2026-09-14.md`

Dashboard: `http://192.168.1.162:8180/`

All API requests require the dashboard control token as a Bearer token. Never
paste the real token into documentation or a troubleshooting snapshot.

## How a client receives the token

The API never returns its own control token. An administrator with SSH access
provisions each authorized client once. On the Windows development machine,
copy the token to the clipboard without displaying it:

```powershell
$Token = (ssh.exe octo2 'cat /opt/riverview-octo-control/control.token').Trim()
$Token | Set-Clipboard
Remove-Variable Token
```

For the web dashboard, paste it into **Control token** and click **Save**. That
browser stores it in its own localStorage and sends it with later API calls.
Each additional browser or device must be provisioned separately. For a script,
paste it when `Read-Host` prompts. Do not create a public token-retrieval route.

## PowerShell setup

```powershell
$Base = 'http://192.168.1.162:8180'
$Token = Read-Host 'Control token'
$Headers = @{ Authorization = "Bearer $Token" }
```

## Read status

```powershell
Invoke-RestMethod "$Base/api/v1/status" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/gpus" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/fans" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/models" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/files" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/logs" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/hermes" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/monitoring" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/instances" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/resources/gpus" -Headers $Headers
```

## Independent model instances

```powershell
$Body = @{
    instance_id = 'qwen-small-p100-1a'
    profile_id = 'qwen25-3b-3060'
    gpu_ids = @(1)
    sharing_policy = 'shared'
    gpu_memory_budget_mb = 5000
} | ConvertTo-Json

Invoke-RestMethod "$Base/api/v1/instances" -Method Post -Headers $Headers -ContentType 'application/json' -Body $Body
Invoke-RestMethod "$Base/api/v1/instances/qwen-small-p100-1a" -Method Delete -Headers $Headers
Invoke-RestMethod "$Base/api/v1/instances/stop-all" -Method Post -Headers $Headers -ContentType 'application/json' -Body '{}'
```

The instance API supports dynamically detected GPUs, shared or exclusive
allocations, several GPUs per model, multiple small models on one GPU when VRAM
reservations fit, optional context/tensor split, and automatic ports 8110-8199.

## Start and stop a model

```powershell
$Body = @{ profile_id = 'qwen25-3b-3060' } | ConvertTo-Json
Invoke-RestMethod "$Base/api/v1/deployments" -Method Post -Headers $Headers -ContentType 'application/json' -Body $Body
Invoke-RestMethod "$Base/api/v1/deployments/current" -Method Delete -Headers $Headers
```

Use `GET /api/v1/models` to obtain the current profile IDs.

## Managed workloads

`GET /api/v1/workloads` reports allowlisted systemd-backed workloads, their
running/readiness state, and whether each unit remains enabled at boot. Use
`POST /api/v1/workloads/{id}/start` or `/stop` to start or stop a listed unit.
These actions do not enable or disable the unit. Unknown workload IDs are
rejected.

## Hermes Agent

Only profiles marked Hermes Verified may be configured:

```powershell
$Body = @{ profile_id = 'qwen3-coder-30b-all' } | ConvertTo-Json
Invoke-RestMethod "$Base/api/v1/hermes/configure" -Method Post -Headers $Headers -ContentType 'application/json' -Body $Body
Invoke-RestMethod "$Base/api/v1/hermes/test" -Method Post -Headers $Headers -ContentType 'application/json' -Body '{}'
```

## Set all populated chassis fans

```powershell
$Body = @{ pwm = 160 } | ConvertTo-Json
Invoke-RestMethod "$Base/api/v1/fans" -Method Post -Headers $Headers -ContentType 'application/json' -Body $Body
```

Presets: Quiet `96`, Normal `160`, Maximum `255`, Off `0`. Fans Off is blocked
while a model is active or a GPU is at least 55 C.

## curl example

```bash
curl -H "Authorization: Bearer CONTROL_TOKEN" http://192.168.1.162:8180/api/v1/status
curl -X POST -H "Authorization: Bearer CONTROL_TOKEN" -H "Content-Type: application/json" -d '{"profile_id":"qwen25-3b-3060"}' http://192.168.1.162:8180/api/v1/deployments
```

The dashboard's Download Snapshot button is the recommended snapshot client
because it submits the currently rendered page along with UI state. Its endpoint
is `POST /api/v1/snapshot` and returns an `application/zip` attachment.
'''

API_HELP_HTML='''<!doctype html><html><head><meta charset="utf-8"><title>OCTO Control API Help 0.6.3</title><style>body{font:16px system-ui;max-width:1100px;margin:30px auto;padding:0 20px;background:#101417;color:#e8eef2}pre{background:#1b2328;padding:14px;overflow:auto;border-radius:8px}code{color:#85e6ef}a{color:#85e6ef}li{margin:.35em 0}</style></head><body><h1>Riverview OCTO Control API Help 0.6.3</h1><p><a href="/">Return to dashboard</a></p><p><strong>Dated repository reference:</strong> <a href="https://github.com/ppow1/Riverview/blob/main/docs/operations/octominer/RIVERVIEW_OCTO_CONTROL_FEATURES_AND_API_2026-09-14.md">RIVERVIEW_OCTO_CONTROL_FEATURES_AND_API_2026-09-14.md</a></p><p>All API calls require <code>Authorization: Bearer CONTROL_TOKEN</code>. Never paste the real token into documentation or snapshots.</p><h2>How a client receives the token</h2><p>The API deliberately does not return its own token. An administrator with SSH access provisions each authorized client once. On the Windows development machine, copy it without displaying it:</p><pre>$Token = (ssh.exe -T -n octo2 'cat /opt/riverview-octo-control/control.token').Trim()
$Token | Set-Clipboard
Remove-Variable Token</pre><p>For the dashboard, paste it into <strong>Control token</strong> and click <strong>Save</strong>. That browser stores it in localStorage. Provision every additional browser or device separately. Scripts receive it from the operator through <code>Read-Host</code>. A public Get Token endpoint is intentionally not provided.</p><h2>PowerShell setup</h2><pre>$Base = 'http://192.168.1.162:8180'
$Token = Read-Host 'Control token'
$Headers = @{ Authorization = "Bearer $Token" }</pre><h2>Read status</h2><pre>Invoke-RestMethod "$Base/api/v1/status" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/gpus" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/fans" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/models" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/files" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/logs" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/monitoring" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/hermes" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/instances" -Headers $Headers
Invoke-RestMethod "$Base/api/v1/resources/gpus" -Headers $Headers</pre><h2>Independent model instances</h2><p>Instances support dynamically detected GPUs, shared or exclusive allocation, multiple GPUs per model, multiple small models per GPU when reservations fit, and automatic ports 8110-8199.</p><pre>$Body = @{
    instance_id = 'qwen-small-p100-1a'
    profile_id = 'qwen25-3b-3060'
    gpu_ids = @(1)
    sharing_policy = 'shared'
    gpu_memory_budget_mb = 5000
} | ConvertTo-Json
Invoke-RestMethod "$Base/api/v1/instances" -Method Post -Headers $Headers -ContentType 'application/json' -Body $Body
Invoke-RestMethod "$Base/api/v1/instances/qwen-small-p100-1a" -Method Delete -Headers $Headers
Invoke-RestMethod "$Base/api/v1/instances/stop-all" -Method Post -Headers $Headers -ContentType 'application/json' -Body '{}'</pre><h2>Start and stop Quick Deployment</h2><pre>$Body = @{ profile_id = 'qwen25-3b-3060' } | ConvertTo-Json
Invoke-RestMethod "$Base/api/v1/deployments" -Method Post -Headers $Headers -ContentType 'application/json' -Body $Body
Invoke-RestMethod "$Base/api/v1/deployments/current" -Method Delete -Headers $Headers</pre><p>Use <code>GET /api/v1/models</code> for the current profile IDs.</p><h2>Set chassis fans</h2><pre>$Body = @{ pwm = 160 } | ConvertTo-Json
Invoke-RestMethod "$Base/api/v1/fans" -Method Post -Headers $Headers -ContentType 'application/json' -Body $Body</pre><p>Quiet: 96; Normal: 160; Maximum: 255; Off: 0. Fans Off is safety-gated.</p><h2>curl</h2><pre>curl -H "Authorization: Bearer CONTROL_TOKEN" http://192.168.1.162:8180/api/v1/status
curl -X POST -H "Authorization: Bearer CONTROL_TOKEN" -H "Content-Type: application/json" -d '{"profile_id":"qwen25-3b-3060"}' http://192.168.1.162:8180/api/v1/deployments</pre><h2>Troubleshooting snapshot</h2><p>Use <strong>Download Snapshot</strong> on the dashboard. It captures the rendered page and synchronized OCTO2 diagnostics. The underlying route is <code>POST /api/v1/snapshot</code>.</p><h2>Managed workloads</h2><pre>GET /api/v1/workloads
POST /api/v1/workloads/qwen30b-vision/start
POST /api/v1/workloads/qwen30b-vision/stop</pre><p>Only allowlisted services are controllable. Start/stop leaves the unit enabled-at-boot setting unchanged.</p></body></html>'''

def run(args, check=False):
    return subprocess.run(args, text=True, capture_output=True, check=check)
def active():
    return run(["systemctl","is-active","--quiet",UNIT]).returncode==0
def state():
    try:return json.loads(STATE.read_text())
    except:return {}
def json_file(path,default):
    try:return json.loads(path.read_text())
    except:return default
def monitoring():
    current=json_file(MONITOR_CURRENT,{})
    age=max(0,time.time()-float(current.get("epoch",0))) if current else None
    return {"available":bool(current),"sample_age_seconds":round(age,1) if age is not None else None,
            "current":current,"load_history":json_file(MONITOR_HISTORY,{})}
def hermes_run(args,timeout=30):
    env=os.environ.copy();env["HERMES_HOME"]=HERMES_HOME
    env["PATH"]=str(Path(HERMES).parent)+":"+env.get("PATH","")
    try:return subprocess.run([HERMES]+args,text=True,capture_output=True,env=env,timeout=timeout)
    except Exception as exc:return type("R",(),{"returncode":1,"stdout":"","stderr":str(exc)})()
def hermes_value(key):
    r=hermes_run(["config","get",key])
    lines=[x.strip() for x in r.stdout.splitlines() if x.strip()]
    return lines[-1] if r.returncode==0 and lines else None
def hermes_status():
    installed=Path(HERMES).is_file()
    version=None
    if installed:
        r=hermes_run(["--version"]);version=next((x.strip() for x in r.stdout.splitlines() if x.strip()),None)
    return {"installed":installed,"version":version,"home":HERMES_HOME,
            "provider":hermes_value("model.provider") if installed else None,
            "base_url":hermes_value("model.base_url") if installed else None,
            "model":hermes_value("model.default") if installed else None,
            "context_length":hermes_value("model.context_length") if installed else None}
def hermes_configure(profile_id):
    deployment=state();p=MODELS.get(profile_id)
    if not p:raise ValueError("unknown profile")
    if (p.get("hermes") or {}).get("status")!="verified":raise ValueError("This profile is not Hermes Verified")
    if deployment.get("profile_id")!=profile_id or not active() or not health(p["port"]):raise ValueError("The selected model must be running and ready")
    values={"model.provider":"custom","model.base_url":f"http://127.0.0.1:{p['port']}/v1",
            "model.default":profile_id,"model.context_length":str(p["context"])}
    for key,value in values.items():
        r=hermes_run(["config","set",key,value,"--force"])
        if r.returncode:raise RuntimeError((r.stderr or r.stdout).strip())
    return hermes_status()
def hermes_test():
    if not Path(HERMES).is_file():raise FileNotFoundError(HERMES)
    r=hermes_run(["chat","-q","Reply exactly: HERMES OCTO2 CONNECTION VERIFIED","--oneshot","-Q","--max-turns","2"],180)
    output=(r.stdout+("\n"+r.stderr if r.stderr else "")).strip()
    if r.returncode:raise RuntimeError(output[-4000:] or "Hermes test failed")
    return {"ok":True,"output":output[-4000:],"exit_code":r.returncode}
def health(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health",timeout=2) as r:
            return json.loads(r.read()).get("status")=="ok"
    except:return False
def gpu_data():
    q="index,name,memory.total,memory.used,utilization.gpu,temperature.gpu,power.draw"
    r=run(["nvidia-smi",f"--query-gpu={q}","--format=csv,noheader,nounits"])
    out=[]
    for line in r.stdout.splitlines():
        x=[v.strip() for v in line.split(",")]
        if len(x)==7:out.append(dict(zip(["index","name","memory_total_mb","memory_used_mb","utilization_percent","temperature_c","power_w"],x)))
    return out
def fan_data():
    if not Path(FANCLI).is_file():
        return {"available":False,"channels":list(FAN_CHANNELS),"presets":FAN_PRESETS,"telemetry":"Fan controller utility not found."}
    r=run([FANCLI,"-r"])
    telemetry=(r.stdout or r.stderr).strip()
    return {"available":r.returncode==0,"channels":list(FAN_CHANNELS),"presets":FAN_PRESETS,
            "telemetry":telemetry,"exit_code":r.returncode}
def set_fans(pwm):
    try:pwm=int(pwm)
    except (TypeError,ValueError):raise ValueError("pwm must be an integer from 0 through 255")
    if not 0 <= pwm <= 255:raise ValueError("pwm must be an integer from 0 through 255")
    if not Path(FANCLI).is_file():raise FileNotFoundError(FANCLI)
    temps=[]
    for gpu in gpu_data():
        try:temps.append(float(gpu["temperature_c"]))
        except (TypeError,ValueError):pass
    if pwm==0 and active():raise ValueError("Fans Off is blocked while a model is running")
    if pwm==0 and any(t>=55 for t in temps):raise ValueError("Fans Off is blocked while a GPU is 55 C or hotter")
    results=[]
    for channel in FAN_CHANNELS:
        r=run([FANCLI,"-f",str(channel),"-v",str(pwm)])
        results.append({"channel":channel,"exit_code":r.returncode,"output":(r.stdout or r.stderr).strip()})
        if r.returncode:raise RuntimeError(f"fan channel {channel} failed: {(r.stderr or r.stdout).strip()}")
    time.sleep(.5)
    answer=fan_data();answer.update({"requested_pwm":pwm,"results":results})
    return answer
def model_files():
    root=Path("/mnt/octo-models-stage")
    if not root.is_dir():return []
    return [{"name":p.name,"size_bytes":p.stat().st_size,
             "kind":"projector" if p.name.lower().startswith("mmproj") or ".mmproj-" in p.name.lower() else "model"}
            for p in sorted(root.glob("*.gguf"))]
def status():
    s=state(); port=s.get("port")
    props=run(["systemctl","show",UNIT,"--property=ActiveState,SubState,MainPID","--no-pager"]).stdout
    return {"version":VERSION,"host":os.uname().nodename,"service_active":active(),"api_ready":health(port) if port else False,
            "deployment":s or None,"gpus":gpu_data(),"monitoring":monitoring(),"systemd":props.strip()}
def stop():
    current=state()
    if current:
        current["desired_state"]="stopped"
        current["stopped_at_iso"]=datetime.now(timezone.utc).isoformat()
        STATE.write_text(json.dumps(current,indent=2))
    run(["systemctl","stop",UNIT])
    run(["systemctl","reset-failed",UNIT])
    for _ in range(30):
        if run(["systemctl","show",UNIT,"--property=LoadState","--value"]).stdout.strip()=="not-found":break
        time.sleep(.1)
    return status()
def deploy(profile_id):
    if profile_id not in MODELS: raise ValueError("unknown profile")
    p=MODELS[profile_id]
    for key in ("model","mmproj"):
        if p.get(key) and not Path(p[key]).is_file(): raise FileNotFoundError(p[key])
    instances.stop_all();stop()
    cmd=[LLAMA,"--model",p["model"],"--host","0.0.0.0","--port",str(p["port"]),
         "--ctx-size",str(p["context"]),"--n-gpu-layers","999","--flash-attn","auto",
         "--cache-type-k","q8_0","--cache-type-v","q8_0","--parallel","1","--metrics","--alias",profile_id]
    if p.get("tensor_split"):cmd += ["--split-mode","layer","--tensor-split",p["tensor_split"]]
    if p.get("mmproj"):cmd += ["--mmproj",p["mmproj"]]
    launch=["systemd-run","--unit",UNIT.replace(".service",""),"--collect","--property=Type=exec",
            f"--setenv=CUDA_VISIBLE_DEVICES={p['gpus']}"]+cmd
    r=run(launch)
    if r.returncode:raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    s={"profile_id":profile_id,"name":p["name"],"port":p["port"],"gpus":p["gpus"],
       "capabilities":p["capabilities"],"api_url":f"http://{host_ip()}:{p['port']}/v1",
       "chat_url":f"http://{host_ip()}:{p['port']}/","started_at":time.time(),
       "started_at_iso":datetime.now(timezone.utc).isoformat(),"desired_state":"running",
       "context":p["context"],"hermes":p.get("hermes",{"status":"not-tested"})}
    STATE.write_text(json.dumps(s,indent=2))
    return s
def host_ip():
    addresses = run(["hostname","-I"]).stdout.split()
    lan = [x for x in addresses if x.startswith("192.168.")]
    return lan[0] if lan else (addresses[0] if addresses else "127.0.0.1")
def logs():
    return run(["journalctl","-u",UNIT,"-n","80","--no-pager"]).stdout
def diagnostic_text(args):
    r=run(args);return (r.stdout + ("\nSTDERR:\n"+r.stderr if r.stderr else "")).strip()
def snapshot_zip(client):
    captured=datetime.now(timezone.utc).isoformat()
    safe_html=client.get("page_html","")
    if not isinstance(safe_html,str) or len(safe_html)>5_000_000:raise ValueError("invalid or oversized page_html")
    files={
      "snapshot_manifest.json":json.dumps({"schema_version":"octo-control-snapshot-v1","controller_version":VERSION,"captured_at":captured,
        "host":os.uname().nodename,"privacy_notice":"Control tokens, SSH keys, environment variables, and model contents are excluded."},indent=2),
      "dashboard.html":"<!doctype html>\n"+safe_html,
      "rendered_text.txt":str(client.get("rendered_text", ""))[:2_000_000],
      "ui_state.json":json.dumps(client.get("ui_state",{}),indent=2),
      "status.json":json.dumps(status(),indent=2),
      "gpu_status.json":json.dumps(gpu_data(),indent=2),
      "fan_status.json":json.dumps(fan_data(),indent=2),
      "monitor_current.json":json.dumps(json_file(MONITOR_CURRENT,{}),indent=2),
      "load_history.json":json.dumps(json_file(MONITOR_HISTORY,{}),indent=2),
      "monitor_events.jsonl":MONITOR_EVENTS.read_text()[-2_000_000:] if MONITOR_EVENTS.exists() else "",
      "monitor_telemetry.jsonl":MONITOR_SAMPLES.read_text()[-5_000_000:] if MONITOR_SAMPLES.exists() else "",
      "instances.json":json.dumps(instances.list_instances(),indent=2),
      "gpu_resources.json":json.dumps(instances.resource_status(),indent=2),
      "configured_profiles.json":json.dumps(MODELS,indent=2),
      "model_files.json":json.dumps(model_files(),indent=2),
      "llama_log.txt":logs(),
      "control_service_status.txt":diagnostic_text(["systemctl","status","riverview-octo-control.service","--no-pager","--full"]),
      "llama_service_status.txt":diagnostic_text(["systemctl","status",UNIT,"--no-pager","--full"]),
      "monitor_service_status.txt":diagnostic_text(["systemctl","status","riverview-octo-monitor.service","--no-pager","--full"]),
      "system_uptime.txt":diagnostic_text(["uptime"]),
      "mounts_and_storage.txt":diagnostic_text(["findmnt","-o","SOURCE,TARGET,FSTYPE,SIZE,AVAIL,OPTIONS"]),
      "nvidia-smi.txt":diagnostic_text(["nvidia-smi"]),
      "README.md":"# OCTO2 Troubleshooting Snapshot\n\nContains the rendered dashboard and matching OCTO2 diagnostics captured at "+captured+".\nNo control token, SSH key, environment dump, or model contents are included.\n"
    }
    files["API_HELP.md"]=API_HELP_MD
    if (ROOT/"CONTROL_PLANE_ARCHITECTURE.md").exists():files["CONTROL_PLANE_ARCHITECTURE.md"]=(ROOT/"CONTROL_PLANE_ARCHITECTURE.md").read_text()
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    return out.getvalue(),datetime.now(timezone.utc).strftime("octo2-snapshot-%Y-%m-%dT%H-%M-%SZ.zip")

HTML='''<!doctype html><html><head><meta charset="utf-8"><title>Riverview OCTO Control 0.6.3</title>
<style>body{font:16px system-ui;background:#101417;color:#e8eef2;margin:30px}button,select,input{font:inherit;padding:9px;margin:4px}.card{background:#1b2328;padding:18px;margin:12px 0;border-radius:10px}.ok{color:#64e572}.bad{color:#ff6868}pre{white-space:pre-wrap}</style></head><body>
<h1>Riverview OCTO Control <span class="ok">0.6.3</span></h1><div class="card">Control token <input id="token" type="password"><button onclick="save()">Save</button> <button onclick="snapshot()">Download Snapshot</button> <button onclick="window.open('/help','_blank')">API Help (F1)</button><span id="snapshotstate"></span></div>
<div class="card"><h2>Quick Deployment (replaces all models)</h2><select id="model"></select><button onclick="start()">Start</button><button onclick="stopit()">Stop</button><button onclick="chat()">Open Chat</button><button onclick="refresh()">Refresh</button><div id="state"></div><div id="timing"></div></div>
<div class="card"><h2>Managed Workloads</h2><p>Authenticated controls for explicitly allowlisted systemd model services. Start/stop preserves each service's boot-enabled setting.</p><button onclick="workloadsrefresh()">Refresh workloads</button><div id="workloads"></div></div>
<div class="card"><h2>Model Instances</h2><p>Run independent models on any detected GPU. Shared allocations permit multiple small models on one GPU; VRAM reservations are admission limits.</p><label>Instance <input id="instanceid" value="worker-1"></label><label> GPUs <input id="instancegpus" value="0" size="8"></label><label> Override VRAM/GPU MB <input id="instancebudget" placeholder="profile default" size="10"></label><label> Port <input id="instanceport" placeholder="automatic" size="8"></label><select id="instancepolicy"><option value="shared">Shared GPU</option><option value="exclusive">Exclusive GPU</option></select><button onclick="createInstance()">Start Instance</button><button onclick="stopAllInstances()">Stop All Instances</button><button onclick="instancesrefresh()">Refresh Instances</button><div id="resources"></div><div id="instances"></div></div>
<div class="card"><h2>Hermes Agent</h2><button onclick="startHermes()">Start Model + Hermes</button><button onclick="configureHermes()">Configure Current Model</button><button onclick="testHermes()">Test Hermes</button><button onclick="hermesrefresh()">Refresh Hermes</button><div id="hermesstate"></div><pre id="hermesoutput"></pre></div>
<div class="card"><h2>GPUs</h2><div id="gpus"></div></div>
<div class="card"><h2>Chassis fans</h2><button onclick="fanset(96)">Quiet</button><button onclick="fanset(160)">Normal</button><button onclick="fanset(255)">Maximum</button><button onclick="fanset(0)">Fans Off</button><div id="fanstate"></div><pre id="fans"></pre></div>
<div class="card"><h2>Files on model drive</h2><button onclick="files()">Refresh files</button><div id="files"></div></div><div class="card"><h2>Recent log</h2><button onclick="log()">Load log</button><pre id="log"></pre></div>
<script>let last=null,catalog={};token.value=localStorage.octoToken||'';function save(){localStorage.octoToken=token.value;models().then(refresh)}
async function api(path,opt={}){opt.headers={...(opt.headers||{}),Authorization:'Bearer '+token.value};let r=await fetch(path,opt);let t=await r.text();if(!r.ok)throw Error(t);return t?JSON.parse(t):{}}
async function models(){catalog=await api('/api/v1/models');model.innerHTML=Object.entries(catalog).map(([k,v])=>'<option value="'+k+'">'+v.name+'</option>').join('');model.onchange=hermesrefresh}
async function workloadsrefresh(){try{let list=await api('/api/v1/workloads');workloads.innerHTML=list.length?list.map(x=>'<div class="workload"><h3>'+x.name+'</h3><p><b class="'+(x.api_ready?'ok':x.running?'':'bad')+'">'+(x.api_ready?'RUNNING / READY':x.running?'RUNNING / LOADING':'STOPPED')+'</b> — '+x.unit+' — port '+x.port+' — boot '+(x.enabled_at_boot?'enabled':'disabled')+'</p><button data-workload="'+x.id+'" data-action="start" '+(x.running?'disabled':'')+'>Start / Reload</button><button data-workload="'+x.id+'" data-action="stop" '+(!x.running?'disabled':'')+'>Stop / Unload</button></div>').join(''):'<p>No managed workloads are configured.</p>';workloads.querySelectorAll('button[data-workload]').forEach(b=>b.onclick=()=>workloadaction(b.dataset.workload,b.dataset.action))}catch(e){workloads.textContent=e}}
async function workloadaction(id,action){try{await api('/api/v1/workloads/'+encodeURIComponent(id)+'/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});await workloadsrefresh()}catch(e){alert(e)}}
function duration(v){v=Math.max(0,Math.round(Number(v)||0));let d=Math.floor(v/86400),h=Math.floor(v%86400/3600),m=Math.floor(v%3600/60),s=v%60;return(d?d+'d ':'')+(h?h+'h ':'')+(m?m+'m ':'')+s+'s'}
async function refresh(){try{last=await api('/api/v1/status');let mon=last.monitoring||{},cur=mon.current||{},dep=last.deployment||{},hist=(mon.load_history||{})[dep.profile_id]||{},live=last.service_active||last.api_ready;state.innerHTML='<b class="'+(last.api_ready?'ok':'bad')+'">'+(last.api_ready?'RUNNING / READY':last.service_active?'LOADING':'STOPPED')+'</b>'+(dep.profile_id?'<p><b>'+(live?'Active deployment':'Last deployment record')+':</b> '+dep.name+' ('+dep.profile_id+')</p>':'<p>No deployment record.</p>')+'<pre>'+JSON.stringify(last.deployment,null,2)+'</pre>';timing.innerHTML='<p><b>Machine uptime:</b> '+duration(cur.uptime_seconds)+' &nbsp; <b>Current model:</b> '+(live&&cur.model_elapsed_seconds!=null?duration(cur.model_elapsed_seconds):'none')+' &nbsp; <b>Monitor sample:</b> '+(mon.sample_age_seconds==null?'unavailable':duration(mon.sample_age_seconds)+' ago')+'</p><p><b>Load history:</b> attempts '+(hist.attempts||0)+', ready '+(hist.successes||0)+', failures '+(hist.failures||0)+', previous '+(hist.load_seconds&&hist.load_seconds.length?duration(hist.load_seconds[hist.load_seconds.length-1]):'none')+', average '+(hist.average_load_seconds==null?'none':duration(hist.average_load_seconds))+'</p>';gpus.innerHTML=last.gpus.map(g=>'<p>GPU '+g.index+' — '+g.name+' — '+g.memory_used_mb+'/'+g.memory_total_mb+' MB — '+g.utilization_percent+'% — '+g.temperature_c+' C — '+g.power_w+' W</p>').join('')}catch(e){state.textContent=e}}
async function start(){try{await api('/api/v1/deployments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profile_id:model.value,stop_conflicting_jobs:true})});refresh()}catch(e){alert(e)}}
async function createInstance(){try{let body={instance_id:instanceid.value,profile_id:model.value,gpu_ids:instancegpus.value,sharing_policy:instancepolicy.value};if(instancebudget.value)body.gpu_memory_budget_mb=Number(instancebudget.value);if(instanceport.value)body.port=Number(instanceport.value);await api('/api/v1/instances',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});instancesrefresh()}catch(e){alert(e)}}
async function stopInstance(id){try{await api('/api/v1/instances/'+encodeURIComponent(id),{method:'DELETE'});instancesrefresh()}catch(e){alert(e)}}
async function stopAllInstances(){if(!confirm('Stop every independently managed model instance?'))return;try{await api('/api/v1/instances/stop-all',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});instancesrefresh()}catch(e){alert(e)}}
async function instancesrefresh(){try{let list=await api('/api/v1/instances'),gpu=await api('/api/v1/resources/gpus');resources.innerHTML='<h3>GPU resources</h3>'+gpu.map(g=>'<p><b>GPU '+g.index+'</b> '+g.name+' — actual '+g.memory_used_mb+'/'+g.memory_total_mb+' MB — reserved '+g.reserved_mb+' MB — instances '+(g.instances.join(', ')||'none')+'</p>').join('');instances.innerHTML='<h3>Instances</h3>'+(list.length?list.map(x=>`<div><b>${x.instance_id}</b> — ${x.name} — GPUs ${x.gpu_ids.join(',')} — port ${x.port} — reserved ${JSON.stringify(x.gpu_memory_budget_mb)} — <b class="${x.api_ready?'ok':x.service_active?'':'bad'}">${x.api_ready?'READY':x.service_active?'LOADING':'STOPPED'}</b> <button class="instance-chat" data-url="${x.chat_url}">Chat</button><button class="instance-stop" data-id="${x.instance_id}">Stop &amp; Remove</button></div>`).join(''):'<p>No independent instances.</p>');instances.querySelectorAll('.instance-chat').forEach(b=>b.onclick=()=>window.open(b.dataset.url,'_blank'));instances.querySelectorAll('.instance-stop').forEach(b=>b.onclick=()=>stopInstance(b.dataset.id))}catch(e){instances.textContent=e}}
async function configureHermes(){hermesoutput.textContent='Configuring Hermes...';try{let h=await api('/api/v1/hermes/configure',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profile_id:model.value})});hermesoutput.textContent=JSON.stringify(h,null,2);hermesrefresh()}catch(e){hermesoutput.textContent=e}}
async function testHermes(){hermesoutput.textContent='Testing Hermes; this may take several minutes...';try{let h=await api('/api/v1/hermes/test',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});hermesoutput.textContent=h.output||JSON.stringify(h,null,2)}catch(e){hermesoutput.textContent=e}}
async function startHermes(){let p=catalog[model.value]||{},hs=(p.hermes||{}).status||'not-tested';if(hs!=='verified'){alert('This profile is not Hermes Verified. Status: '+hs);return}hermesoutput.textContent='Starting model and waiting for readiness...';try{await api('/api/v1/deployments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profile_id:model.value,stop_conflicting_jobs:true})});for(let i=0;i<120;i++){await new Promise(r=>setTimeout(r,5000));let s=await api('/api/v1/status');if(s.api_ready){await configureHermes();return}hermesoutput.textContent='Loading model: '+duration((Date.now()/1000)-(s.deployment||{}).started_at)+' elapsed'}throw Error('Model did not become ready within 10 minutes')}catch(e){hermesoutput.textContent=e}}
async function hermesrefresh(){try{let h=await api('/api/v1/hermes'),p=catalog[model.value]||{},c=p.hermes||{status:'not-tested'};hermesstate.innerHTML='<p><b>Selected profile:</b> '+(p.name||model.value)+'</p><p><b>Compatibility:</b> '+c.status+(c.note?' — '+c.note:'')+'</p><p><b>Installed:</b> '+h.installed+' &nbsp; <b>Configured model:</b> '+(h.model||'none')+' &nbsp; <b>Context:</b> '+(h.context_length||'unknown')+'</p>';if(!h.installed)hermesoutput.textContent='Hermes is not installed on this host.'}catch(e){hermesstate.textContent=e}}
async function stopit(){try{await api('/api/v1/deployments/current',{method:'DELETE'});refresh()}catch(e){alert(e)}}
function chat(){if(last&&last.deployment)window.open(last.deployment.chat_url,'_blank')}
async function files(){try{let f=await api('/api/v1/files');document.getElementById('files').innerHTML=f.map(x=>'<p>'+x.kind.toUpperCase()+' — '+x.name+' — '+(x.size_bytes/1073741824).toFixed(2)+' GiB</p>').join('')}catch(e){alert(e)}}
async function fanrefresh(){try{let f=await api('/api/v1/fans');fanstate.innerHTML='<b class="'+(f.available?'ok':'bad')+'">'+(f.available?'CONTROLLER AVAILABLE':'CONTROLLER UNAVAILABLE')+'</b>';fans.textContent=f.telemetry||'No telemetry returned.'}catch(e){fanstate.textContent=e}}
async function fanset(pwm){if(pwm===0&&!confirm('Turn all chassis fans off? This is blocked while a model is running or a GPU is 55 C or hotter.'))return;try{await api('/api/v1/fans',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pwm:pwm})});fanrefresh()}catch(e){alert(e)}}
async function log(){try{document.getElementById('log').textContent=(await api('/api/v1/logs')).log}catch(e){alert(e)}}
async function snapshot(){snapshotstate.textContent=' Building snapshot...';try{let clone=document.documentElement.cloneNode(true);let secret=clone.querySelector('#token');if(secret){secret.removeAttribute('value');secret.value=''}let payload={page_html:clone.outerHTML,rendered_text:document.body.innerText,ui_state:{selected_profile:model.value,deployment:last&&last.deployment,status:last&&{service_active:last.service_active,api_ready:last.api_ready},captured_at:new Date().toISOString(),url:location.href,viewport:{width:innerWidth,height:innerHeight},user_agent:navigator.userAgent}};let r=await fetch('/api/v1/snapshot',{method:'POST',headers:{Authorization:'Bearer '+token.value,'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!r.ok)throw Error(await r.text());let blob=await r.blob();let cd=r.headers.get('Content-Disposition')||'';let match=cd.match(/filename="([^"]+)"/);let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=match?match[1]:'octo2-snapshot.zip';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);snapshotstate.textContent=' Snapshot downloaded.'}catch(e){snapshotstate.textContent=' Snapshot failed: '+e}}
document.addEventListener('keydown',e=>{if(e.key==='F1'){e.preventDefault();window.open('/help','_blank')}})
models().then(()=>{refresh();workloadsrefresh();instancesrefresh();hermesrefresh();fanrefresh();files()});setInterval(refresh,5000);setInterval(workloadsrefresh,5000);setInterval(instancesrefresh,5000);setInterval(fanrefresh,10000)</script></body></html>'''

class H(BaseHTTPRequestHandler):
    def sendj(self,obj,code=200):
        b=json.dumps(obj).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def sendzip(self,b,name):
        self.send_response(200);self.send_header("Content-Type","application/zip");self.send_header("Content-Disposition",f'attachment; filename="{name}"');self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def auth(self):return self.headers.get("Authorization")=="Bearer "+TOKEN
    def do_GET(self):
        if self.path=="/":b=HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(b);return
        if self.path=="/help":b=API_HELP_HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b);return
        if not self.auth():return self.sendj({"error":"unauthorized"},401)
        if self.path=="/api/v1/status":return self.sendj(status())
        if self.path=="/api/v1/gpus":return self.sendj(gpu_data())
        if self.path=="/api/v1/fans":return self.sendj(fan_data())
        if self.path=="/api/v1/models":return self.sendj(MODELS)
        if self.path=="/api/v1/files":return self.sendj(model_files())
        if self.path=="/api/v1/logs":return self.sendj({"log":logs()})
        if self.path=="/api/v1/monitoring":return self.sendj(monitoring())
        if self.path=="/api/v1/hermes":return self.sendj(hermes_status())
        if self.path=="/api/v1/workloads":return self.sendj(managed.list_workloads())
        if self.path=="/api/v1/instances":return self.sendj(instances.list_instances())
        if self.path=="/api/v1/resources/gpus":return self.sendj(instances.resource_status())
        return self.sendj({"error":"not found"},404)
    def do_POST(self):
        if not self.auth():return self.sendj({"error":"unauthorized"},401)
        try:
            n=int(self.headers.get("Content-Length","0"));body=json.loads(self.rfile.read(n) or b"{}")
            if self.path=="/api/v1/snapshot":
                b,name=snapshot_zip(body);return self.sendzip(b,name)
            if self.path.startswith("/api/v1/workloads/"):
                parts=self.path.strip("/").split("/")
                if len(parts)==5 and parts[:3]==["api","v1","workloads"]:
                    return self.sendj(managed.transition_workload(parts[3],parts[4]))
                return self.sendj({"error":"not found"},404)
            if self.path=="/api/v1/fans":return self.sendj(set_fans(body.get("pwm")))
            if self.path=="/api/v1/hermes/configure":return self.sendj(hermes_configure(body.get("profile_id")))
            if self.path=="/api/v1/hermes/test":return self.sendj(hermes_test())
            if self.path=="/api/v1/instances":return self.sendj(instances.create_instance(body,MODELS,host_ip()),202)
            if self.path=="/api/v1/instances/stop-all":return self.sendj(instances.stop_all())
            if self.path.startswith("/api/v1/power/"):return self.sendj({"error":"smart plug not configured"},501)
            if self.path!="/api/v1/deployments":return self.sendj({"error":"not found"},404)
            return self.sendj({"state":"loading","deployment":deploy(body.get("profile_id"))},202)
        except Exception as e:return self.sendj({"error":str(e)},400)
    def do_DELETE(self):
        if not self.auth():return self.sendj({"error":"unauthorized"},401)
        if self.path=="/api/v1/deployments/current":return self.sendj(stop())
        if self.path.startswith("/api/v1/instances/"):
            try:return self.sendj(instances.delete_instance(self.path.rsplit("/",1)[-1]))
            except Exception as e:return self.sendj({"error":str(e)},400)
        return self.sendj({"error":"not found"},404)
    def log_message(self,fmt,*args):print(fmt%args,flush=True)

ThreadingHTTPServer(("0.0.0.0",8180),H).serve_forever()
