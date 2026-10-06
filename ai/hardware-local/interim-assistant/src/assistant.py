from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime
import json
import urllib.request

ROOT = Path(r"A:\AI\Assistant")
STATE_FILE = ROOT / "data" / "state.json"
LOG_FILE = ROOT / "data" / "assistant.log"

MODEL = "qwen3:8b"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"


def load_state():
    with STATE_FILE.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_state(state):
    temp = STATE_FILE.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    temp.replace(STATE_FILE)


def write_log(text):
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(datetime.now().isoformat() + " " + text + "\n")


def process_command(message, state):
    original = message.strip()
    lower = original.lower().strip()

    prefixes = ["add to today ", "add today ", "put on today ", "put this on today "]
    for prefix in prefixes:
        if lower.startswith(prefix):
            text = original[len(prefix):].strip()
            if not text:
                return None
            state["today"].append(text)
            save_state(state)
            write_log("TODAY ADD: " + text)
            return "Added to Today: " + text

    if lower in ["move last capture to today", "move the last capture to today", "put last capture on today", "put the last capture on today"]:
        captures = state.get("capture", [])
        if not captures:
            return "There is nothing in Capture."
        item = captures.pop()
        text = item["text"]
        state["today"].append(text)
        save_state(state)
        write_log("CAPTURE -> TODAY: " + text)
        return "Moved to Today: " + text

    waiting_prefixes = ["add to waiting ", "add waiting ", "waiting for ", "add waiting for "]
    for prefix in waiting_prefixes:
        if lower.startswith(prefix):
            text = original[len(prefix):].strip()
            if prefix in ["waiting for ", "add waiting for "]:
                text = "Waiting for " + text
            if not text:
                return None
            state["waiting"].append(text)
            save_state(state)
            write_log("WAITING ADD: " + text)
            return "Added to Waiting: " + text

    complete_prefixes = ["complete today ", "finish today ", "done today "]
    for prefix in complete_prefixes:
        if lower.startswith(prefix):
            number_text = lower[len(prefix):].strip()
            try:
                number = int(number_text)
                index = number - 1
                item = state["today"].pop(index)
                state.setdefault("completed", []).append({"time": datetime.now().isoformat(timespec="seconds"), "text": item})
                save_state(state)
                write_log("COMPLETED: " + item)
                return "Completed: " + item
            except Exception:
                return "I couldn't find that Today item."

    if lower in ["what did i complete today", "what have i completed today", "what did i finish today", "show completed today"]:
        today_date = datetime.now().date().isoformat()
        completed = []
        for item in state.get("completed", []):
            if item.get("time", "").startswith(today_date):
                completed.append(item["text"])
        if not completed:
            return "Nothing has been marked completed today."
        lines = [f"{i+1}. {text}" for i,text in enumerate(completed)]
        return "Completed today:\n" + "\n".join(lines)

    if lower in ["show today", "what is on today", "what's on today", "what do i have today"]:
        items = state.get("today", [])
        if not items:
            return "Today is currently empty."
        lines = [f"{i+1}. {text}" for i,text in enumerate(items)]
        return "Today:\n" + "\n".join(lines)

    return None


def ask_qwen(message, state):
    system = """
You are a lightweight local executive assistant.

The JSON STATE below is authoritative.

Your job is to help the user stay oriented across
multiple projects without inventing information.

Use TODAY first when asked what to work on.

Use PROJECTS, WAITING, MONEY and CAPTURE when relevant.

Be concise and practical.

Do not expose internal reasoning.

Do not claim a task was changed unless the application
actually changed the state.

STATE:

""" + json.dumps(state, indent=2)

    payload = {"model": MODEL, "stream": False, "think": False, "messages": [{"role": "system", "content": system}, {"role": "user", "content": message}]}
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as response:
        result = json.loads(response.read())
    return result["message"]["content"]


HTML = r"""<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<title>Assistant</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; margin: 0; background: #101114; color: #f2f2f2; }
main { max-width: 850px; margin: auto; padding: 18px; }
h1 { margin-bottom: 2px; }
.subtitle { color: #999; margin-bottom: 22px; }
.card { background: #1c1e23; border-radius: 14px; padding: 16px; margin-bottom: 14px; }
.card h2 { margin-top: 0; font-size: 19px; }
.item { padding: 9px 0; border-bottom: 1px solid #333; }
.item:last-child { border-bottom: none; }
textarea { width: 100%; height: 105px; box-sizing: border-box; border: 1px solid #444; border-radius: 12px; background: #15171b; color: white; padding: 12px; font-size: 17px; }
.buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
button { min-height: 48px; border: 0; border-radius: 12px; font-size: 16px; font-weight: 600; }
.primary { background: #f2f2f2; color: #111; }
.secondary { background: #30333a; color: white; }
.small { min-height: 38px; font-size: 14px; }
#answer { white-space: pre-wrap; line-height: 1.45; }
.money { font-size: 18px; }
.captureText { color: #ccc; }
.done { opacity: .45; text-decoration: line-through; }
</style>
</head>
<body>
<main>
<h1>Interim Assistant</h1>
<div class="subtitle">CueMastery • Riverview • Estate • Chemistry</div>
<div class="card"><h2>Talk to me</h2><textarea id="input" placeholder="Tap here and use the iPhone microphone..."></textarea><div class="buttons"><button class="primary" onclick="ask()">ASK ASSISTANT</button><button class="secondary" onclick="capture()">CAPTURE</button></div></div>
<div class="card"><h2>Assistant</h2><div id="answer">Ready.</div></div>
<div class="card"><h2>TODAY</h2><div id="today">Loading...</div></div>
<div class="card"><h2>WAITING</h2><div id="waiting">Loading...</div></div>
<div class="card"><h2>MONEY</h2><div id="money">Loading...</div></div>
<div class="card"><h2>RECENT CAPTURE</h2><div id="capture">Loading...</div></div>
</main>
<script>
async function api(path, method="GET", body=null) { let options={method:method,headers:{"Content-Type":"application/json"}}; if(body!==null){options.body=JSON.stringify(body);} let response=await fetch(path,options); return await response.json(); }
function esc(value) { return String(value).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;"); }
async function refresh() { let state=await api("/state"); let today=""; state.today.forEach((item,index)=>{today+=`<div class="item">${esc(item)}<br><button class="secondary small" onclick="completeToday(${index})">DONE</button></div>`;}); if(!today){today="Nothing currently assigned.";} document.getElementById("today").innerHTML=today; let waiting=""; state.waiting.forEach(item=>{waiting+=`<div class="item">${esc(item)}</div>`;}); document.getElementById("waiting").innerHTML=waiting||"Nothing waiting."; let m=state.money; document.getElementById("money").innerHTML=`<div class="money"><b>$${m.available_now}</b> available now</div><div class="item">+$${m.expected_oct_3} expected Oct. 3</div><div class="item">+$${m.expected_oct_15} expected Oct. 15</div><div class="item">$${m.optional_financing} optional financing — not committed</div>`; let captures=state.capture.slice(-5).reverse(); let captureHTML=""; captures.forEach(item=>{captureHTML+=`<div class="item captureText">${esc(item.text)}</div>`;}); document.getElementById("capture").innerHTML=captureHTML||"Nothing captured yet."; }
async function ask() { let input=document.getElementById("input"); let message=input.value.trim(); if(!message)return; document.getElementById("answer").textContent="Thinking..."; let result=await api("/ask","POST",{message:message}); document.getElementById("answer").textContent=result.answer; input.value=""; }
async function capture() { let input=document.getElementById("input"); let text=input.value.trim(); if(!text)return; let result=await api("/capture","POST",{text:text}); document.getElementById("answer").textContent=result.answer; input.value=""; await refresh(); }
async function completeToday(index) { let result=await api("/today/complete","POST",{index:index}); document.getElementById("answer").textContent=result.answer; await refresh(); }
refresh();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        data = json.dumps(obj, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        if self.path == "/":
            data = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/state":
            self.send_json(load_state())
            return
        self.send_error(404)

    def do_POST(self):
        body = self.read_body()
        if self.path == "/capture":
            text = body.get("text", "").strip()
            if not text:
                self.send_json({"answer":"Nothing to capture."})
                return
            state = load_state()
            state["capture"].append({"time": datetime.now().isoformat(timespec="seconds"), "text": text})
            save_state(state)
            write_log("CAPTURE: " + text)
            self.send_json({"answer":"Captured."})
            return

        if self.path == "/today/complete":
            index = body.get("index")
            state = load_state()
            try:
                item = state["today"].pop(int(index))
                state.setdefault("completed", []).append({"time": datetime.now().isoformat(timespec="seconds"), "text": item})
                save_state(state)
                write_log("COMPLETED: " + item)
                self.send_json({"answer":"Completed: " + item})
            except Exception:
                self.send_json({"answer":"Could not complete that item."},400)
            return

        if self.path == "/ask":
            message = body.get("message", "").strip()
            if not message:
                self.send_json({"answer":"Ask me something."})
                return
            state = load_state()
            command_answer = process_command(message, state)
            if command_answer is not None:
                self.send_json({"answer":command_answer})
                return
            try:
                answer = ask_qwen(message, state)
                write_log("USER: " + message)
                write_log("ASSISTANT: " + answer)
                self.send_json({"answer":answer})
            except Exception as e:
                write_log("ERROR: " + repr(e))
                self.send_json({"answer":"Local model error: " + str(e)},500)
            return
        self.send_error(404)

    def log_message(self,*args):
        pass


print("")
print("INTERIM ASSISTANT v0.2")
print("Listening on port 8765")
print("")

ThreadingHTTPServer(("0.0.0.0",8765), Handler).serve_forever()
