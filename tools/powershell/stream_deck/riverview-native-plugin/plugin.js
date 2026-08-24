import { execFile, spawn } from "node:child_process";
import { appendFileSync, existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PLUGIN_UUID = "com.riverview.operator";
const CONTROL_SCRIPT = "A:\\Riverview\\repo\\tools\\powershell\\stream_deck\\Invoke-RiverviewStreamDeckControl.ps1";
const POWERSHELL = "C:\\Program Files\\PowerShell\\7\\pwsh.exe";
const WORKING_DIRECTORY = "A:\\Riverview\\repo";
const ADB = "C:\\Users\\wille\\Downloads\\platform-tools-latest-windows\\platform-tools\\adb.exe";
const LONG_PRESS_MS = 1250;
const DOUBLE_TAP_MS = 400;
const ACTIONS = {
  "com.riverview.operator.runtime": "runtime",
  "com.riverview.operator.quest-dev": "quest-dev",
  "com.riverview.operator.quest-cast": "quest-cast"
};

let socket = null;
const contexts = new Map();
const presses = new Map();
const taps = new Map();
const LOG_PATH = path.join(path.dirname(fileURLToPath(import.meta.url)), "riverview-native-events.log");
const RUN_LOG_PATH = path.join(path.dirname(fileURLToPath(import.meta.url)), "riverview-native-runs.log");

function diagnostic(message) {
  try { appendFileSync(LOG_PATH, `${new Date().toISOString()} ${message}\n`, "utf8"); }
  catch { /* diagnostics must never take down the action plugin */ }
}

function runDiagnostic(message) {
  try { appendFileSync(RUN_LOG_PATH, `${new Date().toISOString()} ${message}\n`, "utf8"); }
  catch { /* diagnostics must never take down the action plugin */ }
}

function parseArgs(argv) {
  const result = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (!argv[i].startsWith("-")) continue;
    result[argv[i].replace(/^-+/, "")] = argv[i + 1] && !argv[i + 1].startsWith("-") ? argv[++i] : true;
  }
  return result;
}

function send(event, context, payload = {}) {
  if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ event, context, payload }));
}

const STATUS_COLORS = { green: "#18a558", yellow: "#d6b03f", red: "#c73535", gray: "#6b7280" };

function renderStatusImage(label, status) {
  const accent = STATUS_COLORS[status.color] || STATUS_COLORS.gray;
  const value = String(status.value || "...");
  const valueSize = value.length > 8 ? 22 : value.length > 5 ? 28 : 36;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144">
  <rect width="144" height="144" rx="12" fill="#101318"/>
  <rect x="8" y="8" width="128" height="128" rx="10" fill="#151a21" stroke="${accent}" stroke-width="8"/>
  <rect x="17" y="17" width="110" height="25" rx="4" fill="${accent}"/>
  <text x="72" y="36" fill="#ffffff" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="700" text-anchor="middle">${label}</text>
  <text x="72" y="92" fill="#ffffff" font-family="Arial, Helvetica, sans-serif" font-size="${valueSize}" font-weight="800" text-anchor="middle">${value}</text>
</svg>`;
  return `data:image/svg+xml;base64,${Buffer.from(svg, "utf8").toString("base64")}`;
}

function command(command, args, options = {}) {
  return new Promise((resolve, reject) => execFile(command, args, { windowsHide: true, timeout: options.timeout || 2500, cwd: options.cwd }, (error, stdout, stderr) => {
    if (error) { error.stdout = stdout; error.stderr = stderr; reject(error); return; }
    resolve({ stdout, stderr });
  }));
}

function runtimeStatus() {
  const statusPath = path.join(WORKING_DIRECTORY, "runtime", "riverview-supervisor", "status.json");
  if (!existsSync(statusPath)) return { value: "OFF", color: "red" };
  try {
    const state = JSON.parse(readFileSync(statusPath, "utf8"));
    const services = Object.values(state.services || {}).filter((service) => service.enabled !== false);
    const running = services.filter((service) => service.status === "running").length;
    if (services.length > 0 && running === services.length) return { value: "RUNNING", color: "green" };
    if (running > 0) return { value: "DEGRADED", color: "yellow" };
    return { value: "STOPPED", color: "red" };
  } catch { return { value: "ERROR", color: "red" }; }
}

async function questStatus() {
  if (!existsSync(ADB)) return { value: "OFF", color: "red" };
  try {
    const result = await command(ADB, ["devices", "-l"]);
    const rows = result.stdout.split(/\r?\n/).map((line) => line.trim()).filter((line) => /^\S+\s+(device|unauthorized)\b/.test(line));
    const quest = rows.find((line) => /Quest_2|hollywood|Quest/i.test(line));
    if (!quest) return { value: "OFF", color: "red" };
    if (/\bunauthorized\b/.test(quest)) return { value: "BLOCKED", color: "yellow" };
    const serial = quest.split(/\s+/)[0];
    return { value: serial.includes(":") || serial.includes("_adb-tls") ? "ADB" : "USB", color: serial.includes(":") || serial.includes("_adb-tls") ? "green" : "yellow" };
  } catch { return { value: "OFF", color: "red" }; }
}

async function statusFor(control) {
  if (control === "runtime") return runtimeStatus();
  if (control === "quest-dev") return questStatus();
  return { value: "BLOCKED", color: "yellow" };
}

async function refreshContext(context, control) {
  const status = await statusFor(control);
  send("setImage", context, { image: renderStatusImage(control === "quest-dev" ? "QUEST DEV" : control === "quest-cast" ? "QUEST CAST" : "RUNTIME", status), target: 0 });
  send("setTitle", context, { title: "", target: 0 });
  diagnostic(`status control=${control} value=${status.value} color=${status.color} context=${context}`);
}

async function refreshVisibleContexts() {
  await Promise.all(Array.from(contexts.entries()).map(([context, control]) => refreshContext(context, control)));
}

function run(control, gesture) {
  const args = ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", CONTROL_SCRIPT, "-Control", control, "-Gesture", gesture];
  runDiagnostic(`spawn executable=${POWERSHELL} cwd=${WORKING_DIRECTORY} args=${JSON.stringify(args)} control=${control} gesture=${gesture}`);
  const child = spawn(POWERSHELL, args, {
    cwd: WORKING_DIRECTORY,
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true
  });
  runDiagnostic(`spawned pid=${child.pid ?? "none"} control=${control} gesture=${gesture}`);
  child.stdout.on("data", (data) => runDiagnostic(`stdout pid=${child.pid} ${String(data).trimEnd()}`));
  child.stderr.on("data", (data) => runDiagnostic(`stderr pid=${child.pid} ${String(data).trimEnd()}`));
  child.on("error", (error) => runDiagnostic(`spawn-error pid=${child.pid ?? "none"} name=${error.name} message=${error.message}`));
  child.on("close", (code, signal) => { runDiagnostic(`exit pid=${child.pid ?? "none"} code=${code ?? "none"} signal=${signal ?? "none"} control=${control} gesture=${gesture}`); for (const [context, mappedControl] of contexts) if (mappedControl === control) refreshContext(context, control); });
}

function title(context, text) {
  send("setTitle", context, { title: text, target: 0 });
}

function clearTimer(map, context) {
  const item = map.get(context);
  if (item?.timer) clearTimeout(item.timer);
  map.delete(context);
}

function actionFor(context) { return contexts.get(context); }

function beginPress(context, control) {
  clearTimer(presses, context);
  const press = { control, longTriggered: false, timer: setTimeout(() => {
    press.longTriggered = true;
    clearTimer(taps, context);
    title(context, "STOPPING");
    diagnostic(`gesture=long control=${control} context=${context}`);
    run(control, "long");
  }, LONG_PRESS_MS) };
  presses.set(context, press);
  title(context, "HOLD");
}

function finishShortPress(context, control) {
  const previous = taps.get(context);
  if (previous) {
    clearTimer(taps, context);
    diagnostic(`gesture=double control=${control} context=${context}`);
    title(context, "OPENING");
    run(control, "double");
    return;
  }
  const timer = setTimeout(() => {
    taps.delete(context);
    diagnostic(`gesture=single control=${control} context=${context}`);
    title(context, "STARTING");
    run(control, "single");
  }, DOUBLE_TAP_MS);
  taps.set(context, { timer });
  title(context, "TAP?");
}

function endPress(context) {
  const press = presses.get(context);
  if (!press) return;
  clearTimer(presses, context);
  if (press.longTriggered) return;
  finishShortPress(context, press.control);
}

function handle(message) {
  const payload = JSON.parse(message.data);
  diagnostic(`event=${payload.event} action=${payload.action || ""} context=${payload.context || ""}`);
  if (payload.event === "willAppear") {
    const control = ACTIONS[payload.action];
    if (control) { contexts.set(payload.context, control); refreshContext(payload.context, control); }
  } else if (payload.event === "willDisappear") {
    clearTimer(presses, payload.context); clearTimer(taps, payload.context); contexts.delete(payload.context);
  } else if (payload.event === "keyDown" && actionFor(payload.context)) {
    beginPress(payload.context, actionFor(payload.context));
  } else if (payload.event === "keyUp" && actionFor(payload.context)) {
    endPress(payload.context);
  }
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.port || !args.pluginUUID || !args.registerEvent) throw new Error("RIV-SD-0001: Stream Deck launch arguments missing.");
  diagnostic(`start port=${args.port} pluginUUID=${args.pluginUUID} registerEvent=${args.registerEvent}`);
  socket = new WebSocket(`ws://127.0.0.1:${args.port}`);
  socket.addEventListener("open", () => { diagnostic(`websocket=open registration=send uuid=${args.pluginUUID}`); socket.send(JSON.stringify({ event: args.registerEvent, uuid: args.pluginUUID })); });
  socket.addEventListener("message", handle);
  socket.addEventListener("close", () => process.exit(0));
  socket.addEventListener("error", (error) => { diagnostic(`websocket=error message=${error.message || error}`); console.error("RIV-SD-0002: Stream Deck plugin socket error", error); });
  setInterval(() => refreshVisibleContexts().catch((error) => diagnostic(`status-error message=${error.message}`)), 5000).unref();
}

main();
