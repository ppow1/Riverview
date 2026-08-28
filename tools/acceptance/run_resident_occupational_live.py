import json
import urllib.request
import http.cookiejar
import urllib.error
from pathlib import Path
from uuid import uuid4

BASE = 'http://127.0.0.1:18082'
GRACE = '40f225e2-6f58-55d2-b862-eab7d95700d8'
JESSICA = 'f98ff6cc-907a-5ac9-909f-7165358084d2'

CORPORA = {
    'Grace': [
        'Good evening, Grace.', 'What is currently moving?', 'Anything stuck right now?',
        'What is the CME health and progression state?', 'Do we have enough capacity for another Codex job?',
        'Which resource has the best current availability?', 'What did the latest Comms5 submission become?',
        'Where did my last request go?', 'Have we seen this failure before?',
        'What does the Cookbook say about this symptom?', 'What diagnostics are relevant?',
        'What actually needs the Steward?', 'Can this keep moving without me?',
        'Who owns the current responsibility area?', 'Where are we on the roadmap?',
        'I have three projects around the house.', 'I like your resourcefulness.',
        'This CME discussion is getting old.', 'Why has the active work not moved?',
        'What happened after the last attempt?', 'Which work is ready next?',
        'What is the current objective position?', 'Do we have a fresh C1/C2/C3 observation?',
        'Explain the difference between blocked and Steward-gated work.',
        'Prepare a small bounded request to document a bracket inspection procedure.',
        'What needs my attention after that request?',
    ],
    'Jessica': [
        'Good evening, Jessica.', 'What do we actually know about Grace?',
        'What is established about Alfred?', 'What changed between Grace versions?',
        'What proposals exist for Grace?', 'What evidence supports the current Grace canon?',
        'What do we know authoritatively about Grace childhood?',
        'What remains unknown about Alfred?', 'Compare Grace with Alfred.',
        'Go back to Grace: what is still unknown?', 'What is canon versus proposal here?',
        'Has anything been observed that differs from canon?', 'What evidence is historical rather than canon?',
        'Can an interpretation become canon automatically?', 'What is the current accepted version?',
        'Good afternoon, Jessica.', 'You look nice tonight.', 'I have three character ideas.',
        'What proposals are pending review?', 'Prepare a bounded proposal for Grace based on observed guarded behavior.',
        'What evidence should accompany that proposal?', 'Was the proposal published?',
    ],
}


def call(op, cookie, resident_id, message, conversation_id, session_id=None):
    payload = {'request_id': str(uuid4()), 'correlation_id': str(uuid4()), 'resident_id': resident_id, 'message': message, 'conversation_id': conversation_id}
    if session_id: payload['session_id'] = session_id
    body = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + '/api/chat', data=body, method='POST', headers={'Content-Type': 'application/json', 'Cookie': cookie})
    try:
        with op.open(req, timeout=240) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read().decode('utf-8', 'replace'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return error.code, {'error': 'http_error', 'detail': str(error)}


def run_resident(op, cookie, name, resident_id, turns):
    body = json.dumps({'resident_id': resident_id, 'title': f'{name} occupational acceptance'}).encode()
    req = urllib.request.Request(BASE + '/api/conversations', data=body, method='POST', headers={'Content-Type': 'application/json', 'Cookie': cookie})
    with op.open(req, timeout=30) as response:
        conversation = json.load(response)
    cid = str(conversation['id'])
    results = []
    session_id = None
    for message in turns:
        status, payload = call(op, cookie, resident_id, message, cid, session_id)
        resident = payload.get('resident', {})
        session_id = resident.get('session_id', session_id)
        results.append({'message': message, 'http_status': status, 'model_passes': resident.get('model_passes'), 'selected_capability': resident.get('selected_capability'), 'tool_status': resident.get('tool_status'), 'provider': resident.get('provider'), 'model': resident.get('model'), 'resource': resident.get('resource'), 'package_id': resident.get('package_id'), 'summary': payload.get('response', {}).get('summary', '')[:800]})
    return {'conversation_id': cid, 'session_id': session_id, 'turns': results}


def main():
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with op.open(urllib.request.Request(BASE + '/session', method='POST'), timeout=20) as response:
        response.read()
    cookie = '; '.join(f'{c.name}={c.value}' for c in jar)
    report = {'runtime': None, 'residents': {}}
    with op.open(urllib.request.Request(BASE + '/health'), timeout=20) as response:
        report['runtime'] = json.load(response)
    report['residents']['Grace'] = run_resident(op, cookie, 'Grace', GRACE, CORPORA['Grace'])
    report['residents']['Jessica'] = run_resident(op, cookie, 'Jessica', JESSICA, CORPORA['Jessica'])
    for resident in report['residents'].values():
        stats = {}
        for turn in resident['turns']:
            key = 'no_tool' if not turn['selected_capability'] else 'capability'
            stats[key] = stats.get(key, 0) + 1
            if turn['tool_status']:
                stats['broker_' + str(turn['tool_status'])] = stats.get('broker_' + str(turn['tool_status']), 0) + 1
            if turn['model_passes'] == 2:
                stats['second_pass'] = stats.get('second_pass', 0) + 1
        resident['statistics'] = stats
    out = Path('runtime/acceptance/resident-occupational-live-2026-08-28.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'output': str(out), 'runtime_sha': report['runtime'].get('source_sha'), 'counts': {k: len(v['turns']) for k, v in report['residents'].items()}, 'statistics': {k: v['statistics'] for k, v in report['residents'].items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
