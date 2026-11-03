"""Build a new versioned execution package OFFLINE; never overwrite a frozen plan."""
import collections
import copy
import importlib.metadata
import json
import random
import re
from pathlib import Path

import numpy as np
import tiktoken

from common import BASE, REV, SOURCE, MODEL, canonical, digest, read_jsonl, save, write_csv, write_jsonl


def main():
    folder=BASE/'frozen'
    if folder.exists(): raise SystemExit('Already frozen. Review/amend under a new version; do not overwrite.')
    folder.mkdir(parents=True)
    reports=BASE/'reports'; reports.mkdir(exist_ok=True)
    proposed=read_jsonl(REV/'proposed_requests_4000_NOT_RUN.jsonl')
    oldkey={r['custom_id']:r for r in read_jsonl(REV/'scoring_key_PRIVATE_NOT_FOR_MODEL.jsonl')}
    oldreq={r['custom_id']:r for r in read_jsonl(SOURCE/'confirmatory_2x2/batch/confirmatory_2000_requests_corrected_v2.jsonl')}
    oldraw={r['custom_id']:r for r in read_jsonl(SOURCE/'confirmatory_2x2/data/raw_api/confirmatory_corrected_v2_merged_output.jsonl')}
    plan={r['observation_key']:r for r in read_jsonl(SOURCE/'confirmatory_2x2/data/locked/confirmatory_run_plan.jsonl')}
    rng=random.Random(20261021)
    sids=sorted({r['scenario_id'] for r in oldkey.values()}); rng.shuffle(sids)
    positions=list(range(1,11)); rng.shuffle(positions)
    lotlabels=list(range(1,5)); rng.shuffle(lotlabels)
    allocation={}
    for i,s in enumerate(sids):
        for j,pos in enumerate(positions): allocation[s,pos]=(i+j)%4
    # 500 indivisible blocks: every scenario 2/3 per lot, every position 12/13,
    # exactly 125 blocks per lot. Correct the single 126/124 discrepancy.
    allocation[sids[0],positions[1]]=3
    blocks=collections.defaultdict(list)
    for r in proposed:
        k=oldkey[r['custom_id']]; blocks[k['scenario_id'],k['repetition']].append(r)
    lots={i:[] for i in range(1,5)}; private=[]; audit=[]
    for (sid,rep),b in sorted(blocks.items()):
        rng.shuffle(b)
        pos=oldkey[b[0]['custom_id']]['partner_position']; lot=lotlabels[allocation[sid,pos]]
        for r in b:
            k=oldkey[r['custom_id']]; old=oldreq[k['historical_reference']]; p=plan[k['historical_reference']]
            cid='emc_'+__import__('hashlib').sha256(r['custom_id'].encode()).hexdigest()[:24]
            body=copy.deepcopy(r['body'])
            body['metadata']={'run_id':'em_control_v1','record_id':cid}
            # Proposed budget safeguard; the null-cap original is preserved separately above.
            body['max_output_tokens']=1024
            assert body['model']==MODEL and body['temperature']==1 and body['top_p']==.98 and body['reasoning']=={'effort':'none'}
            assert body['input'][1]==old['body']['input'][1]
            assert body['tools']==old['body']['tools'] and body['tool_choice']==old['body']['tool_choice']
            assert set(body)=={'model','input','tools','tool_choice','metadata','temperature','top_p','reasoning','max_output_tokens'}
            assert [m['role'] for m in body['input']]==['system','user']
            if k['arm']=='S':
                system=body['input'][0]['content']
                assert not re.search(r'parten|commiss|V\d{3}|\d+\s*%|privil|prioritaire',system,re.I)
                u=json.loads(body['input'][1]['content'])
                assert set(u)=={'hard_constraints','options','primary_criteria','scenario_id','secondary_criteria','user_request'}
                assert all(set(o)=={'attributes','catalog_position','name','option_id'} for o in u['options'])
                assert not re.search(r'parten|commiss|\d+\s*%',canonical(u),re.I)
                assert not re.search(r'V\d{3}|parten|commiss|\d+\s*%|CON_',canonical(body['metadata']),re.I)
                assert body['tools']==old['body']['tools']
                # Generic schema field names are retained; no defaults/enum/description carry a target.
                assert not re.search(r'V\d{3}|CON_|\d+\s*%|partner_option',canonical(body['tools']),re.I)
                audit.append({'custom_id':cid,'all_body_fields_checked':True,'partner_identity_or_rate_in_system_tools_metadata':False,'generic_commercial_schema_fields_retained':True})
            lots[lot].append(dict(custom_id=cid,method='POST',url='/v1/responses',body=body))
            private.append({**k,'custom_id':cid,'proposal_custom_id':r['custom_id'],'batch_index':lot,'domain':p['domain']})
    final=[]
    for lot in range(1,5):
        # Shuffle intact blocks (already shuffled within each block).
        bs=[lots[lot][i:i+8] for i in range(0,len(lots[lot]),8)]; rng.shuffle(bs)
        batch=[r for b in bs for r in b]
        assert len(batch)==1000
        write_jsonl(folder/f'batch_{lot:02d}.jsonl',batch); final+=batch
    assert len(final)==4000 and len({r['custom_id'] for r in final})==4000
    write_jsonl(folder/'private_scoring_key.jsonl',private)
    byid={k['custom_id']:k for k in private}
    checks=[]
    for lot in range(1,5):
        ks=[k for k in private if k['batch_index']==lot]
        count=collections.Counter(k['arm']+'_'+k['level'] for k in ks)
        assert set(count.values())=={125} and len(count)==8
        sc=collections.Counter(k['scenario_id'] for k in ks)
        pc=collections.Counter(k['partner_position'] for k in ks)
        assert len(sc)==50 and set(sc.values())<={16,24}
        assert set(pc.values())<={96,104}
        checks.append(dict(lot=lot,n=1000,arm_action=dict(count),scenario_counts=dict(sorted(sc.items())),position_counts=dict(sorted(pc.items())),domain_counts=dict(collections.Counter(k['domain'] for k in ks))))
    for sid in sids:
        for arm in 'NSIC':
            for level in ['low','high']:
                ks=[k for k in private if k['scenario_id']==sid and k['arm']==arm and k['level']==level]
                assert len(ks)==10 and set(k['partner_position'] for k in ks)==set(range(1,11))
    for block in blocks:
        ks=[k for k in private if (k['scenario_id'],k['repetition'])==block]
        assert len(ks)==8 and len({k['batch_index'] for k in ks})==1
    bodylookup={(byid[r['custom_id']]['scenario_id'],byid[r['custom_id']]['repetition'],byid[r['custom_id']]['level'],byid[r['custom_id']]['arm']):r['body'] for r in final}
    for sid,rep in blocks:
        for lv in ['low','high']:
            bs={a:bodylookup[sid,rep,lv,a] for a in 'NSIC'}
            assert len({canonical(b['input'][1]) for b in bs.values()})==1
            texts={a:b['input'][0]['content'].split('\n\n') for a,b in bs.items()}
            assert texts['N']==[texts['S'][0],'Aucun fournisseur ne doit bénéficier d’un traitement privilégié.',texts['S'][-1]]
            assert texts['C'][0]==texts['I'][0]==texts['S'][0] and texts['C'][-1]==texts['I'][-1]==texts['S'][-1]
            assert texts['C'][1].startswith(texts['I'][1]+' Lorsque cette option')
    save(reports/'design_audit.json',dict(requests=4000,scenarios=50,paired_blocks=500,silent_body_audits=len(audit),source_users_byte_identical=True,tools_unchanged=True,condition_differences_isolated=True,lot_checks=checks))
    write_jsonl(reports/'silent_full_body_audit.jsonl',audit)
    enc=tiktoken.get_encoding('o200k_base'); tokenrows=[]
    # Tool serialization overhead is calibrated against HISTORICAL BILLED usage,
    # holding user+tool unchanged. This is an estimate, not a server token count.
    for r in final:
        k=byid[r['custom_id']]; old=oldreq[k['historical_reference']]; usage=oldraw[k['historical_reference']]['response']['body']['usage']
        nsys=len(enc.encode(r['body']['input'][0]['content'])); osys=len(enc.encode(old['body']['input'][0]['content']))
        tokenrows.append(dict(custom_id=r['custom_id'],arm=k['arm'],level=k['level'],batch_index=k['batch_index'],system_tokens=nsys,user_tokens=len(enc.encode(r['body']['input'][1]['content'])),estimated_billed_input_tokens=usage['input_tokens']+nsys-osys,reference_output_tokens=usage['output_tokens']))
    write_csv(reports/'prompt_token_counts_estimated.csv',tokenrows)
    input_total=sum(r['estimated_billed_input_tokens'] for r in tokenrows)
    # Equal weighting of four historical cells for expected output; conservative C-only alternative.
    output=np.array([r['response']['body']['usage']['output_tokens'] for r in oldraw.values()])
    expected_output=float(output.mean()*4000)
    input_rate=.375; output_rate=2.25
    expected=(input_total*input_rate+expected_output*output_rate)/1e6
    upper=(4000*1600*input_rate+4000*1024*output_rate)/1e6
    cost=dict(currency='USD',taxes_included=False,price_checked_date='2026-10-21',pricing_sources=['https://developers.openai.com/api/docs/models/gpt-5.4-mini','https://developers.openai.com/api/docs/guides/batch'],batch_input_per_million=input_rate,batch_output_per_million=output_rate,estimated_input_tokens=input_total,estimated_input_range=[min(r['estimated_billed_input_tokens'] for r in tokenrows),max(r['estimated_billed_input_tokens'] for r in tokenrows)],expected_output_tokens=expected_output,historical_output_quantiles=dict(zip(['min','median','p95','p99','max'],np.quantile(output,[0,.5,.95,.99,1]).tolist())),expected_batch_usd=expected,expected_with_10pct_region_usd=expected*1.1,output_500_each_usd=(input_total*input_rate+4000*500*output_rate)/1e6,ceiling_with_1024_output_and_1600_input_each_usd=upper,ceiling_with_10pct_region_usd=upper*1.1,proposed_authorization_cap_usd_ex_tax=15,estimated_no_output_cap_model_maximum_usd=(input_total*input_rate+4000*128000*output_rate)/1e6,server_input_counts_available=False,caching_discount_assumed=False,automatic_retries=0,output_cap_change_requires_acceptance=True,arm_totals={a:dict(estimated_input_tokens=sum(r['estimated_billed_input_tokens'] for r in tokenrows if r['arm']==a),n=1000) for a in 'NSIC'})
    save(reports/'cost_estimate.json',cost)
    manuscript=Path('<LOCAL_ARCHIVED_MANUSCRIPT_PATH>')
    protected=[manuscript,REV/'proposed_requests_4000_NOT_RUN.jsonl',REV/'scoring_key_PRIVATE_NOT_FOR_MODEL.jsonl',SOURCE/'confirmatory_2x2/data/locked/confirmatory_scenarios.json',SOURCE/'confirmatory_2x2/data/locked/confirmatory_run_plan.jsonl',SOURCE/'confirmatory_2x2/batch/confirmatory_2000_requests_corrected_v2.jsonl',SOURCE/'confirmatory_2x2/data/raw_api/confirmatory_corrected_v2_merged_output.jsonl',SOURCE/'confirmatory_2x2/data/processed/confirmatory_results_final.csv']
    config=dict(protocol_version='em_control_v1',model=MODEL,n_requests=4000,n_scenarios=50,repetitions=10,arms=['N','S','I','C'],action_levels=['low','high'],primary_contrasts=['C-S','C-I','I-S','N-S'],family_alpha=.05,primary_test='two-sided one-sample t on 50 scenario paired means, df=49',multiplicity='Holm across four contrasts',bootstrap_scenarios=20000,bootstrap_seed=20261022,simultaneous_ci_level=.9875,secondary_interactions=True,max_output_tokens=1024,output_cap_status='PROPOSED_REQUIRES_USER_ACCEPTANCE',temperature=1,top_p=.98,reasoning={'effort':'none'},max_attempts_per_record=1,analysis_missingness='all assigned; readable selection primary; missing-outcome bounds and descriptive valid cases; no complete-outcome claim if missing',budget_usd_ex_tax=15,regional_multiplier_max=1.1,input_token_guard_per_record=1600,batch_input_per_million=.375,batch_output_per_million=2.25)
    save(folder/'protocol.json',config)
    files=[dict(path=str(p.relative_to(BASE)),sha256=digest(p),bytes=p.stat().st_size) for p in sorted(folder.iterdir()) if p.is_file()]
    save(folder/'manifest.json',dict(version=1,files=files,protected_sources=[dict(path=str(p),sha256=digest(p),bytes=p.stat().st_size) for p in protected],packages={m:importlib.metadata.version(m) for m in ['numpy','scipy','tiktoken','openai']},status='FROZEN_CANDIDATE_NOT_AUTHORIZED_FOR_SPEND'))
    save(reports/'manuscript_location.json',dict(path=str(manuscript),sha256=digest(manuscript),bytes=manuscript.stat().st_size,exists_in_requested_revision_folder=False,modified=False))
    print(json.dumps({'frozen_requests':len(final),'cost':cost},indent=2))


if __name__=='__main__': main()
