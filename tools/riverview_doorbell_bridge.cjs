// Riverview-owned bounded RV-008.3 browser bridge.
// Version: 1.0.0 | 2026-08-14
// No arbitrary browser, prompt, selector, navigation, or script interface.

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const VERSION = '1.0.0';
const OPERATION = 'ring_riverview_doorbell';
const WAKE_TEXT = 'Riverview doorbell v1: inspect the Riverview MCP mailbox.';
const ROOT = path.resolve(__dirname, '..');
const CONFIG = process.env.RIVERVIEW_DOORBELL_CONFIG || path.join(ROOT, 'runtime', 'doorbell', 'config', 'doorbell.json');
const JOURNAL = path.join(ROOT, 'runtime', 'doorbell', 'diagnostics', 'evidence.json');
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function now() { return new Date().toISOString(); }
function targetRef(id) { return `target-sha256:${crypto.createHash('sha256').update(id).digest('hex')}`; }
function loadConfig() {
  const raw = JSON.parse(fs.readFileSync(CONFIG, 'utf8'));
  const allowed = ['adapter_version', 'browser_executable', 'cdp_port', 'conversation_id'];
  if (Object.keys(raw).sort().join(',') !== allowed.join(',')) throw Error('RIV-PLY-0011');
  if (!UUID.test(raw.conversation_id) || !Number.isInteger(raw.cdp_port) || raw.cdp_port < 9225 || raw.cdp_port > 9325) throw Error('RIV-PLY-0011');
  if (typeof raw.browser_executable !== 'string' || !path.isAbsolute(raw.browser_executable)) throw Error('RIV-PLY-0011');
  return raw;
}
function selectExactTarget(targets, conversationId) {
  const matches = targets.filter(item => { try { return item.type === 'page' && new URL(item.url).hostname === 'chatgpt.com' && new URL(item.url).pathname === `/c/${conversationId}` && item.webSocketDebuggerUrl; } catch { return false; } });
  if (matches.length === 0) throw Error('RIV-PLY-0005');
  if (matches.length > 1) throw Error('RIV-PLY-0006');
  return matches[0];
}
async function exactTarget(config) {
  const response = await fetch(`http://127.0.0.1:${config.cdp_port}/json/list`);
  if (!response.ok) throw Error('RIV-PLY-0003');
  return selectExactTarget(await response.json(), config.conversation_id);
}
function connect(target, timeout) {
  const socket = new WebSocket(target.webSocketDebuggerUrl); let id = 0; const pending = new Map();
  socket.onmessage = event => { const message = JSON.parse(event.data); const item = pending.get(message.id); if (!item) return; pending.delete(message.id); message.error ? item.reject(Error(message.error.message)) : item.resolve(message.result); };
  const opened = new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = () => reject(Error('RIV-PLY-0004')); });
  const call = (method, params = {}) => new Promise((resolve, reject) => { const key = ++id; const timer = setTimeout(() => { pending.delete(key); reject(Error('RIV-PLY-0009')); }, timeout); pending.set(key, { resolve: value => { clearTimeout(timer); resolve(value); }, reject }); socket.send(JSON.stringify({ id: key, method, params })); });
  return { socket, opened, call };
}
const READINESS = `(()=>{const b=document.body?.innerText||'';const blocked=/log in|sign in|verify you are human|captcha|something went wrong/i.test(b);const e=document.querySelector('#prompt-textarea[contenteditable="true"],div[contenteditable="true"][aria-label="Chat with ChatGPT"]');const r=e?.getBoundingClientRect?.();return {authenticated:!blocked,composer:!!e&&!!r&&r.width>0&&r.height>0&&!e.disabled};})()`;
const FIXED_ACTION = `(()=>{const e=document.querySelector('#prompt-textarea[contenteditable="true"],div[contenteditable="true"][aria-label="Chat with ChatGPT"]');if(!e)return 'composer_unavailable';e.focus();e.replaceChildren();const p=document.createElement('p');p.textContent=${JSON.stringify(WAKE_TEXT)};e.appendChild(p);e.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:${JSON.stringify(WAKE_TEXT)}}));const b=e.closest('form')?.querySelector('button[type="submit"],button[aria-label*="Send" i],button[aria-label*="Submit" i]');if(b&&!b.disabled){b.click();return 'submitted';}e.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));return 'submitted';})()`;
function readJournal() { try { return JSON.parse(fs.readFileSync(JOURNAL, 'utf8')); } catch { return {}; } }
function writeJournal(value) { fs.mkdirSync(path.dirname(JOURNAL), { recursive: true }); const tmp = `${JOURNAL}.${process.pid}.tmp`; fs.writeFileSync(tmp, JSON.stringify(value, null, 2) + '\n'); fs.renameSync(tmp, JOURNAL); }
function result(input, status, failure, evidence, started, attempt, config) { return { attempt_id: attempt, request_id: input.request_id, correlation_id: input.correlation_id, bridge_version: VERSION, designated_target_ref: targetRef(config.conversation_id), started_at: started, completed_at: now(), status, failure_class: failure || null, evidence_ref: evidence || null }; }
function validate(input) { const keys = Object.keys(input || {}).sort().join(','); if (keys !== 'correlation_id,operation,request_id,timeout_seconds' || input.operation !== OPERATION || !UUID.test(input.request_id) || !UUID.test(input.correlation_id) || !Number.isInteger(input.timeout_seconds) || input.timeout_seconds < 1 || input.timeout_seconds > 120) throw Error('RIV-PLY-0002'); }
async function preflight() { const out = { bridge_version: VERSION, browser_runtime: false, cdp_available: false, authenticated_session: false, designated_target_configured: false, exact_target_resolvable: false, fixed_action_available: true, ready: false }; let config; try { config = loadConfig(); out.designated_target_configured = true; out.browser_runtime = fs.existsSync(config.browser_executable); const target = await exactTarget(config); out.cdp_available = true; out.exact_target_resolvable = !!target; const connection = connect(target, 5000); await connection.opened; const probe = await connection.call('Runtime.evaluate', { returnByValue: true, expression: READINESS }); out.authenticated_session = probe?.result?.value?.authenticated === true && probe?.result?.value?.composer === true; connection.socket.close(); } catch { /* metadata-only fail closed */ } out.ready = out.browser_runtime && out.cdp_available && out.authenticated_session && out.designated_target_configured && out.exact_target_resolvable; return out; }
async function ring(input) { validate(input); const started = now(); const config = loadConfig(); const key = `${input.request_id}:${input.correlation_id}`; const journal = readJournal(); if (journal[key]?.status === 'succeeded') return { ...journal[key], status: 'already_succeeded' }; const target = await exactTarget(config); const connection = connect(target, input.timeout_seconds * 1000); await connection.opened; const probe = await connection.call('Runtime.evaluate', { returnByValue: true, expression: READINESS }); if (!probe?.result?.value?.authenticated) throw Error('RIV-PLY-0004'); if (!probe?.result?.value?.composer) throw Error('RIV-PLY-0007'); const action = await connection.call('Runtime.evaluate', { returnByValue: true, expression: FIXED_ACTION }); connection.socket.close(); if (action?.result?.value !== 'submitted') throw Error('RIV-PLY-0008'); const output = result(input, 'succeeded', null, `riverview://doorbell/${crypto.randomUUID()}`, started, crypto.randomUUID(), config); journal[key] = output; writeJournal(journal); return output; }
async function main() { try { if (process.argv.includes('--preflight')) { console.log(JSON.stringify(await preflight())); return; } if (!process.argv.includes('--ring')) throw Error('RIV-PLY-0002'); let text = ''; for await (const chunk of process.stdin) text += chunk; console.log(JSON.stringify(await ring(JSON.parse(text)))); } catch (error) { console.log(JSON.stringify({ operation: OPERATION, bridge_version: VERSION, status: 'failed', failure_class: error.message || 'RIV-PLY-0002' })); process.exitCode = 2; } }
if (require.main === module) main();
module.exports = { FIXED_ACTION, OPERATION, WAKE_TEXT, loadConfig, selectExactTarget };
