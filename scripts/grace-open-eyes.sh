#!/usr/bin/env bash
# Grace Open Eyes: idempotent, bounded reload of the approved vision systemd service.
# Install on OCTO1 as /usr/local/sbin/grace-open-eyes (root:root, mode 0755).
set -Eeuo pipefail

SERVICE=grace-vision.service
LAUNCHER=/usr/local/bin/grace-vision-fast
UUID=GPU-ace423ce-ae61-803e-0734-a907283efe54
URL=http://127.0.0.1:18080
LOCK=/run/lock/grace-open-eyes.lock

exec 9>"$LOCK"
flock -w 10 9 || { echo 'OPEN_EYES_FAIL: another load attempt holds the lock' >&2; exit 20; }

[[ -x "$LAUNCHER" ]] || { echo 'OPEN_EYES_FAIL: launcher missing/not executable' >&2; exit 21; }
# Check the exact currently approved arguments without modifying the launcher.
python3 - "$LAUNCHER" "$UUID" <<'PY'
import re,sys
s=open(sys.argv[1],encoding="utf-8").read()
uuid=sys.argv[2]
for name,pat in [
 ("GPU UUID",rf'CUDA_VISIBLE_DEVICES\s*=\s*["\x27]?{re.escape(uuid)}\b'),
 ("context 32768",r'(?<!\S)(?:-c|--ctx-size)(?:\s+|=)32768\b'),
 ("eight slots",r'(?<!\S)(?:-np|--parallel)(?:\s+|=)8\b'),
 ("port 18080",r'(?<!\S)(?:--port)(?:\s+|=)18080\b'),
]:
 if not re.search(pat,s):
  raise SystemExit("OPEN_EYES_FAIL: launcher does not match approved "+name)
print("APPROVED_LAUNCHER: yes",flush=True)
PY

check_health() {
 python3 - "$URL" <<'PY'
import json,sys,urllib.request
base=sys.argv[1]
def get(path):
 with urllib.request.urlopen(base+path,timeout=3) as r:
  return json.load(r)
h=get('/health')
slots=get('/slots')
assert h.get('status')=='ok',h
assert len(slots)==8 and all(x.get('n_ctx')==4096 for x in slots),[x.get('n_ctx') for x in slots]
print("OPEN_EYES_READY: true; slots=8; context_each=4096",flush=True)
PY
}

if systemctl is-active --quiet "$SERVICE"; then
  echo 'VISION_SERVICE: already active; verifying'
  check_health
  exit 0
fi

# A stopped service is NOT permission to preempt GPU0. Refuse to load if GPU UUID
# is currently used by any compute process, including one owned by another worker.
if ! nvidia-smi --query-gpu=uuid --format=csv,noheader | grep -Fxq "$UUID"; then
  echo 'OPEN_EYES_FAIL: approved GPU UUID not present' >&2
  exit 22
fi
GPU_PIDS="$(nvidia-smi --query-compute-apps=gpu_uuid,pid --format=csv,noheader,nounits | awk -F, -v u="$UUID" '$1 ~ u {gsub(/ /,"",$2); if ($2 ~ /^[0-9]+$/) print $2}')"
if [[ -n "$GPU_PIDS" ]]; then
  echo "OPEN_EYES_FAIL: GPU reserved/occupied by compute PID(s): $GPU_PIDS" >&2
  exit 23
fi

echo 'VISION_SERVICE: starting approved systemd unit'
systemctl start "$SERVICE"

# Bounded wait; failure leaves the unit state visible for operator diagnosis.
for i in $(seq 1 60); do
  if ! systemctl is-active --quiet "$SERVICE"; then
    echo 'OPEN_EYES_FAIL: vision service failed during startup' >&2
    exit 24
  fi
  if check_health >/dev/null 2>&1; then
    echo 'OPEN_EYES_READY: true; slots=8; context_each=4096'
    exit 0
  fi
  sleep 1
done
echo 'OPEN_EYES_FAIL: health/slot verification timed out' >&2
exit 25
