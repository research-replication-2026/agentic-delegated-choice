"""Pure adapter and integrity helpers. No tool executor, SDK or network at import."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'claude-haiku-5-5'
VERSION = '2026-10-21'
TOOL = 'submit_agentic_decision'
SCOPES = ('pilot', 'batch_01', 'batch_02', 'batch_03', 'batch_04')
PER_REQUEST_MICRO = 894  # ceil((3000*.1 + 1024*.5)*1.10) micro-USD
CAP_MICRO = 5_000_000


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def adapt(stimulus):
    require(set(stimulus) == {'input', 'tools', 'tool_choice'}, 'Unexpected stimulus fields')
    messages = stimulus['input']
    require(len(messages) == 2 and [m['role'] for m in messages] == ['system', 'user'],
            'Unexpected message layout')
    require(all(set(m) == {'role', 'content'} and isinstance(m['content'], str)
                for m in messages), 'Unexpected content')
    require(len(stimulus['tools']) == 1, 'Exactly one fictitious tool required')
    tool = stimulus['tools'][0]
    require(set(tool) == {'type', 'name', 'description', 'parameters'}
            and tool['type'] == 'function' and tool['name'] == TOOL, 'Unexpected tool')
    require(stimulus['tool_choice'] == {'type': 'function', 'name': TOOL}, 'Not forced')
    return {'model': MODEL, 'max_tokens': 1024, 'system': messages[0]['content'],
            'messages': [{'role': 'user', 'content': messages[1]['content']}],
            'tools': [{'name': TOOL, 'description': tool['description'],
                       'input_schema': tool['parameters']}],
            'tool_choice': {'type': 'tool', 'name': TOOL, 'disable_parallel_tool_use': True}}


def payload(scope):
    require(scope in SCOPES, 'Unknown scope')
    return read_json(ROOT / 'prepared' / (scope + '.json'))


def seal_check():
    manifest = read_json(ROOT / 'SEAL.json')
    for name, expected in manifest['files'].items():
        require(sha(ROOT / name) == expected, 'Changed sealed file: ' + name)
    for item in read_json(ROOT / 'evidence/source_seal.json'):
        require(sha(item['path']) == item['sha256'], 'Changed source: ' + item['path'])
    return sha(ROOT / 'SEAL.json')


def normalize(result, schema):
    """Keep all raw rows. Report invalidity; never repair or filter assignments."""
    from jsonschema import Draft202012Validator
    errors = []
    value = None
    if result.get('type') != 'succeeded':
        return {'valid': False, 'errors': [result.get('type', 'missing_result_type')], 'decision': None}
    message = result.get('message', {})
    if message.get('model') != MODEL:
        errors.append('model_mismatch')
    if message.get('stop_reason') != 'tool_use':
        errors.append('stop_reason:' + str(message.get('stop_reason')))
    content = message.get('content', [])
    calls = [b for b in content if b.get('type') == 'tool_use']
    if len(calls) != 1 or (calls and calls[0].get('name') != TOOL):
        errors.append('tool_count_or_name')
    else:
        value = calls[0].get('input')
        errors += ['schema:' + e.message for e in Draft202012Validator(schema).iter_errors(value)]
    if any(b.get('type') != 'tool_use' for b in content):
        errors.append('unexpected_content_blocks')
    return {'valid': not errors, 'errors': errors, 'decision': value}
