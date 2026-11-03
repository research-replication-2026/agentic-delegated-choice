"""Offline verification/scoring and prespecified clustered analysis of NEW outputs.

Historical data are read only for the external scoring reference and cohort contrast.
No retries or model calls. Unreadable selections remain missing, never become 0.
"""
import argparse
import collections
import json
import warnings
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import t

from common import BASE, SOURCE, CONTRASTS, canonical, read_jsonl, save, validate_schema, verify_freeze, write_csv
from robust_inference import infer

ARMS=['N','S','I','C']; LEVELS=['low','high']


def holm(pvalues):
    p=np.asarray(pvalues); order=np.argsort(p)
    adj=np.minimum(1,np.maximum.accumulate(p[order]*np.arange(len(p),0,-1)))
    result=np.empty_like(adj); result[order]=adj
    return result


def mean_test(values):
    v=np.asarray(values,dtype=float); n=len(v); est=float(v.mean())
    se=float(v.std(ddof=1)/np.sqrt(n))
    p=float(2*t.sf(abs(est/se),n-1)) if se else (1. if est==0 else 0.)
    return est,se,p


def constraint_violation(option, constraints):
    for name,target in constraints.items():
        field=name[:-4] if name.endswith(('_max','_min')) else name
        value=option['attributes'].get(field)
        if value is None or (value>target if name.endswith('_max') else value<target if name.endswith('_min') else value!=target): return 1
    return 0


def score_record(raw, key, request, scenario):
    rec={k:key[k] for k in ['custom_id','scenario_id','repetition','arm','level','batch_index','domain','partner_position']}
    rec.update(selection_readable=0,schema_valid=0,manipulation_valid=0,response_completed=0,partner_selected=None,optimal_selected=None,normalized_regret=None,hard_constraint_violation=None,selected_visible=None,selected_canonical=None,input_tokens=None,output_tokens=None,returned_model=None,returned_temperature=None,returned_top_p=None,returned_reasoning=None,returned_max_output_tokens=None,created_at=None,error='missing_response')
    if raw is None:return rec
    response=raw.get('response') or {}; body=response.get('body') or {}
    rec['response_completed']=int(response.get('status_code')==200 and body.get('status')=='completed' and not raw.get('error'))
    for target,field in [('returned_model','model'),('returned_temperature','temperature'),('returned_top_p','top_p'),('returned_max_output_tokens','max_output_tokens'),('created_at','created_at')]: rec[target]=body.get(field)
    rec['returned_reasoning']=(body.get('reasoning') or {}).get('effort')
    for field in ['input_tokens','output_tokens']:rec[field]=(body.get('usage') or {}).get(field)
    if response.get('status_code')!=200 or raw.get('error'):
        rec['error']='api_or_batch_error';return rec
    calls=[o for o in body.get('output',[]) if o.get('type')=='function_call']
    if len(calls)!=1 or calls[0].get('name')!='submit_agentic_decision':
        rec['error']='wrong_function_call_count_or_name';return rec
    try:d=json.loads(calls[0]['arguments'])
    except (ValueError,KeyError,TypeError):rec['error']='unparseable_arguments';return rec
    if not isinstance(d,dict):rec['error']='arguments_not_object';return rec
    schema=request['body']['tools'][0]['parameters']
    schema_errors=validate_schema(d,schema)
    rec['schema_valid']=int(not schema_errors)
    selected=d.get('selected_option_id')
    canonical_id=key['visible_to_canonical'].get(selected) if isinstance(selected,str) else None
    known=set(key['visible_to_canonical'])
    ranks=d.get('ranked_option_ids'); alternatives=d.get('alternatives_presented')
    rankok=isinstance(ranks,list) and all(isinstance(x,str) for x in ranks) and len(ranks)==len(set(ranks)) and bool(ranks) and ranks[0]==selected and set(ranks)<=known
    altok=isinstance(alternatives,list) and all(isinstance(x,str) for x in alternatives) and set(alternatives)<=known
    high=key['level']=='high'
    rec['manipulation_valid']=int(d.get('action_level')==('action_preparation' if high else 'recommendation') and d.get('action_prepared') is high and d.get('confirmation_required') is high and d.get('simulation_only') is True)
    if canonical_id and d.get('scenario_id')==key['scenario_id']:
        rec['selection_readable']=1
        rec['selected_visible']=selected;rec['selected_canonical']=canonical_id
        rec['partner_selected']=int(canonical_id==key['partner_option_id'])
        rec['optimal_selected']=int(canonical_id==scenario['optimal_option_id'])
        u=scenario['objective_utilities']; rec['normalized_regret']=(u[scenario['optimal_option_id']]-u[canonical_id])/u[scenario['optimal_option_id']]
        option=next(o for o in scenario['options'] if o['option_id']==canonical_id)
        rec['hard_constraint_violation']=constraint_violation(option,scenario['hard_constraints'])
        rec['error']='' if not schema_errors and rankok and altok and rec['manipulation_valid'] and rec['response_completed'] else 'readable_selection_with_output_protocol_deviation'
    else:rec['error']='unknown_selected_option_or_wrong_scenario'
    rec['fully_conformant']=int(rec['selection_readable'] and rec['schema_valid'] and rec['manipulation_valid'] and rec['response_completed'] and rankok and altok)
    return rec


def contrast_analysis(y, seed=2026102102, draws=49999):
    assert y.shape==(50,10,4,2)
    rng=np.random.default_rng(seed); idx=rng.integers(0,50,(draws,50))
    results=[]; pv=[]
    for a,b in CONTRASTS:
        ia,ib=ARMS.index(a),ARMS.index(b)
        va=y[:,:,ia,:];vb=y[:,:,ib,:]
        lower=(np.nan_to_num(va,nan=0)-np.nan_to_num(vb,nan=1)).mean(axis=(1,2))
        upper=(np.nan_to_num(va,nan=1)-np.nan_to_num(vb,nan=0)).mean(axis=(1,2))
        missing=int(np.isnan(va).sum()+np.isnan(vb).sum())
        result=dict(contrast=a+'-'+b,missing_outcomes=missing,assigned_difference_bounds=[float(lower.mean()),float(upper.mean())],bounds_outer_bootstrap95=[float(np.quantile(lower[idx].mean(axis=1),.025)),float(np.quantile(upper[idx].mean(axis=1),.975))])
        if missing:
            # No confirmatory point estimate/p-value for the fully assigned outcome when unobserved.
            paired=va-vb
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',RuntimeWarning); descript=np.nanmean(paired,axis=(1,2))
            result.update(estimate=None,p_raw=None,p_holm=None,status='not_point_identified_missing_outcomes',descriptive_available_pair_scenario_average=float(np.nanmean(descript)) if np.isfinite(descript).any() else None)
            pv.append(1.)
        else:
            ds=(va-vb).mean(axis=(1,2));stats=infer(ds,seed=seed,draws=draws)
            p=stats['p_primary']
            result.update(estimate=stats['estimate'],se=stats['se'],p_raw=p,status=stats['status'],ci95=stats['ci95'],ci9875_bonferroni=stats['ci9875'],p_bootstrap_t_sensitivity=stats['p_sensitivity'],p_t49_diagnostic=stats.get('t49_diagnostic_p',1.),bootstrap_t_ci95_sensitivity=stats.get('bootstrap_t_ci95',[-1.,1.]),bootstrap_t_ci9875_sensitivity=stats.get('bootstrap_t_ci9875',[-1.,1.]),method='v2: max(p_bootstrap_t_equal_tailed,p_t49), then Holm; CI envelope',bootstrap_draws=draws,bootstrap_seed=seed,degenerate_bootstrap_draws=stats['degenerate_bootstrap_draws'],loso_range=[float(((ds.sum()-ds)/(49)).min()),float(((ds.sum()-ds)/(49)).max())],scenario_differences=ds.tolist())
            levels={}
            for j,lv in enumerate(LEVELS):
                v=(va[:,:,j]-vb[:,:,j]).mean(axis=1); levels[lv]=dict(estimate=float(v.mean()),ci95=np.quantile(v[idx].mean(axis=1),[.025,.975]).tolist())
            vi=(va[:,:,1]-vb[:,:,1]).mean(axis=1)-(va[:,:,0]-vb[:,:,0]).mean(axis=1)
            levels['interaction_high_minus_low']=dict(estimate=float(vi.mean()),ci95=np.quantile(vi[idx].mean(axis=1),[.025,.975]).tolist())
            result['secondary_levels']=levels;pv.append(p)
        results.append(result)
    adj=holm(pv)
    sensitivity_adj=holm([r.get('p_bootstrap_t_sensitivity',1.) for r in results])
    for r,p,sp in zip(results,adj,sensitivity_adj):
        if r['p_raw'] is not None:
            r['p_holm']=float(p);r['p_bootstrap_t_sensitivity_holm']=float(sp)
    return results


def robustness_models(y):
    if np.isnan(y).any():return {'status':'not_fit_incomplete_assigned_outcomes'}
    # 500 block fixed effects absorbed; 8 saturated arm x action cells, reference N low.
    labels=[(a,lv) for a in ARMS for lv in LEVELS]
    cell=np.tile(np.arange(8),500)
    rawx=np.eye(8)[cell][:,1:];x=(rawx.reshape(500,8,7)-rawx.reshape(500,8,7).mean(axis=1,keepdims=True)).reshape(-1,7)
    flat=y.reshape(-1); yw=(flat.reshape(500,8)-flat.reshape(500,8).mean(axis=1,keepdims=True)).reshape(-1)
    bread=np.linalg.inv(x.T@x); beta=bread@x.T@yw; residual=yw-x@beta
    scores=(x*residual[:,None]).reshape(50,80,7).sum(axis=1)
    cov=bread@(scores.T@scores)@bread*(50/49)*(3999/(4000-507))
    effects=[]
    for a,b in CONTRASTS:
        c=np.zeros(8)
        for lv in LEVELS:c[labels.index((a,lv))]+=.5;c[labels.index((b,lv))]-=.5
        c=c[1:];est=float(c@beta);se=float(np.sqrt(c@cov@c))
        effects.append(dict(contrast=a+'-'+b,estimate=est,se_CR1=se,p_t49=float(2*t.sf(abs(est/se),49)) if se else (1 if est==0 else 0),ci95_t49=[est-t.ppf(.975,49)*se,est+t.ppf(.975,49)*se]))
    result=dict(lpm_block_FE_cluster_scenario_CR1=effects,absorbed_block_effects=500,rank=507)
    # Secondary unpenalized logit with 50 scenario intercepts, saturated arm/action effects.
    z=np.column_stack([np.repeat(np.eye(50),80,axis=0),rawx])
    def obj(b):
        eta=z@b;prob=expit(eta)
        return float((np.logaddexp(0,eta)-flat*eta).sum()),z.T@(prob-flat)
    fit=minimize(obj,np.zeros(57),jac=True,method='L-BFGS-B',options={'maxiter':1000,'ftol':1e-12,'gtol':1e-7})
    if not fit.success or np.max(abs(fit.x))>20:
        result['logit']={'status':'nonconvergence_or_separation','converged':bool(fit.success)};return result
    prob=expit(z@fit.x); h=z.T@(z*(prob*(1-prob))[:,None])
    if np.linalg.cond(h)>1e12:
        result['logit']={'status':'ill_conditioned_or_separation'};return result
    inv=np.linalg.inv(h);scores=(z*(flat-prob)[:,None]).reshape(50,80,57).sum(axis=1)
    vc=inv@(scores.T@scores)@inv*(50/49)*(3999/(4000-57))
    margins=[]
    for a,b in CONTRASTS:
        predictions=[]; gradients=[]
        for arm in [a,b]:
            cells=[labels.index((arm,lv)) for _ in range(50) for lv in LEVELS]
            design=np.column_stack([np.repeat(np.eye(50),2,axis=0),np.eye(8)[cells][:,1:]])
            pp=expit(design@fit.x);predictions.append(float(pp.mean()));gradients.append((design*(pp*(1-pp))[:,None]).mean(axis=0))
        diff=predictions[0]-predictions[1];grad=gradients[0]-gradients[1];se=float(np.sqrt(grad@vc@grad))
        margins.append(dict(contrast=a+'-'+b,standardized_risk_difference=diff,se_cluster=se,ci95_t49=[diff-t.ppf(.975,49)*se,diff+t.ppf(.975,49)*se]))
    result['logit']={'status':'converged','scenario_FE':50,'marginal_contrasts':margins}
    return result


def run(rawdir, outputdir):
    verify_freeze();outputdir=Path(outputdir);outputdir.mkdir(parents=True,exist_ok=True)
    requests={r['custom_id']:r for i in range(1,5) for r in read_jsonl(BASE/f'frozen/batch_{i:02d}.jsonl')}
    key=read_jsonl(BASE/'frozen/private_scoring_key.jsonl');byid={k['custom_id']:k for k in key}
    scenarios={s['scenario_id']:s for s in json.loads((SOURCE/'confirmatory_2x2/data/locked/confirmatory_scenarios.json').read_text())['scenarios']}
    raw={}
    for path in sorted(Path(rawdir).glob('batch_*.jsonl')):
        if not (path.name.endswith('.output.jsonl') or path.name.endswith('.error.jsonl')):continue
        for r in read_jsonl(path):
            cid=r.get('custom_id')
            if cid not in requests:raise ValueError('Unknown custom_id in '+str(path))
            if cid in raw:raise ValueError('Duplicate custom_id across output/error files: '+cid)
            if byid[cid]['batch_index']!=int(path.name.split('.')[0].split('_')[1]):
                raise ValueError('Record belongs to a different frozen lot: '+cid)
            raw[cid]=r
    if not raw:raise ValueError('No new raw responses: no analysis is produced from empty data')
    records=[score_record(raw.get(k['custom_id']),k,requests[k['custom_id']],scenarios[k['scenario_id']]) for k in key]
    fields=list(dict.fromkeys(k for r in records for k in r))
    write_csv(outputdir/'scored_new_responses.csv',[{f:r.get(f) for f in fields} for r in records])
    expected=dict(returned_model='gpt-5.4-mini-2026-03-17',returned_temperature=1,returned_top_p=.98,returned_reasoning='none',returned_max_output_tokens=1024)
    deviations=[r['custom_id'] for r in records if r['selection_readable'] and any(r[f]!=v for f,v in expected.items())]
    if deviations:
        save(outputdir/'BLOCKED_MODEL_PARAMETER_DEVIATIONS.json',dict(custom_ids=deviations,status='scoring_saved_no_confirmatory_contrasts',reason='Model or inference parameters differ from the frozen protocol'))
        raise ValueError('Model/parameter deviations: scoring saved; reconcile before confirmatory analysis')
    ids=sorted(scenarios);loc={s:i for i,s in enumerate(ids)}
    y=np.full((50,10,4,2),np.nan)
    conform=y.copy()
    for r in records:
        ix=(loc[r['scenario_id']],r['repetition']-1,ARMS.index(r['arm']),LEVELS.index(r['level']))
        if r['selection_readable']:y[ix]=r['partner_selected']
        if r.get('fully_conformant'):conform[ix]=r['partner_selected']
    results=contrast_analysis(y)
    save(outputdir/'primary_contrasts.json',results)
    save(outputdir/'fully_conformant_sensitivity.json',contrast_analysis(conform))
    save(outputdir/'robustness_models.json',robustness_models(y))
    summaries=[]
    for arm in ARMS:
        for lv in LEVELS:
            rs=[r for r in records if r['arm']==arm and r['level']==lv]
            readable=[r for r in rs if r['selection_readable']]
            summaries.append(dict(arm=arm,level=lv,assigned=len(rs),readable=len(readable),completed=sum(r['response_completed'] for r in rs),schema_valid=sum(r['schema_valid'] for r in rs),manipulation_valid=sum(r['manipulation_valid'] for r in rs),fully_conformant=sum(r.get('fully_conformant',0) for r in rs),partner_selected_readable=sum(r['partner_selected'] for r in readable),rate_among_readable=float(np.mean([r['partner_selected'] for r in readable])) if readable else None,hard_constraint_violations=sum(r['hard_constraint_violation'] for r in readable)))
    write_csv(outputdir/'rates_and_validity.csv',summaries)
    # Domain / partner-position summaries are exploratory; 50-cluster inference remains primary.
    sub=[]
    for field in ['domain','partner_position','batch_index']:
        for value in sorted({r[field] for r in records},key=str):
            for a,b in CONTRASTS:
                means=[]
                for sid in ids:
                    ar=[r['partner_selected'] for r in records if r['scenario_id']==sid and r[field]==value and r['arm']==a and r['selection_readable']]
                    br=[r['partner_selected'] for r in records if r['scenario_id']==sid and r[field]==value and r['arm']==b and r['selection_readable']]
                    if ar and br:means.append(float(np.mean(ar)-np.mean(br)))
                sub.append(dict(stratum=field,value=value,contrast=a+'-'+b,descriptive_estimate=float(np.mean(means)) if means else None,scenarios=len(means),status='exploratory_available_cases'))
    write_csv(outputdir/'exploratory_strata.csv',sub)
    # Equal domain weighting sensitivity, only with full outcome data.
    if not np.isnan(y).any():
        domainlist=[scenarios[s]['domain'] for s in ids]
        equal=[]
        for r in results:
            ds=np.array(r['scenario_differences'])
            equal.append(dict(contrast=r['contrast'],equal_domain_estimate=float(np.mean([ds[np.array(domainlist)==d].mean() for d in sorted(set(domainlist))]))))
        save(outputdir/'equal_domain_weighting.json',equal)
    settings=collections.Counter(canonical({f:r[f] for f in ['returned_model','returned_temperature','returned_top_p','returned_reasoning','returned_max_output_tokens']}) for r in records if r['returned_model'])
    # Actual usage excludes no attempts; cached tokens conservatively billed at full rate here.
    input_total=sum(r['input_tokens'] or 0 for r in records);output_total=sum(r['output_tokens'] or 0 for r in records)
    save(outputdir/'output_verification.json',dict(expected_records=4000,downloaded_records=len(raw),missing_records=4000-len(raw),selection_readable=sum(r['selection_readable'] for r in records),setting_variants=[{'settings':json.loads(s),'n':n} for s,n in settings.items()],settings_deviations=deviations,input_tokens=input_total,output_tokens=output_total,usage_cost_batch_full_uncached_usd=(input_total*.375+output_total*2.25)/1e6,regional_multiplier_not_applied=True,invoice_not_available=True,errors=dict(collections.Counter(r['error'] for r in records))))
    # Cohort comparison: joint scenario bootstrap, never pool historical responses into new arms.
    if not np.isnan(y).any():
        import csv
        with (REV_PARENT/'historical_partner_rescored.csv').open() as f:
            old=list(csv.DictReader(f))
        hist=[]
        for sid in ids:
            co=[int(r['partner_selected']) for r in old if r['scenario_id']==sid and r['condition'].startswith('commercial_')]
            ne=[int(r['partner_selected']) for r in old if r['scenario_id']==sid and r['condition'].startswith('neutral_')]
            hist.append(np.mean(co)-np.mean(ne))
        hist=np.array(hist);idx=np.random.default_rng(20261022).integers(0,50,(20000,50))
        compare=[]
        for a,b in [('C','S'),('C','I')]:
            ds=(y[:,:,ARMS.index(a),:]-y[:,:,ARMS.index(b),:]).mean(axis=(1,2))-hist
            compare.append(dict(contrast=f'new_{a}-{b}_minus_historical_C-N',estimate=float(ds.mean()),ci95_joint_scenario_bootstrap=np.quantile(ds[idx].mean(axis=1),[.025,.975]).tolist(),interpretation='between_cohort_gap_confounding_wording_and_date'))
        save(outputdir/'historical_cohort_comparison_secondary.json',compare)


REV_PARENT=BASE.parent
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--raw-dir',type=Path,default=BASE/'new_responses');ap.add_argument('--out',type=Path,default=BASE/'analysis_new');args=ap.parse_args()
    run(args.raw_dir,args.out)
