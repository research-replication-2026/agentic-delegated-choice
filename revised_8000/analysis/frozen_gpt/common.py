"""Shared offline utilities. Importing this module cannot make an API call."""
import csv
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
REV = BASE.parent
SOURCE = REV.parent
MODEL = 'gpt-5.4-mini-2026-03-17'
CONTRASTS = [('C','S'), ('C','I'), ('I','S'), ('N','S')]


def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def save(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def verify_freeze():
    manifest = json.loads((BASE/'frozen/manifest.json').read_text())
    for item in manifest['files']:
        if digest(BASE/item['path']) != item['sha256']:
            raise ValueError('Frozen file changed: ' + item['path'])
    for item in manifest['protected_sources']:
        if digest(item['path']) != item['sha256']:
            raise ValueError('Historical/original file changed: ' + item['path'])
    original_report=BASE/'reports/manuscript_protection.json'
    if original_report.exists():
        protection=json.loads(original_report.read_text());original=Path(protection['original'])
        if digest(original)!=protection['original_sha256'] or original.stat().st_mode & 0o222:
            raise ValueError('Original manuscript contents or read-only protection changed')
    return manifest


def validate_schema(data, schema, at='$'):
    """Validate precisely the keywords used in the unchanged historical schema.

    Unsupported validation keywords fail closed instead of silently being ignored.
    Schema descriptions/titles/$schema are annotations, not validation rules.
    """
    allowed = {'$schema','title','description','type','additionalProperties','required',
               'properties','items','minItems','uniqueItems','enum','const'}
    if set(schema)-allowed:
        raise ValueError('Unsupported schema keywords: ' + str(set(schema)-allowed))
    typ = schema.get('type')
    ok = {'object': lambda: isinstance(data,dict), 'array':lambda:isinstance(data,list),
          'string':lambda:isinstance(data,str), 'boolean':lambda:type(data) is bool,
          'integer':lambda:type(data) is int, 'number':lambda:type(data) in (int,float)}
    errors=[]
    if typ and (typ not in ok or not ok[typ]()):
        return [at + ': wrong type ' + str(typ)]
    if 'enum' in schema and data not in schema['enum']:
        errors.append(at + ': enum')
    if 'const' in schema and (type(data) is not type(schema['const']) or data != schema['const']):
        errors.append(at + ': const')
    if isinstance(data,dict):
        errors += [at + ': missing ' + k for k in schema.get('required',[]) if k not in data]
        if schema.get('additionalProperties') is False:
            errors += [at + ': extra ' + k for k in data if k not in schema.get('properties',{})]
        for k,v in schema.get('properties',{}).items():
            if k in data:
                errors += validate_schema(data[k],v,at+'.'+k)
    if isinstance(data,list):
        if len(data)<schema.get('minItems',0): errors.append(at+': minItems')
        if schema.get('uniqueItems') and len({canonical(v) for v in data})!=len(data): errors.append(at+': uniqueItems')
        if 'items' in schema:
            for i,v in enumerate(data): errors += validate_schema(v,schema['items'],at+f'[{i}]')
    return errors
