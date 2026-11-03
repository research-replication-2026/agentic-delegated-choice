#!/usr/bin/env python3
"""Portable offline analysis of archived output projections. Input instructions withheld.
Only results/reproduced is written. Original frozen scorer, infer and NLP rules
are imported unchanged; local absolute paths and provider accounts are unnecessary.
"""
import argparse,ast,csv,gzip,hashlib,io,json,re,socket,sys,warnings
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from scipy.stats import t

P=Path(__file__).resolve().parents[1];OUT=P/'results/reproduced'
sys.dont_write_bytecode=True
sys.path.insert(0,str(P/'analysis/frozen_gpt'))
import analyze_responses as frozen
from robust_inference import infer
sys.path.insert(0,str(P/'disclosure_validation/rules'))
import rules_v2 as rules
ST=['OUI','NON','INCERTAIN','NON_OBSERVABLE'];FIELDS=['short_rationale','commercial_disclosure_text']
ARMS=frozen.ARMS;LEVELS=frozen.LEVELS
def data(rel):
    p=P/rel;b=p.read_bytes();return gzip.decompress(b) if p.suffix=='.gz' else b
def js(rel):return json.loads(data(rel))
def jl(rel):return [json.loads(x) for x in data(rel).decode().splitlines() if x.strip()]
def rd(rel):return list(csv.DictReader(io.StringIO(data(rel).decode('utf-8-sig'))))
def save(name,x):(OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def cs(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def close(a,b,atol=1e-12):assert np.allclose(a,b,atol=atol,rtol=1e-10,equal_nan=True),(a,b)
def check_manifest():
    path=P/'provenance/RELEASE_SHA256.json'
    if path.exists():
        for p,h in js('provenance/RELEASE_SHA256.json').items():assert hashlib.sha256((P/p).read_bytes()).hexdigest()==h,p
    for row in rd('provenance/source_to_release_manifest.csv'):
        assert hashlib.sha256((P/row['path']).read_bytes()).hexdigest()==row['published_sha256']
        if row['transformation'] in ['byte_identical','gzip_lossless']:
            assert hashlib.sha256(data(row['path'])).hexdigest()==row['source_sha256']

def kappa(rows):
    n=len(rows);agree=sum(r['A']==r['B'] for r in rows);a=Counter(r['A'] for r in rows);b=Counter(r['B'] for r in rows)
    pe=Fraction(sum(a[s]*b[s] for s in ST),n*n);po=Fraction(agree,n)
    return dict(n=n,agreements=agree,disagreements=n-agree,exact_agreement_pct=float(100*po),
        expected_agreement=float(pe),cohen_kappa=float((po-pe)/(1-pe)) if pe!=1 else None)

def main():
    OUT.mkdir(parents=True,exist_ok=True);check_manifest()
    freeze=js('disclosure_validation/RULES_FINAL_FREEZE.json')
    assert hashlib.sha256((P/'disclosure_validation/rules/rules_v2.py').read_bytes()).hexdigest()==freeze['rule_sha256']
    assert hashlib.sha256((P/'disclosure_validation/rules/rules_previous.py').read_bytes()).hexdigest()==freeze['adapter_sha256']
    scenarios={s['scenario_id']:s for s in js('data/scenarios.json')['scenarios']};sids=sorted(scenarios)
    assert len(scenarios)==50
    tree=ast.parse((P/'analysis/frozen_scenario/common.py').read_text())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['score_option','violates_hard_constraints']]
    ns={'Any':object};exec(compile(ast.Module(body=nodes,type_ignores=[]),'original_pure_utility_functions','exec'),ns)
    for s in scenarios.values():assert {o['option_id']:ns['score_option'](o,s['weights'],s['hard_constraints']) for o in s['options']}==s['objective_utilities']
    keys={r['custom_id']:r for r in jl('data/assignments_gpt.jsonl.gz')}
    mp={r['record_id']:r for r in js('data/assignments_claude.json.gz')}
    expected={(r['campaign'],r['response_id']):r for r in rd('data/processed/NLP_8000_expected.csv.gz')}
    records=[];nlprows=[];nlpmatches=0;settings=defaultdict(Counter)
    for campaign,prefix in [('GPT_nouveau','gpt'),('Claude','claude')]:
        for batch in range(1,5):
            raw=jl(f'data/raw/{prefix}_batch_{batch:02d}.jsonl.gz')
            assert len(raw)==1000
            schema=js('data/decision_schema.json')
            setting=js('data/protocol_settings.json')[campaign]
            for x in raw:
                rid=x['custom_id'];key=keys[rid if prefix=='gpt' else mp[rid]['custom_id']];s=scenarios[key['scenario_id']]
                assert key['batch_index']==batch
                settings[campaign][json.dumps(setting,sort_keys=True)]+=1
                if prefix=='gpt':
                    msg=x['response']['body'];d=json.loads(next(z['arguments'] for z in msg['output'] if z['type']=='function_call'))
                    adapted=x
                else:
                    msg=x['result']['message'];d=next(z['input'] for z in msg['content'] if z['type']=='tool_use')
                    adapted={'response':{'status_code':200,'body':{'status':'completed' if msg['stop_reason']=='tool_use' else 'incomplete',
                        'output':[{'type':'function_call','name':'submit_agentic_decision','arguments':json.dumps(d)}],
                        'model':msg['model'],'usage':msg['usage']}}}
                rec=frozen.score_record(adapted,key,{'body':{'tools':[{'parameters':schema}]}},s)
                canon=rec['selected_canonical'];u=s['objective_utilities'];ustar=u[s['optimal_option_id']]
                row=dict(campaign=campaign,response_id=rid,scenario_id=key['scenario_id'],policy=key['arm'],level=key['level'],repetition=key['repetition'],
                    domain=s['domain'],batch=key['batch_index'],partner_position=key['partner_position'],commission_rate=s['commission_rate'],utility_gap=s['utility_gap'],
                    selected_option_id=d.get('selected_option_id'),selected_canonical=canon,selection_known=rec['selection_readable'],partner_selected=rec['partner_selected'],optimal_selected=rec['optimal_selected'],
                    utility_regret=ustar-u[canon] if canon else None,normalized_regret=rec['normalized_regret'],hard_violation=rec['hard_constraint_violation'],
                    schema_valid=rec['schema_valid'],fully_conformant=rec.get('fully_conformant',0),completed=rec['response_completed'],
                    manipulation_valid=rec['manipulation_valid'],truncated=not bool(rec['response_completed']),
                    disclosure_boolean=d.get('commercial_relationship_disclosed') if type(d.get('commercial_relationship_disclosed')) is bool else None)
                row.update(partner_regret_contribution=row['normalized_regret']*row['partner_selected'] if canon else None,
                    other_regret_contribution=row['normalized_regret']*(1-row['partner_selected']) if canon else None)
                records.append(row);old=expected[campaign,rid];pp=[]
                for field in FIELDS:
                    assert (d.get(field) or '')==old[field]
                    pred=rules.classify(d.get(field),d.get('selected_option_id') if canon else None,key['visible_partner_option_id'],key['visible_to_canonical']);pp.append(pred)
                    for m in 'LABC':
                        assert pred[m]==old[field+'_'+m];nlpmatches+=1
                        nlprows.append(dict(campaign=campaign,policy=key['arm'],response_id=rid,field=field,indicator=m,label=pred[m]))
                for m in 'LABC':
                    val=rules.union(pp,m)
                    if m=='B' and canon:
                        pos={v for p in pp for e in p['events'] for v in e['affirmed_options']};neg={v for p in pp for e in p['events'] for v in e['negated_options']}
                        if d['selected_option_id'] in pos&neg:val='INCERTAIN'
                    if m=='C' and any(e['platform_recipient_affirmed'] for p in pp for e in p['events']) and any(e['platform_remuneration_denied'] for p in pp for e in p['events']):val='INCERTAIN'
                    assert val==old['union_'+m];nlpmatches+=1
                    nlprows.append(dict(campaign=campaign,policy=key['arm'],response_id=rid,field='union',indicator=m,label=val))
    assert len(records)==len({(r['campaign'],r['response_id']) for r in records})==8000
    assert sum(r['selection_known'] for r in records)==7995
    # Verify assignment balance; executed input messages are not distributed.
    blocks=defaultdict(set)
    for r in records:blocks[r['campaign'],r['scenario_id'],r['repetition'],r['level']].add(r['policy'])
    assert len(blocks)==2000 and all(v==set(ARMS) for v in blocks.values())
    save('request_settings.json',{c:[dict(settings=json.loads(k),n=v) for k,v in ctr.items()] for c,ctr in settings.items()})
    # Existing scores are validation targets, never inputs to the scoring calculation.
    df=pd.DataFrame(records);old=rd('results/reference/scored_8000.csv.gz');idx={(r['campaign'],r['response_id']):r for r in records}
    for r in old:
        a=idx[r['campaign'],r['response_id']]
        for m in ['partner_selected','optimal_selected','utility_regret','normalized_regret','hard_violation']:
            assert (a[m] is None and not r[m]) or (a[m] is not None and abs(a[m]-float(r[m]))<1e-12)
    cs('scored_8000.csv',records)
    print('PASS raw scoring and 96,000 frozen NLP labels',flush=True)
    ys={};primary={};cross=[];rates=[];quality=[];strict={}
    for campaign,label in [('GPT_nouveau','GPT'),('Claude','Claude')]:
        y=np.full((50,10,4,2),np.nan);conform=y.copy()
        rr=[r for r in records if r['campaign']==campaign]
        for r in rr:
            loc=(sids.index(r['scenario_id']),r['repetition']-1,ARMS.index(r['policy']),LEVELS.index(r['level']))
            if r['selection_known']:y[loc]=r['partner_selected']
            if r['fully_conformant']:conform[loc]=r['partner_selected']
        ys[label]=y;primary[label]=frozen.contrast_analysis(y);strict[label]=frozen.contrast_analysis(conform)
        ref=js('results/reference/primary_contrasts.json')[label]
        for a,b in zip(primary[label],ref):
            for key in ['estimate','p_raw','p_holm','ci95','ci9875_bonferroni','assigned_difference_bounds','bounds_outer_bootstrap95']:
                if key in b:
                    if b[key] is None:assert a[key] is None
                    else:close(a[key],b[key])
        for arm in ARMS:
            sub=[r for r in rr if r['policy']==arm];known=[r for r in sub if r['selection_known']]
            hits=sum(r['partner_selected'] for r in known)
            rates.append(dict(model=label,policy=arm,assigned=len(sub),recognized=len(known),partner=hits,unknown=len(sub)-len(known),rate_pct=100*hits/len(known)))
            quality.append(dict(model=label,policy=arm,recognized=len(known),optimal_pct=100*np.mean([r['optimal_selected'] for r in known]),
                normalized_regret_pct=100*np.mean([r['normalized_regret'] for r in known]),hard_violations=sum(r['hard_violation'] for r in known),
                schema_valid=sum(r['schema_valid'] for r in sub),fully_conformant=sum(r['fully_conformant'] for r in sub),
                completed=sum(r['completed'] for r in sub),disclosure_boolean_true=sum(r['disclosure_boolean'] is True for r in sub),
                disclosure_boolean_missing=sum(r['disclosure_boolean'] is None for r in sub)))
    for a,b in frozen.CONTRASTS:
        vg=ys['GPT'][:,:,ARMS.index(a),:]-ys['GPT'][:,:,ARMS.index(b),:]
        vc=ys['Claude'][:,:,ARMS.index(a),:]-ys['Claude'][:,:,ARMS.index(b),:]
        missing=int(np.isnan(vc).sum());z=infer(np.nanmean(vc,axis=(1,2))-vg.mean(axis=(1,2)))
        z.update(contrast=a+'-'+b,missing_pairs=missing,full_assignment_p=None if missing else z['p_primary']);cross.append(z)
    fulladj=frozen.holm([r['full_assignment_p'] if r['full_assignment_p'] is not None else 1 for r in cross])
    availadj=frozen.holm([r['p_primary'] for r in cross])
    for r,p,av,old in zip(cross,fulladj,availadj,js('results/reference/cross_model_secondary.json')):
        r['full_assignment_holm_p']=float(p) if r['full_assignment_p'] is not None else None
        r['available_pair_secondary_holm_p']=float(av)
        for m in ['estimate','ci95','p_primary','available_pair_secondary_holm_p']:close(r[m],old[m])
        assert r['full_assignment_holm_p']==old['full_assignment_holm_p']
    save('primary_contrasts.json',primary);save('cross_implementation.json',cross);save('conformity_sensitivity.json',strict)
    cs('partner_rates.csv',rates);cs('quality_and_conformity.csv',quality)
    quality_reference=js('results/reference/quality_and_usage.json')
    for model in ['GPT','Claude']:
        rr=[r for r in quality if r['model']==model]
        for actual,archived in [('recognized','selection_readable'),('schema_valid','schema_valid'),('fully_conformant','fully_conformant_frozen_definition'),('completed','completed')]:
            assert sum(r[actual] for r in rr)==quality_reference[model][archived]
    print('PASS original primary contrasts, CI envelopes, Holm and cross-implementation comparisons',flush=True)
    # All 144 archived revised-campaign economic comparisons, including missing-data bounds and scale convention.
    economic=[];economic_ref=rd('results/reference/economic_family_144.csv');cache={}
    def matrix(c,p,level,m):
        token=(c,p,level,m)
        if token in cache:return cache[token]
        a=np.full((50,10,2 if level=='ALL' else 1),np.nan)
        for r in records:
            if r['campaign']==c and r['policy']==p and (level=='ALL' or r['level']==level):
                a[sids.index(r['scenario_id']),r['repetition']-1,LEVELS.index(r['level']) if level=='ALL' else 0]=r[m] if r[m] is not None else np.nan
        cache[token]=a;return a
    for old in economic_ref:
        c=old['campaign'];a,b=old['contrast'].split('-');level=old['level'];m=old['metric']
        x=matrix(c,a,level,m);y=matrix(c,b,level,m);d=np.nanmean(x-y,axis=(1,2));missing=int(np.isnan(x).sum()+np.isnan(y).sum())
        close(float(d.mean()),float(old['estimate']));z={}
        if not missing and d.std(ddof=1)>1e-13:
            scale=max(max(s['objective_utilities'].values()) for s in scenarios.values()) if m=='utility_regret' else 1
            z=infer(d/scale);close(z['p_primary'],float(old['p_raw']));close(np.array(z['ci95'])*scale,[float(old['ci_low']),float(old['ci_high'])])
            z=dict(p_raw=z['p_primary'],ci_low=z['ci95'][0]*scale,ci_high=z['ci95'][1]*scale)
        else:assert not old['p_raw'];z=dict(p_raw=None,ci_low=None,ci_high=None)
        economic.append(dict(campaign=c,contrast=old['contrast'],level=level,metric=m,missing=missing,estimate=float(d.mean()),**z))
    adj=frozen.holm([r['p_raw'] if r['p_raw'] is not None else 1 for r in economic])
    for r,p,old in zip(economic,adj,economic_ref):
        r['p_holm']=float(p) if r['p_raw'] is not None else None
        if r['p_holm'] is not None:close(r['p_holm'],float(old['p_holm']))
    cs('economic_family_144.csv',economic)
    counts=Counter((r['campaign'],r['policy'],r['field'],r['indicator'],r['label']) for r in nlprows)
    nlp_summary=[dict(campaign=c,policy=a,field=f,indicator=m,**{s:counts[c,a,f,m,s] for s in ST}) for c in ['GPT_nouveau','Claude'] for a in ARMS for f in FIELDS+['union'] for m in 'LABC']
    cs('NLP_complete_8000.csv',nlp_summary)
    nlp_index={(r['campaign'],r['policy'],r['field'],r['indicator']):r for r in nlp_summary}
    for old in rd('results/reference/NLP_complete_8000.csv'):
        actual=nlp_index[old['campaign'],old['policy'],old['field'],old['indicator']]
        assert sum(actual[s] for s in ST)==int(old['N'])==1000
        for s in ST:assert actual[s]==int(old[s])
    # Existing human labels are read, never generated or harmonized.
    labelmaps={}
    for who in ['A','B','final']:
        labelmaps[who]={(r['campaign'],r['response_id'],r['field'],r['indicator']):r['label'] for r in rd('disclosure_validation/coder_'+who+'.csv')}
        assert len(labelmaps[who])==400 and set(labelmaps[who].values())<=set(ST)
    assert set(labelmaps['A'])==set(labelmaps['B'])==set(labelmaps['final'])
    context={(r['campaign'],r['response_id']):r for r in js('disclosure_validation/control_contexts_50.json.gz')}
    control=[]
    for key,av in labelmaps['A'].items():
        c,rid,field,m=key;ct=context[c,rid];pred=rules.classify(ct[field],ct['selected_option_id'],ct['commercial_partner_id'],ct['catalog'])
        assert pred[m]==ct['expected_NLP'][field+'_'+m]
        bv=labelmaps['B'][key];fv=labelmaps['final'][key];assert fv in [av,bv]
        control.append(dict(campaign=c,response_id=rid,field=field,indicator=m,A=av,B=bv,final=fv,NLP=pred[m],final_label_origin='BOTH' if av==bv else 'A' if fv==av else 'B'))
    ks=kappa(control);assert ks['agreements']==392 and abs(ks['cohen_kappa']-0.9647840824052472)<1e-14
    assert sum(r['final']==r['NLP'] for r in control)==388
    cs('coding_chain_400.csv',control);cs('initial_disagreements.csv',[r for r in control if r['A']!=r['B']]);cs('final_NLP_disagreements.csv',[r for r in control if r['final']!=r['NLP']])
    save('coding_statistics.json',dict(initial=ks,final_NLP_agreements=388,final_NLP_disagreements=12,final_NLP_disagreement_responses=len({(r['campaign'],r['response_id']) for r in control if r['final']!=r['NLP']})))
    # Explicit confrontation with every numeric row of Tables 2, 3 and 4 in the final manuscript.
    tables=js('results/reference/manuscript_numeric_tables.json');checks=[]
    def number(s):return float(s.replace('−','-').replace(',','').replace('*',''))
    for row in tables['2'][1:]:
        model,policy,ratio,unknown,pct=row;arm=policy[0];r=next(x for x in rates if x['model']==model and x['policy']==arm)
        num,den=[int(x.strip().replace(',','')) for x in ratio.split('/')];assert (num,den,int(unknown))==(r['partner'],r['recognized'],r['unknown']);assert abs(number(pct)-r['rate_pct'])<=.00501
        checks.append(dict(table=2,model=model,cell=arm,status='PASS'))
    for row in tables['3'][1:]:
        model,contrast,effect,ci,p=row;contrast=contrast.replace('−','-');r=next(x for x in primary[model] if x['contrast']==contrast)
        value=r['estimate'] if r['estimate'] is not None else r['descriptive_available_pair_scenario_average']
        assert abs(number(effect)-100*value)<=.00501
        if r['estimate'] is not None:
            printed=[number(x) for x in ci.strip('[]').split(',')];assert np.max(abs(np.array(printed)-100*np.array(r['ci95'])))<=.00501
            if p.startswith('<'):assert r['p_holm']<number(p[1:].strip())
            else:assert abs(number(p)-r['p_holm'])<=.000501
        else:assert ci=='Not estimated' and p=='NE'
        checks.append(dict(table=3,model=model,cell=contrast,status='PASS'))
    for row in tables['4'][1:]:
        model,arm,opt,regret=row;r=next(x for x in quality if x['model']==model and x['policy']==arm)
        assert abs(number(opt)-r['optimal_pct'])<=.00501 and abs(number(regret)-r['normalized_regret_pct'])<=.0000501
        checks.append(dict(table=4,model=model,cell=arm,status='PASS'))
    cs('manuscript_table_checks.csv',checks)
    save('VERIFICATION.json',dict(status='PASS',raw_responses=8000,recognized_selections=7995,unknown_selections=5,
        scenarios=50,assigned_policy_blocks=2000,executed_input_messages_distributed=False,
        frozen_NLP_label_comparisons=nlpmatches,economic_comparisons=144,manuscript_numeric_table_rows_checked=len(checks),
        initial_agreement=ks,final_NLP_agreements=388,model_API_calls=0,network_calls=0,
        scope='Analysis from archived output projections, assignments and structural schema. Input instructions are withheld; complete input-to-output replication is therefore not available in this distribution.'))
    check_manifest();print('PASS: 8000 raw responses, 7995 recognized, 24 manuscript table rows, 144 economic contrasts, 392/400 initial coding and 388/400 final/NLP.',flush=True)

if __name__=='__main__':
    with patch('socket.socket',side_effect=RuntimeError('Network prohibited during offline replication')):
        with warnings.catch_warnings():warnings.simplefilter('ignore',RuntimeWarning);main()
