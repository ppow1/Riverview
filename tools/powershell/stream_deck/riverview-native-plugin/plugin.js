import { spawn } from "node:child_process";

const PLUGIN_UUID = "com.riverview.operator";
const CONTROL_SCRIPT = "A:\\Riverview\\repo\\tools\\powershell\\stream_deck\\Invoke-RiverviewStreamDeckControl.ps1";
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

function run(control, gesture) {
  const child = spawn("pwsh.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", CONTROL_SCRIPT, "-Control", control, "-Gesture", gesture], {
    detached: true,
    stdio: "ignore",
    windowsHide: true
  });
  child.unref();
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
    run(control, "long");
  }, LONG_PRESS_MS) };
  presses.set(context, press);
  title(context, "HOLD");
}

function finishShortPress(context, control) {
  const previous = taps.get(context);
  if (previous) {
    clearTimer(taps, context);
    title(context, "OPENING");
    run(control, "double");
    return;
  }
  const timer = setTimeout(() => {
    taps.delete(context);
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
  if (payload.event === "willAppear") {
    const control = ACTIONS[payload.action];
    if (control) { contexts.set(payload.context, control); title(payload.context, control.toUpperCase()); }
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
  socket = new WebSocket(`ws://127.0.0.1:${args.port}`);
  socket.addEventListener("open", () => socket.send(JSON.stringify({ event: args.registerEvent, uuid: PLUGIN_UUID })));
  socket.addEventListener("message", handle);
  socket.addEventListener("close", () => process.exit(0));
  socket.addEventListener("error", (error) => console.error("RIV-SD-0002: Stream Deck plugin socket error", error));
}

main();
