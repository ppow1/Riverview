const test = require('node:test');
const assert = require('node:assert/strict');
const { OPERATION, WAKE_TEXT, selectExactTarget, validate } = require('../tools/riverview_doorbell_bridge.cjs');

const id = '00000000-0000-4000-8000-000000000000';
const page = conversationId => ({ type: 'page', url: `https://chatgpt.com/c/${conversationId}`, webSocketDebuggerUrl: 'ws://riverview-test' });
const projectPage = conversationId => ({ type: 'page', url: `https://chatgpt.com/g/riverview-project/c/${conversationId}`, webSocketDebuggerUrl: 'ws://riverview-project-test' });

test('Riverview target resolution is exact and fail-closed', () => {
assert.equal(selectExactTarget([page(id)], id).url, page(id).url);
assert.equal(selectExactTarget([projectPage(id)], id).url, projectPage(id).url);
assert.doesNotThrow(() => validate({ operation: OPERATION, request_id: id, correlation_id: id, timeout_seconds: 60 }));
assert.throws(() => validate({ operation: OPERATION, request_id: 'bad', correlation_id: id, timeout_seconds: 60 }), /RIV-PLY-0002/);
  assert.throws(() => selectExactTarget([], id), /RIV-PLY-0005/);
  assert.throws(() => selectExactTarget([page(id), page(id)], id), /RIV-PLY-0006/);
  assert.throws(() => selectExactTarget([page('11111111-1111-4111-8111-111111111111')], id), /RIV-PLY-0005/);
});

test('bridge contract fixes operation and wake text', () => {
  assert.equal(OPERATION, 'ring_riverview_doorbell');
  assert.equal(WAKE_TEXT, 'Riverview doorbell v1: inspect the Riverview MCP mailbox.');
});
