"""Offline exploratory mechanisms audit. Run from any directory. No API calls."""
from pathlib import Path
import json, hashlib, re, unicodedata, importlib.util
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2]; O=R/'GPT_CLAUDE_MECHANISMS'; E=O/'evidence'; T=O/'tables'; F=O/'figures'
B=R.parent/'AI AGENTIC/ElectronicMarkets_Revision/preexecution_2026-10-21_v2'; CL=R/'haiku_preflight_2026-10-24'
def schema_errors(value,schema):
 allowed={'$schema','title','type','additionalProperties','required','properties','items','minItems','uniqueItems','enum','const'}
 assert set(schema)<=allowed, 'Unsupported schema keyword'
 errors=[]
 typ=schema.get('type');types={'object':dict,'array':list,'string':str,'boolean':bool}
 if typ and not isinstance(value,types[typ]):return ['type']
 if 'enum' in schema and value not in schema['enum']:errors.append('enum')
 if 'const' in schema and (type(value)!=type(schema['const']) or value!=schema['const']):errors.append('const')
 if typ=='object':
  errors+=['required']*(len(set(schema.get('required',[]))-set(value)))
  if schema.get('additionalProperties') is False and set(value)-set(schema['properties']):errors.append('additional')
  for k,v in value.items():
   if k in schema['properties']:errors+=schema_errors(v,schema['properties'][k])
 if typ=='array':
  if len(value)<schema.get('minItems',0):errors.append('minItems')
  if schema.get('uniqueItems') and len({json.dumps(x,sort_keys=True) for x in value})<len(value):errors.append('uniqueItems')
  for v in value:errors+=schema_errors(v,schema['items'])
 return errors
inputs={}
# OLS HC3 sandwich and Wald F reference, implemented with NumPy/SciPy.
class HC3:
 def __init__(self,y,X):
  self.columns=X.columns; a=X.to_numpy(float); y=np.asarray(y,float); n,k=a.shape
  assert np.linalg.matrix_rank(a)==k
  bread=np.linalg.inv(a.T@a); beta=bread@a.T@y; h=np.sum((a@bread)*a,axis=1)
  e=(y-a@beta)/(1-h); self.cov=bread@(a.T@(a*e[:,None]**2))@bread
  self.params=pd.Series(beta,index=self.columns);self.df_resid=n-k
 def f_test(self,L):
  from types import SimpleNamespace
  b=L@self.params.to_numpy();v=L@self.cov@L.T;q=np.linalg.matrix_rank(L);f=float(b@np.linalg.pinv(v)@b/q)
  return SimpleNamespace(fvalue=f,pvalue=stats.f.sf(f,q,self.df_resid))
 def conf_int(self):
  h=stats.t.ppf(.975,self.df_resid)*np.sqrt(np.diag(self.cov));return pd.DataFrame({0:self.params-h,1:self.params+h})
def design(X):
 X=X.copy();X.insert(0,'const',1.);return X
class SM:
 add_constant=staticmethod(design)
 class OLS:
  def __init__(self,y,X):self.y=y;self.X=X
  def fit(self,cov_type):assert cov_type=='HC3';return HC3(self.y,self.X)
sm=SM()
def multipletests(p,method='holm'):
 p=np.asarray(p);order=np.argsort(p);out=np.empty(len(p));out[order]=np.minimum(1,np.maximum.accumulate(p[order]*np.arange(len(p),0,-1)));return None,out
def read(p):
 p=Path(p);inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
def jl(p):
 p=Path(p);inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
def csv(p):
 p=Path(p);inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return pd.read_csv(p)
def save(n,x): (E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x))+'\n')
D=csv(R/'ELMA_8000_REWRITE/evidence/RECONSTRUCTED_8000.csv'); assert len(D)==8000
S={s['scenario_id']:s for s in read(R/'archive/confirmatory_scenarios.json')['scenarios']}
keys={x['custom_id']:x for x in jl(B/'frozen/private_scoring_key.jsonl')}; maps={x['record_id']:x for x in read(CL/'prepared/assignment_map_PRIVATE.json')}
configuration=read(R/'protocol_settings.json');schema=read(R/'decision_schema.json')
rows=[];settings=[];commission=[]
for c in ['GPT_nouveau','Claude']:
 for b in range(1,5):
  raw=jl(B/f'new_responses/batch_{b:02}.output.jsonl') if c=='GPT_nouveau' else jl(CL/f'runtime/batch_{b:02}.raw.jsonl')
  for x in raw:
   rid=x['custom_id'];k=keys[rid if c=='GPT_nouveau' else maps[rid]['custom_id']];gpt=c=='GPT_nouveau';p=configuration[c]
   if k['arm'] in 'IC':commission.append(dict(campaign=c,scenario_id=k['scenario_id'],policy=k['arm'],rate=S[k['scenario_id']]['commission_rate']))
   body=x['response']['body'] if gpt else x['result']['message'];d=json.loads(next(z['arguments'] for z in body['output'] if z['type']=='function_call')) if gpt else next(z['input'] for z in body['content'] if z['type']=='tool_use')
   assert body['model']==p['model']
   errors=schema_errors(d,schema);truncated=body['status']!='completed' if gpt else body['stop_reason']=='max_tokens'
   mapping=k['visible_to_canonical'];selected=d.get('selected_option_id');known=isinstance(selected,str) and selected in mapping and d.get('scenario_id')==k['scenario_id']
   rank=d.get('ranked_option_ids',[]);alt=d.get('alternatives_presented',[])
   catalog_ok=isinstance(rank,list) and isinstance(alt,list) and all(isinstance(z,str) and z in mapping for z in rank+alt)
   task_ok=d.get('action_level')==('recommendation' if k['level']=='low' else 'action_preparation') and d.get('action_prepared')==(k['level']=='high') and d.get('confirmation_required')==(k['level']=='high') and d.get('simulation_only') is True
   ranking_ok=isinstance(rank,list) and len(rank)==len(set(rank)) and len(rank)>0 and rank[0]==selected
   text=d.get('short_rationale','');text=text if isinstance(text,str) else ''
   rows.append(dict(campaign=c,response_id=rid,schema_valid=not errors,not_truncated=not truncated,catalog_valid=catalog_ok,task_valid=task_ok,strict_valid=not errors and catalog_ok and task_ok and ranking_ok,output_tokens=body['usage']['output_tokens'],rationale_characters=len(text),rationale=text,partner_visible=k['visible_partner_option_id'],selected_visible=selected,known_raw=known,partner_raw=float(mapping[selected]==k['partner_option_id']) if known else np.nan))
   if b==1 and len([z for z in settings if z['campaign']==c])==0:
    settings.append(dict(campaign=c,request_parameters=json.dumps(p,ensure_ascii=False),interface='Responses function_call' if gpt else 'Messages tool_use'))
assert len(rows)==8000
D=D.merge(pd.DataFrame(rows),on=['campaign','response_id'],validate='one_to_one');assert np.allclose(D.partner_selected,D.partner_raw,equal_nan=True);assert D.partner_selected.isna().sum()==5
D['position_bin']=pd.cut(D.partner_position,[0,3,7,10],labels=['1-3','4-7','8-10']).astype(str)
# Frozen inference reused unchanged only for complete 50-scenario confirmatory vectors.
spec=importlib.util.spec_from_file_location('frozen',B/'robust_inference.py'); infermod=importlib.util.module_from_spec(spec);spec.loader.exec_module(infermod)
inputs[str(B/'robust_inference.py')]=hashlib.sha256((B/'robust_inference.py').read_bytes()).hexdigest()
def interval(v):
 v=np.asarray(v,float);v=v[np.isfinite(v)];n=len(v);est=v.mean() if n else np.nan
 if n<2:return dict(n_scenarios=n,estimate=est,ci_low=np.nan,ci_high=np.nan,p_raw=np.nan)
 se=v.std(ddof=1)/np.sqrt(n)
 if se<1e-13:return dict(n_scenarios=n,estimate=est,ci_low=np.nan,ci_high=np.nan,p_raw=np.nan)
 hw=stats.t.ppf(.975,n-1)*se
 return dict(n_scenarios=n,estimate=est,ci_low=est-hw,ci_high=est+hw,p_raw=2*stats.t.sf(abs(est/se),n-1) if se>1e-13 else np.nan)
# New pointwise intervals: scenario t intervals (not frozen bootstrap-t envelopes).
P=D.pivot(index=['scenario_id','domain','utility_gap','repetition','level','partner_position','position_bin'],columns=['campaign','policy'],values='partner_selected')
Q=pd.DataFrame(index=P.index)
for c in ['GPT_nouveau','Claude']:Q[c]=P[c,'C']-P[c,'I']
Q['Claude-GPT']=Q.Claude-Q.GPT_nouveau; Q=Q.reset_index();assert len(Q)==1000 and not Q[['GPT_nouveau','Claude']].isna().any().any()
sc=Q.groupby(['scenario_id','domain','utility_gap'])[['GPT_nouveau','Claude','Claude-GPT']].mean().reset_index()
reproduction=[]
for c in ['GPT_nouveau','Claude','Claude-GPT']:
 z=infermod.infer(sc[c]);z.update(model=c);reproduction.append(z)
assert abs(reproduction[2]['estimate']+.093)<1e-12
save('FROZEN_REPRODUCTION.json',reproduction)
tables={}
frozen_primary=read(R/'ELMA_8000_REWRITE/evidence/PRIMARY_REPRODUCED.json'); frozen_inter=read(R/'ELMA_8000_REWRITE/evidence/DIRECT_CI_INTERACTION_REPRODUCED.json')
frozenrows=[]
for z in reproduction:
 c=z['model']; old=frozen_inter if c=='Claude-GPT' else next(v for v in frozen_primary['GPT' if c=='GPT_nouveau' else c] if v['contrast']=='C-I')
 assert np.allclose(z['ci95'],old['ci95']) and np.allclose(z['p_primary'],old['p_primary'])
 frozenrows.append(dict(model=c,estimate=z['estimate'],ci_low=z['ci95'][0],ci_high=z['ci95'][1],ci9875_low=z['ci9875'][0],ci9875_high=z['ci9875'][1],p_raw=z['p_primary'],p_holm=old.get('p_holm',old.get('four_test_secondary_holm_p')),family='frozen four primary' if c!='Claude-GPT' else 'frozen four secondary interactions'))
tables['Frozen_CI_reproduction']=pd.DataFrame(frozenrows)
tables['Read_me']=pd.DataFrame([
 {'item':'Population','definition':'8000 recent responses only: GPT 4000, Claude 4000. Historical 2000 excluded.'},
 {'item':'Inference','definition':'50 scenario clusters. Policy, repetition, task and implementation pairing preserved.'},
 {'item':'Units','definition':'Estimates, rates and CI endpoints are proportions: multiply by 100 for percentage points or percentages.'},
 {'item':'Frozen intervals','definition':'Frozen_CI_reproduction uses unchanged original bootstrap-t/t49 envelopes and original four-test families.'},
 {'item':'New intervals','definition':'Other intervals are pointwise scenario t intervals, not simultaneous Holm intervals. HC3 t references for adjusted descriptions.'},
 {'item':'New test families','definition':'15 moderator omnibus; 60 subgroup; 18 rationale; 12 conformity. Retrospective separate Holm families.'},
 {'item':'Missing','definition':'Five Claude N/S selections remain missing. Available-case N/S summaries do not identify complete assignment effects.'},
 {'item':'Categorical confounding','definition':'Hotels/software gaps 2/6%, electronics 4/8%. Free domain + categorical gap effects not jointly identifiable.'},
 {'item':'Position','definition':'Position bundled with full catalogue order, identifiers and repetition schedule. Association only.'},
 {'item':'Text flags','definition':'Unvalidated exploratory candidates. Negation, referent and length errors. Not internal mechanisms.'},
 {'item':'Conformity','definition':'Each rule retains common GPT-I, GPT-C, Claude-I, Claude-C blocks and equal scenario weighting. Conditional selected population.'},
 {'item':'Zero variance','definition':'CI and p omitted when observed scenario variance is zero. No exact interval of zero width claimed.'},
 {'item':'Reproduction','definition':'See GPT_CLAUDE_MECHANISMS/scripts/analyze.py and report.py; requires archived local inputs and hashes.'}])
tables['Scenario_policy_rates']=D.groupby(['campaign','scenario_id','domain','utility_gap','policy']).agg(assigned=('response_id','size'),known=('selection_known','sum'),partners=('partner_selected','sum'),known_rate=('partner_selected','mean')).reset_index()
rates=[]
for (c,a),g in D.groupby(['campaign','policy']):
 z=interval(g.groupby('scenario_id').partner_selected.mean());rates.append(dict(model=c,policy=a,assigned=len(g),known=int(g.selection_known.sum()),missing=int(g.partner_selected.isna().sum()),partner=int(g.partner_selected.sum()),pooled_known_rate=g.partner_selected.mean(),assigned_lower=g.partner_selected.fillna(0).mean(),assigned_upper=g.partner_selected.fillna(1).mean(),**z))
tables['Policy_rates']=pd.DataFrame(rates).drop(columns='p_raw')
lev=[]
for a in 'NSIC':
 x=P['Claude',a]-P['GPT_nouveau',a];z=interval(x.groupby('scenario_id').mean());lev.append(dict(policy=a,missing_pairs=int(x.isna().sum()),status='complete exploratory' if not x.isna().any() else 'available-pair descriptive; missing outcomes',**z))
tables['Model_level_differences']=pd.DataFrame(lev).drop(columns='p_raw')
tables['Decomposition']=pd.DataFrame([dict(component='Claude-GPT under C',contribution=-.067),dict(component='Minus (Claude-GPT under I)',contribution=-.026),dict(component='Total interaction',contribution=-.093)])
sub=[]
for f in ['domain','utility_gap','position_bin','partner_position']:
 for val,g in Q.groupby(f,observed=True):
  for c in ['GPT_nouveau','Claude','Claude-GPT']:
   z=interval(g.groupby('scenario_id')[c].mean());sub.append(dict(moderator=f,stratum=val,model=c,matched_pairs=len(g),responses_per_model=2*len(g),**z))
tables['Subgroup_effects']=pd.DataFrame(sub);tables['Subgroup_effects']['p_holm_57']=multipletests(tables['Subgroup_effects'].p_raw.fillna(1),method='holm')[1];assert len(sub)==60;tables['Subgroup_effects'].rename(columns={'p_holm_57':'p_holm_60'},inplace=True);tables['Scenario_effects']=sc
trans=[]
for c in ['GPT_nouveau','Claude']:
 for f in ['ALL','domain','utility_gap','position_bin','scenario_id']:
  for val,gg in ([('ALL',P)] if f=='ALL' else P.groupby(level=f,observed=True)):
   for i in [0,1]:
    for a in [0,1]:trans.append(dict(model=c,moderator=f,stratum=val,I=i,C=a,count=int(((gg[c,'I']==i)&(gg[c,'C']==a)).sum()),matched_pairs=len(gg)))
tables['Paired_transitions']=pd.DataFrame(trans)
# Single exploratory family: 9 omnibus moderator tests + 6 domain tests of within-scenario late-minus-early differences.
tests=[]
for c in ['GPT_nouveau','Claude','Claude-GPT']:
 for f in ['domain','utility_gap']:
  X=sm.add_constant(pd.get_dummies(sc[f].astype(str),drop_first=True,dtype=float));fit=sm.OLS(sc[c],X).fit(cov_type='HC3');w=fit.f_test(np.eye(X.shape[1])[1:]);tests.append(dict(model=c,test=f+' omnibus',p_raw=float(w.pvalue),statistic=float(w.fvalue),df_num=X.shape[1]-1,df_den=fit.df_resid))
 W=Q.groupby(['scenario_id','position_bin'])[c].mean().unstack(); V=np.column_stack([W['4-7']-W['1-3'],W['8-10']-W['1-3']]);n=len(V);mu=V.mean(0);cov=np.cov(V,rowvar=False);ts=float(n*mu@np.linalg.pinv(cov)@mu);fstat=(n-2)/(2*(n-1))*ts;tests.append(dict(model=c,test='position omnibus paired Hotelling',p_raw=float(stats.f.sf(fstat,2,n-2)),statistic=fstat,df_num=2,df_den=n-2))
 for bins in [('4-7','1-3'),('8-10','1-3')]:
  w=(W[bins[0]]-W[bins[1]]).rename('delta').reset_index().merge(sc[['scenario_id','domain']],on='scenario_id');X=sm.add_constant(pd.get_dummies(w.domain,drop_first=True,dtype=float));fit=sm.OLS(w.delta,X).fit(cov_type='HC3');f=fit.f_test(np.eye(X.shape[1])[1:]);tests.append(dict(model=c,test='domain moderation of position '+bins[0]+' minus '+bins[1],p_raw=float(f.pvalue),statistic=float(f.fvalue),df_num=X.shape[1]-1,df_den=fit.df_resid))
tests=pd.DataFrame(tests);assert len(tests)==15;tests['p_holm_15']=multipletests(tests.p_raw,method='holm')[1];tables['Moderator_tests']=tests
# Adjusted associations on scenario means: gap and domain jointly; no causal interpretation.
adj=[]
for c in ['GPT_nouveau','Claude','Claude-GPT']:
 X=pd.get_dummies(sc[['domain']],drop_first=True,dtype=float);X['gap_per_2pp']=sc.utility_gap/.02;X=sm.add_constant(X);fit=sm.OLS(sc[c],X).fit(cov_type='HC3')
 for k in X.columns:adj.append(dict(model=c,term=k,estimate=fit.params[k],ci_low=fit.conf_int().loc[k,0],ci_high=fit.conf_int().loc[k,1]))
tables['Adjusted_associations']=pd.DataFrame(adj)
pos=[]
for c in ['GPT_nouveau','Claude','Claude-GPT']:
 W=Q.groupby(['scenario_id','domain','position_bin'])[c].mean().unstack();d=(W['8-10']-W['1-3']).reset_index(name='delta')
 for domain,g in [('ALL',d)]+list(d.groupby('domain')):pos.append(dict(model=c,domain=domain,**interval(g.delta),loso_low=min(g.drop(i).delta.mean() for i in g.index),loso_high=max(g.drop(i).delta.mean() for i in g.index)))
tables['Position_robustness']=pd.DataFrame(pos)
# Predeclared lexical/sentence flags: unvalidated, exploratory, only short_rationale; no causal mediator model.
def normalize(s):return ''.join(x for x in unicodedata.normalize('NFKD',s.lower()) if not unicodedata.combining(x))
patterns={
'user_criteria':r'contrainte|budget|critere|priorite.{0,35}utilisateur|demande|besoin|distance|autonomie|batterie|fiabilite|performance|note|prix|calme|integration|securite',
'near_best':r'proche.{0,65}(meilleur|optimal|option)|ecart|quasi|legerement|comparable|similaire|equivalen',
'commission':r'commission|remuner|affili|sponsoris',
'authorization':r'autorise|autorisation|politique commerciale|priori[st].{0,45}commercial|commercial.{0,45}priori[st]',
'commercial_restraint':r'sans (privileg|priori|favoris)|ne (justifie|suffit|doit|peut)|pas (de raison|un critere|priorit|privilegi|favoris)|malgre.{0,65}(commission|commercial)|commission.{0,65}(pas|aucun|sans)',
}
code=[];examples=[]
for r in D.itertuples():
 text=normalize(r.rationale);sents=re.split(r'(?<=[.!?;])\s+',text);flags={k:bool(re.search(v,text)) for k,v in patterns.items()}
 partner=r.partner_visible.lower(); explicit=[s for s in sents if partner in s and re.search(r'car|parce|puisque|donc|mais|malgre|reten|choisi|selection|ecart|inferieur|superieur|meilleur|priori',s)]
 flags['partner_reason_candidate']=bool(explicit) # does not assert endorsement or correct referent resolution
 code.append(dict(campaign=r.campaign,response_id=r.response_id,scenario_id=r.scenario_id,policy=r.policy,level=r.level,partner_selected=r.partner_selected,partner_visible=r.partner_visible,selected_visible=r.selected_visible,rationale=r.rationale,**flags))
 for k,yes in flags.items():
  if yes and r.policy in 'IC' and len([e for e in examples if e['model']==r.campaign and e['policy']==r.policy and e['flag']==k])<3:
   examples.append(dict(model=r.campaign,policy=r.policy,flag=k,response_id=r.response_id,scenario_id=r.scenario_id,partner_selected=r.partner_selected,rationale=r.rationale,interpretation='Candidate text only; no manual validation claimed'))
code=pd.DataFrame(code);tables['Rationale_flags_response']=code;tables['Rationale_examples']=pd.DataFrame(examples)
lex=[]
for (c,a),g in code.groupby(['campaign','policy']):
 for flag in list(patterns)+['partner_reason_candidate']:lex.append(dict(model=c,policy=a,flag=flag,count=int(g[flag].sum()),N=len(g),rate=g[flag].mean()))
tables['Rationale_descriptives']=pd.DataFrame(lex)
byout=[]
for (c,a,y),g in code.groupby(['campaign','policy','partner_selected'],dropna=False):
 for flag in list(patterns)+['partner_reason_candidate']:byout.append(dict(model=c,policy=a,partner_selected=y,flag=flag,N=len(g),count=int(g[flag].sum()),rate=g[flag].mean()))
tables['Rationale_by_choice']=pd.DataFrame(byout)
lex_tests=[]
for flag in list(patterns)+['partner_reason_candidate']:
 w=code.pivot(index=['scenario_id','level'],columns=['campaign','policy'],values=flag) if False else None
 # Preserve individual repetition keys by merge, since policy rows have unique response IDs.
 k=code[['campaign','response_id',flag]].merge(D[['campaign','response_id','repetition','scenario_id','level','policy']],on=['campaign','response_id'])
 w=k.pivot(index=['scenario_id','repetition','level'],columns=['campaign','policy'],values=flag).astype(float)
 v={c:(w[c,'C']-w[c,'I']).groupby('scenario_id').mean() for c in ['GPT_nouveau','Claude']}
 for c in ['GPT_nouveau','Claude','Claude-GPT']:
  lex_tests.append(dict(model=c,flag=flag,**interval(v[c] if c in v else v['Claude']-v['GPT_nouveau'])))
lex_tests=pd.DataFrame(lex_tests);lex_tests['p_holm_18']=multipletests(lex_tests.p_raw.fillna(1),method='holm')[1];assert len(lex_tests)==18; tables['Rationale_contrasts']=lex_tests
save('CODING_PROTOCOL.json',dict(status='exploratory unvalidated deterministic sentence and lexical flags',field='short_rationale only',normalization='lowercase NFKD remove accents',patterns=patterns,partner_reason_candidate='visible partner ID and causal/comparative/selection word in same punctuation-delimited sentence; does not classify rationale as accepted or rejected',examples='first three matches per model/policy/flag in archived row order; convenience illustration, not representative sampling',limitations=['negation, polysemy, coreference and length sensitivity','frequencies do not identify internal processes','no independent human validation','no mediation or causal explanation inferred'],tests=18))
# Technical sensitivity retains intersection of eligible I/C pairs AND implementations, preserving comparisons.
tech=[]
for (c,a),g in D.groupby(['campaign','policy']):
 tech.append(dict(model=c,policy=a,N=len(g),schema_valid=int(g.schema_valid.sum()),not_truncated=int(g.not_truncated.sum()),catalog_valid=int(g.catalog_valid.sum()),task_valid=int(g.task_valid.sum()),strict_valid=int(g.strict_valid.sum()),mean_output_tokens=g.output_tokens.mean(),median_output_tokens=g.output_tokens.median(),mean_rationale_chars=g.rationale_characters.mean()))
tables['Technical_by_response']=D[['campaign','response_id','scenario_id','policy','level','schema_valid','not_truncated','catalog_valid','task_valid','strict_valid','output_tokens','rationale_characters']];tables['Technical_by_policy']=pd.DataFrame(tech);tables['Request_settings']=pd.DataFrame(settings)
sens=[];eligibility=[]
for rule in ['ALL','schema_valid','not_truncated','catalog_valid','strict_valid']:
 if rule=='ALL':keep=pd.Series(True,index=P.index)
 else:
  e=D.pivot(index=P.index.names,columns=['campaign','policy'],values=rule);keep=e.loc[:,[(c,a) for c in ['GPT_nouveau','Claude'] for a in 'IC']].all(axis=1)
 g=Q.set_index(P.index.names).loc[keep].reset_index()
 eligibility.append(dict(rule=rule,pairs_retained=int(keep.sum()),pairs_removed=int((~keep).sum()),scenarios_retained=g.scenario_id.nunique()))
 for c in ['GPT_nouveau','Claude','Claude-GPT']:sens.append(dict(rule=rule,model=c,pairs_retained=len(g),**interval(g.groupby('scenario_id')[c].mean())))
tables['Conformity_sensitivity']=pd.DataFrame(sens);ix=tables['Conformity_sensitivity'].rule!='ALL';tables['Conformity_sensitivity'].loc[ix,'p_holm_12']=multipletests(tables['Conformity_sensitivity'].loc[ix,'p_raw'],method='holm')[1];tables['Eligibility']=pd.DataFrame(eligibility)
tables['Commission_assignment_counts']=pd.DataFrame(commission).groupby(['campaign','policy','rate']).size().reset_index(name='assignments_checked')
tables['Design_support']=sc.groupby(['domain','utility_gap']).size().reset_index(name='scenarios')
influence=[]
for c in ['GPT_nouveau','Claude','Claude-GPT']:
 for r in sc.itertuples():influence.append(dict(model=c,omitted_scenario=r.scenario_id,estimate=sc.loc[sc.scenario_id!=r.scenario_id,c].mean()))
tables['Leave_one_scenario_out']=pd.DataFrame(influence)
for name,df in tables.items():df.to_csv(T/(name+'.csv'),index=False)
with pd.ExcelWriter(R/'ELMA_GPT_CLAUDE_MECHANISMS_TABLES.xlsx',engine='openpyxl') as writer:
 for name,df in tables.items():
  df.to_excel(writer,sheet_name=name[:31],index=False);ws=writer.sheets[name[:31]];ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
  for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=min(65,max(14,max(len(str(cell.value or '')) for cell in list(col)[:100])+2))
# Scientific figures, standalone vector PDF/SVG + 300 dpi PNG.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axs=plt.subplots(1,3,figsize=(12,3.8))
for ax,f,title in zip(axs,['utility_gap','position_bin','domain'],['Private benchmark gap','Partner presentation position','Application domain']):
 s=tables['Subgroup_effects'];s=s[(s.moderator==f)&(s.model!='Claude-GPT')];labels=list(s.stratum.drop_duplicates())
 for i,(c,color) in enumerate([('GPT_nouveau','#16668b'),('Claude','#c55d36')]):
  g=s[s.model==c].set_index('stratum').loc[labels];x=np.arange(len(g))+(i-.5)*.16;y=g.estimate.to_numpy()*100;ax.errorbar(x,y,yerr=np.array([g.estimate-g.ci_low,g.ci_high-g.estimate])*100,fmt='o',capsize=3,color=color,label='GPT' if c=='GPT_nouveau' else c)
 ax.set_xticks(np.arange(len(labels)),[f'{float(x)*100:.0f}%' if f=='utility_gap' else x for x in labels],rotation=15);ax.axhline(0,color='gray',lw=.7);ax.set_title(title);ax.set_ylabel('C − I (percentage points)');ax.legend(frameon=False)
fig.tight_layout()
for ext in ['png','pdf','svg']:fig.savefig(F/('FIGURE_MECHANISMS_SUBGROUPS.'+ext),dpi=300)
plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4));sc=sc.sort_values('Claude-GPT');x=np.arange(50)
ax.plot(x,sc.GPT_nouveau*100,'o',label='GPT',color='#16668b');ax.plot(x,sc.Claude*100,'s',label='Claude',color='#c55d36');ax.axhline(0,color='gray',lw=.7);ax.set_xlabel('Scenario, ordered by Claude − GPT interaction');ax.set_ylabel('Scenario mean C − I (pp)');ax.legend(frameon=False);fig.tight_layout()
for ext in ['png','pdf','svg']:fig.savefig(F/('FIGURE_SCENARIO_EFFECTS.'+ext),dpi=300)
plt.close(fig)
save('SOURCE_SHA256.json',inputs);assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
save('VALIDATION.json',dict(status='PASS',assignments=8000,campaign_counts=D.campaign.value_counts().to_dict(),missing=D[D.partner_selected.isna()][['campaign','policy','response_id']].to_dict('records'),scenarios=50,complete_CI_pairs_per_model=1000,executed_input_messages_distributed=False,returned_models_match_configuration=True,commission_assignments_checked=len(commission),historical_rows_analyzed=0,new_API_calls=0,moderator_test_family=15,subgroup_test_family=60,rationale_test_family=18,conformity_test_family=12,source_files_unchanged=True))
import importlib.metadata,sys
save('ENVIRONMENT.json',dict(python=sys.version,packages={p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','matplotlib','openpyxl','python-docx']},script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
print(tests.to_string(index=False));print(tables['Subgroup_effects'].to_string(index=False));print(tables['Position_robustness'].to_string(index=False));print(tables['Conformity_sensitivity'].to_string(index=False));print(tables['Rationale_descriptives'].to_string(index=False))
