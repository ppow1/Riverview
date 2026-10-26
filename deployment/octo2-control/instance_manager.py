#!/usr/bin/env python3
"""Version 0.6.2 source snapshot (OCTOMINER2, 2026-10-26): expandable llama.cpp instance allocator."""
import json, os, re, socket, subprocess, threading, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path("/opt/riverview-octo-control")
REGISTRY=ROOT/"instances.json"
LLAMA="/opt/llama.cpp/build/bin/llama-server"
LOCK=threading.RLock()
PORT_MIN,PORT_MAX=8110,8199
RESERVE_MARGIN_MB=512

def run(args,timeout=20):
    try:return subprocess.run(args,text=True,capture_output=True,timeout=timeout)
    except Exception as exc:return type("R",(),{"returncode":1,"stdout":"","stderr":str(exc)})()
def load_registry():
    try:return json.loads(REGISTRY.read_text())
    except Exception:return {}
def save_registry(data):
    tmp=REGISTRY.with_suffix(".json.tmp");tmp.write_text(json.dumps(data,indent=2)+"\n");os.replace(tmp,REGISTRY)
def valid_id(value):
    value=str(value or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}",value):raise ValueError("instance_id must use 1-40 lowercase letters, numbers, or hyphens")
    return value
def unit_name(instance_id):return f"riverview-llama-{instance_id}.service"
def active(instance_id):return run(["systemctl","is-active","--quiet",unit_name(instance_id)]).returncode==0
def ready(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health",timeout=1.5) as response:return json.loads(response.read()).get("status")=="ok"
    except Exception:return False
def gpu_inventory():
    fields="index,name,memory.total,memory.used,utilization.gpu,temperature.gpu,power.draw"
    r=run(["nvidia-smi",f"--query-gpu={fields}","--format=csv,noheader,nounits"])
    out=[]
    for line in r.stdout.splitlines():
        x=[v.strip() for v in line.split(",")]
        if len(x)==7:
            out.append({"index":int(x[0]),"name":x[1],"memory_total_mb":int(x[2]),"memory_used_mb":int(x[3]),
                        "utilization_percent":float(x[4]),"temperature_c":float(x[5]),"power_w":float(x[6])})
    return out
def port_free(port):
    with socket.socket() as s:
        try:s.bind(("0.0.0.0",int(port)));return True
        except OSError:return False
def allocate_port(registry,requested=None):
    used={int(x.get("port",0)) for x in registry.values() if x.get("desired_state")=="running" or active(x["instance_id"])}
    if requested is not None:
        port=int(requested)
        if not 1024<=port<=65535:raise ValueError("port must be between 1024 and 65535")
        if port in used or not port_free(port):raise ValueError(f"port {port} is unavailable")
        return port
    for port in range(PORT_MIN,PORT_MAX+1):
        if port not in used and port_free(port):return port
    raise RuntimeError("no free instance port is available")
def normalize_gpus(value,inventory):
    if isinstance(value,str):value=[x.strip() for x in value.split(",") if x.strip()]
    if not isinstance(value,list) or not value:raise ValueError("gpu_ids must contain at least one GPU")
    ids=[]
    for item in value:
        idx=int(item)
        if idx not in {g["index"] for g in inventory}:raise ValueError(f"GPU {idx} does not exist")
        if idx not in ids:ids.append(idx)
    return ids
def reservations(registry):
    result={}
    for item in registry.values():
        if item.get("desired_state")!="running" and not active(item["instance_id"]):continue
        for key,value in item.get("gpu_memory_budget_mb",{}).items():result[int(key)]=result.get(int(key),0)+int(value)
    return result
def default_budget(profile,gpus):
    configured=profile.get("gpu_memory_budget_mb")
    if isinstance(configured,dict):return {str(g):int(configured.get(str(g),configured.get("default",5500))) for g in gpus}
    total=int(profile.get("vram_budget_mb",5500))
    each=max(1024,(total+len(gpus)-1)//len(gpus))
    return {str(g):each for g in gpus}
def list_instances():
    with LOCK:registry=load_registry()
    answer=[]
    for item in registry.values():
        row=dict(item);row["service_active"]=active(item["instance_id"]);row["api_ready"]=ready(item["port"])
        row["elapsed_seconds"]=max(0,round(time.time()-float(item.get("started_at",time.time())),1)) if row["service_active"] else None
        answer.append(row)
    return sorted(answer,key=lambda x:x["instance_id"])
def resource_status():
    registry=load_registry();reserved=reservations(registry);instances=list_instances()
    out=[]
    for gpu in gpu_inventory():
        gpu["reserved_mb"]=reserved.get(gpu["index"],0)
        gpu["available_for_reservation_mb"]=max(0,gpu["memory_total_mb"]-RESERVE_MARGIN_MB-gpu["reserved_mb"])
        gpu["instances"]=[x["instance_id"] for x in instances if gpu["index"] in x["gpu_ids"] and x["service_active"]]
        out.append(gpu)
    return out
def create_instance(body,models,host_ip):
    with LOCK:
        registry=load_registry();instance_id=valid_id(body.get("instance_id"));profile_id=str(body.get("profile_id") or "")
        if instance_id in registry:
            if registry[instance_id].get("desired_state")=="running" or active(instance_id):raise ValueError("instance_id is already running")
            registry.pop(instance_id)
        if profile_id not in models:raise ValueError("unknown profile")
        profile=models[profile_id]
        for key in ("model","mmproj"):
            if profile.get(key) and not Path(profile[key]).is_file():raise FileNotFoundError(profile[key])
        inventory=gpu_inventory();gpus=normalize_gpus(body.get("gpu_ids",profile.get("gpus")),inventory)
        policy=str(body.get("sharing_policy","shared")).lower()
        if policy not in ("shared","exclusive"):raise ValueError("sharing_policy must be shared or exclusive")
        budget=body.get("gpu_memory_budget_mb") or default_budget(profile,gpus)
        if isinstance(budget,(int,float,str)):budget={str(g):int(budget) for g in gpus}
        budget={str(g):int(budget.get(str(g),0)) for g in gpus}
        if any(v<512 for v in budget.values()):raise ValueError("each selected GPU requires a reservation of at least 512 MB")
        current=reservations(registry);by_index={g["index"]:g for g in inventory}
        for existing in registry.values():
            overlap=set(gpus)&set(existing.get("gpu_ids",[]))
            if overlap and (policy=="exclusive" or existing.get("sharing_policy")=="exclusive") and (existing.get("desired_state")=="running" or active(existing["instance_id"])):
                raise ValueError(f"exclusive GPU collision with {existing['instance_id']} on {sorted(overlap)}")
        for gpu in gpus:
            if current.get(gpu,0)+budget[str(gpu)]>by_index[gpu]["memory_total_mb"]-RESERVE_MARGIN_MB:
                raise ValueError(f"GPU {gpu} reservation would exceed its safe VRAM capacity")
        port=allocate_port(registry,body.get("port"));context=int(body.get("context",profile["context"]))
        tensor=body.get("tensor_split",profile.get("tensor_split"))
        cmd=[LLAMA,"--model",profile["model"],"--host","0.0.0.0","--port",str(port),"--ctx-size",str(context),
             "--n-gpu-layers","999","--flash-attn","auto","--cache-type-k","q8_0","--cache-type-v","q8_0","--parallel","1","--metrics","--alias",instance_id]
        if len(gpus)>1:
            if not tensor:tensor=",".join("1" for _ in gpus)
            cmd += ["--split-mode","layer","--tensor-split",str(tensor)]
        if profile.get("mmproj"):cmd += ["--mmproj",profile["mmproj"]]
        launch=["systemd-run","--unit",unit_name(instance_id).removesuffix(".service"),"--collect","--property=Type=exec",
                f"--setenv=CUDA_VISIBLE_DEVICES={','.join(map(str,gpus))}"]+cmd
        result=run(launch)
        if result.returncode:raise RuntimeError((result.stderr or result.stdout).strip())
        item={"instance_id":instance_id,"profile_id":profile_id,"name":profile["name"],"gpu_ids":gpus,
              "gpu_memory_budget_mb":budget,"sharing_policy":policy,"port":port,"context":context,"tensor_split":tensor,
              "capabilities":profile["capabilities"],"hermes":profile.get("hermes",{"status":"not-tested"}),
              "api_url":f"http://{host_ip}:{port}/v1","chat_url":f"http://{host_ip}:{port}/",
              "desired_state":"running","started_at":time.time(),"started_at_iso":datetime.now(timezone.utc).isoformat()}
        registry[instance_id]=item;save_registry(registry);return item
def stop_instance(instance_id):
    instance_id=valid_id(instance_id)
    with LOCK:
        registry=load_registry()
        if instance_id not in registry:raise ValueError("unknown instance")
        run(["systemctl","stop",unit_name(instance_id)])
        registry[instance_id]["desired_state"]="stopped";registry[instance_id]["stopped_at_iso"]=datetime.now(timezone.utc).isoformat()
        save_registry(registry);return registry[instance_id]
def delete_instance(instance_id):
    instance_id=valid_id(instance_id)
    with LOCK:
        stop_instance(instance_id);registry=load_registry();item=registry.pop(instance_id);save_registry(registry);return item
def stop_all():
    for item in list_instances():
        if item["service_active"]:stop_instance(item["instance_id"])
    return list_instances()
