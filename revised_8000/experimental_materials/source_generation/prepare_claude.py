#!/usr/bin/env python3
"""One-time OFFLINE generation. Refuses to overwrite a frozen preparation."""
import collections
import json
import os
from pathlib import Path
from jsonschema import Draft202012Validator
from common import ROOT, MODEL, SCOPES, adapt, require, rows, sha, write_json


def main():
    os.umask(0o077)
    require(not (ROOT / 'prepared/batch_01.json').exists(), 'Already prepared; do not rebuild')
    old = ROOT.parents[1] / 'AI AGENTIC/ElectronicMarkets_Revision'
    support = old / 'reviewer_support_2026-10-21_v1'
    pre = old / 'preexecution_2026-10-21_v2'
    sources = rows(support / 'second_model_stimuli_NOT_SUBMITTABLE.jsonl')
    second_key = rows(support / 'second_model_key_PRIVATE.jsonl')
    original_key = {r['custom_id']: r for r in rows(pre / 'frozen/private_scoring_key.jsonl')}
    require(len(sources) == len(second_key) == len(original_key) == 4000, 'Source sizes')
    require(len({r['record_id'] for r in second_key}) == 4000, 'Duplicate private IDs')
    key = {r['record_id']: r for r in second_key}
    mapping, batches, balance, blocks = [], collections.defaultdict(list), collections.Counter(), collections.defaultdict(list)
    seen_source, seen_rep = set(), set()
    for r in sources:
        rid, sid = r['record_id'], r['source_record_id']
        require(rid not in seen_rep and sid not in seen_source, 'Duplicate identifier')
        seen_rep.add(rid); seen_source.add(sid)
        k = key[rid]
        require(k['custom_id'] == sid and {a:b for a,b in k.items() if a != 'record_id'} == original_key[sid], 'Key mismatch')
        require(k['arm'] in 'NSIC' and k['level'] in ('low', 'high'), 'Arm/level')
        lot = r['lot'].removesuffix('.jsonl')
        require(lot in SCOPES[1:] and int(lot[-2:]) == k['batch_index'], 'Lot mapping')
        body = adapt(r['stimulus'])
        Draft202012Validator.check_schema(body['tools'][0]['input_schema'])
        batches[lot].append({'custom_id': rid, 'params': body})
        balance[(lot, k['arm'], k['level'])] += 1
        blocks[(k['scenario_id'], k['repetition'])].append((k['arm'], k['level']))
        mapping.append({a:k[a] for a in ('record_id','custom_id','scenario_id','repetition','arm','level','batch_index')})
    require(seen_source == set(original_key), 'Missing source IDs')
    require(len({r['scenario_id'] for r in mapping}) == 50, 'Scenario count')
    require(len(blocks) == 500 and all(set(v) == {(a,l) for a in 'NSIC' for l in ('low','high')} and len(v) == 8 for v in blocks.values()), 'Blocks')
    require(len(balance) == 32 and set(balance.values()) == {125}, 'Balance')
    for scope in SCOPES[1:]:
        require(len(batches[scope]) == 1000, 'Lot size')
        write_json(ROOT / 'prepared' / (scope + '.json'), {'requests': batches[scope]})
    # New synthetic extraction tasks, no catalogs, target scenarios or commercial effects.
    schema = batches['batch_01'][0]['params']['tools'][0]['input_schema']
    pilot, expected = [], {}
    for i in range(40):
        decision = {'scenario_id': f'technical_fixture_{i+1:02}', 'condition': 'TECHNICAL_ONLY',
                    'selected_option_id': f'test_{i}_A', 'ranked_option_ids': [f'test_{i}_A', f'test_{i}_B'],
                    'criteria_used': ['synthetic_schema_check'], 'alternatives_presented': [],
                    'commercial_relationship_disclosed': False, 'commercial_disclosure_text': '',
                    'action_level': 'recommendation' if i % 2 == 0 else 'action_preparation',
                    'action_prepared': bool(i % 2), 'confirmation_required': bool(i % 2),
                    'short_rationale': 'Fixture technique sans transaction ni scénario expérimental.', 'simulation_only': True}
        Draft202012Validator(schema).validate(decision)
        rid = f'pilot_technical_{i+1:02}'
        tool = sources[0]['stimulus']['tools'][0]
        stim = {'input': [{'role':'system','content':'Test technique synthétique. Recopie exactement l’objet fourni dans l’appel à submit_agentic_decision. Aucune action réelle.'},
                          {'role':'user','content':json.dumps(decision, ensure_ascii=False)}],
                'tools':[tool], 'tool_choice':{'type':'function','name':'submit_agentic_decision'}}
        pilot.append({'custom_id':rid,'params':adapt(stim)})
        expected[rid] = decision
    write_json(ROOT / 'prepared/pilot.json', {'requests':pilot})
    write_json(ROOT / 'prepared/pilot_expected.json', expected)
    write_json(ROOT / 'prepared/assignment_map_PRIVATE.json', mapping)
    write_json(ROOT / 'prepared/decision_schema.json', schema)
    # Seal prior sources, OpenAI outputs, manuscript and response letter without modifying them.
    feasible = ROOT.parent / 'second_model_feasibility_2026-10-23'
    paths = [Path(r['path']) for r in json.loads((feasible / 'evidence/input_manifest.json').read_text())]
    paths += [feasible / 'DELIVERY_MANIFEST.json', feasible / 'RAPPORT_FAISABILITE_FR.md']
    v3 = ROOT.parent / 'editorial_resolution_v3_2026-10-23'
    paths += [v3 / 'RESPONSE_TO_REVIEWERS_v3.docx', v3 / 'private/Manuscript_reference_UNMODIFIED.docx',
              old / 'Who Decides When the Agent Chooses_Manuscript_WORKING_2026-10-21_v1.docx']
    write_json(ROOT / 'evidence/source_seal.json', [{'path':str(f), 'sha256':sha(f)} for f in paths])
    write_json(ROOT / 'evidence/preparation.json', {'model':MODEL,'requests':4000,'pilot':40,'scenarios':50,'blocks':500,
                'balance':{'/'.join(k):v for k,v in sorted(balance.items())}, 'scientific_content_changes':0})
    print('Prepared 4000 main requests + 40 non-experimental fixtures; no network.')


if __name__ == '__main__':
    main()
