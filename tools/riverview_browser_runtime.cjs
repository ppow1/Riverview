// Riverview-owned Chromium lifecycle helper.
// Version: 1.0.0 | 2026-08-14
// Starts only the configured Riverview profile and localhost CDP endpoint.

const fs = require('node:fs');
const { spawn } = require('node:child_process');
const path = require('node:path');
const bridge = require('./riverview_doorbell_bridge.cjs');

const ROOT = path.resolve(__dirname, '..');
const RUNTIME_ROOT = path.resolve(ROOT, '..', 'runtime');
const PROFILE = path.join(RUNTIME_ROOT, 'browser', 'profile');
const PID_FILE = path.join(RUNTIME_ROOT, 'browser', 'runtime.json');

async function main() {
  let config;
  try { config = bridge.loadConfig(); } catch (error) { console.log(JSON.stringify({ ready: false, failure_class: 'RIV-PLY-0010' })); process.exitCode = 2; return; }
  if (process.argv.includes('--preflight')) { console.log(JSON.stringify(await bridgePreflight())); return; }
  if (!process.argv.includes('--start')) throw Error('RIV-PLY-0012: named lifecycle operation required');
  const existing = await bridgePreflight();
  if (existing.cdp_available) { console.log(JSON.stringify({ status: 'already_ready', cdp_port: config.cdp_port })); return; }
  if (!fs.existsSync(config.browser_executable)) throw Error('RIV-PLY-0013: configured browser executable unavailable');
  fs.mkdirSync(PROFILE, { recursive: true });
  const child = spawn(config.browser_executable, [`--remote-debugging-port=${config.cdp_port}`, '--remote-debugging-address=127.0.0.1', `--user-data-dir=${PROFILE}`, '--no-first-run', '--no-default-browser-check', `https://chatgpt.com/c/${config.conversation_id}`], { detached: true, stdio: 'ignore' });
  fs.mkdirSync(path.dirname(PID_FILE), { recursive: true }); fs.writeFileSync(PID_FILE, JSON.stringify({ pid: child.pid, cdp_port: config.cdp_port, profile: PROFILE, started_at: new Date().toISOString() }) + '\n'); child.unref();
  console.log(JSON.stringify({ status: 'started', pid: child.pid, cdp_port: config.cdp_port, profile: PROFILE }));
}
async function bridgePreflight() { const child = require('./riverview_doorbell_bridge.cjs'); const out = { cdp_available: false, browser_runtime: false, profile: PROFILE }; try { const c = child.loadConfig(); out.browser_runtime = fs.existsSync(c.browser_executable); const r = await fetch(`http://127.0.0.1:${c.cdp_port}/json/version`); out.cdp_available = r.ok; } catch { /* bounded status */ } return out; }
main().catch(error => { console.log(JSON.stringify({ status: 'failed', failure_class: error.message })); process.exitCode = 2; });
