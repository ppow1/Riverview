# Start provisional OCTOMINER1 Gemma visual/second-opinion worker.
# Recovery source: docs/operations/LOCAL_AI_CHAT_WORKER_TESTING_AND_STARTUP.md
# Run from Windows PowerShell. Password may be overridden with -Password.

param(
    [string]$HostIp = '192.168.1.160',
    [string]$User = 'root',
    [string]$Password = 'test'
)

Clear-Host
$ErrorActionPreference = 'Stop'

$Plink = (Get-Command plink.exe -ErrorAction SilentlyContinue).Source
if (-not $Plink) { $Plink = "$env:ProgramFiles\PuTTY\plink.exe" }
if (-not (Test-Path -LiteralPath $Plink)) { throw 'plink.exe not found.' }

$Remote = @'
set -e
LLAMA=/opt/llama.cpp/build/bin/llama-server
MODEL=/opt/models/adi-gemma3-12b-ablit-glm5.2-q4_k_m.gguf
MMPROJ=/opt/models/mmproj-gemma3-12b-f16.gguf
PORT=8095
LOG=/opt/localcad/gemma3-12b-ablit-vl-p100-32k.log
PIDFILE=/opt/localcad/gemma3-12b-ablit-vl-p100.pid
mkdir -p /opt/localcad

if curl -fsS http://127.0.0.1:${PORT}/health >/dev/null 2>&1; then
    echo 'GEMMAP100_ALREADY_READY'
    curl -s http://127.0.0.1:${PORT}/health
    exit 0
fi

if [ -f "$PIDFILE" ]; then
    OLD=$(cat "$PIDFILE" 2>/dev/null || true)
    if [ -n "$OLD" ] && kill -0 "$OLD" 2>/dev/null; then
        kill "$OLD" || true
        sleep 3
    fi
fi

CUDA_VISIBLE_DEVICES=1 nohup "$LLAMA" \
    --model "$MODEL" \
    --mmproj "$MMPROJ" \
    --ctx-size 32768 \
    --n-gpu-layers 999 \
    --cache-type-k q8_0 \
    --cache-type-v q8_0 \
    --flash-attn auto \
    --host 0.0.0.0 \
    --port "$PORT" \
    >"$LOG" 2>&1 < /dev/null &
PID=$!
echo "$PID" > "$PIDFILE"

for i in $(seq 1 180); do
    if curl -fsS http://127.0.0.1:${PORT}/health >/dev/null 2>&1; then
        echo 'GEMMAP100_READY'
        curl -s http://127.0.0.1:${PORT}/health
        echo
        nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv
        exit 0
    fi
    if ! kill -0 "$PID" 2>/dev/null; then
        echo 'GEMMAP100_FAILED'
        tail -120 "$LOG"
        exit 1
    fi
    sleep 1
done

echo 'GEMMAP100_TIMEOUT'
tail -120 "$LOG"
exit 1
'@

& $Plink -ssh -batch -pw $Password "$User@$HostIp" $Remote
if ($LASTEXITCODE -ne 0) { throw "Gemma worker startup failed with exit code $LASTEXITCODE." }

$Health = Invoke-RestMethod "http://$HostIp`:8095/health" -TimeoutSec 10
Write-Host "Gemma P100 VLM ready: http://$HostIp`:8095/v1/chat/completions" -ForegroundColor Green
$Health | ConvertTo-Json -Depth 5
