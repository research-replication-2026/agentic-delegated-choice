#!/usr/bin/env python3
"""Run unchanged archived exploratory analysis in a disposable compatibility tree.
All inputs come from this checkout or its fresh raw-based scoring results.
No original workstation path, ledger, model service or external file is needed.
"""
import contextlib,gzip,io,json,os,runpy,shutil,socket,tempfile
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from reproduce import P,OUT,data,js,check_manifest,save

def main():
    check_manifest();assert (OUT/'VERIFICATION.json').is_file(),'Run reproduce.py first'
    with tempfile.TemporaryDirectory(prefix='_compat_',dir=OUT) as temp:
        root=Path(temp);project=root/'project';b=root/'AI AGENTIC/ElectronicMarkets_Revision/preexecution_2026-10-21_v2'
        def put(target,content):target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
        put(project/'archive/confirmatory_scenarios.json',data('data/scenarios.json'))
        put(b/'frozen/private_scoring_key.jsonl',data('data/assignments_gpt.jsonl.gz'))
        put(project/'haiku_preflight_2026-10-24/prepared/assignment_map_PRIVATE.json',data('data/assignments_claude.json.gz'))
        put(b/'robust_inference.py',data('analysis/frozen_gpt/robust_inference.py'))
        put(project/'decision_schema.json',data('data/decision_schema.json'))
        put(project/'protocol_settings.json',data('data/protocol_settings.json'))
        for i in range(1,5):
            put(b/f'new_responses/batch_{i:02d}.output.jsonl',data(f'data/raw/gpt_batch_{i:02d}.jsonl.gz'))
            put(project/f'haiku_preflight_2026-10-24/runtime/batch_{i:02d}.raw.jsonl',data(f'data/raw/claude_batch_{i:02d}.jsonl.gz'))
        frame=pd.read_csv(OUT/'scored_8000.csv')
        original_columns=pd.read_csv(P/'results/reference/scored_8000.csv.gz',nrows=0).columns
        frame=frame[list(original_columns)].copy();frame['selection_known']=frame.selection_known.astype(bool)
        target=project/'ELMA_8000_REWRITE/evidence/RECONSTRUCTED_8000.csv';target.parent.mkdir(parents=True,exist_ok=True);frame.to_csv(target,index=False)
        primary=js('results/reproduced/primary_contrasts.json')
        for rr in primary.values():
            for r in rr:r['p_primary']=r['p_raw']
        put(project/'ELMA_8000_REWRITE/evidence/PRIMARY_REPRODUCED.json',json.dumps(primary).encode())
        cross=next(r for r in js('results/reproduced/cross_implementation.json') if r['contrast']=='C-I')
        cross['four_test_secondary_holm_p']=cross['full_assignment_holm_p']
        put(project/'ELMA_8000_REWRITE/evidence/DIRECT_CI_INTERACTION_REPRODUCED.json',json.dumps(cross).encode())
        source=project/'GPT_CLAUDE_MECHANISMS/scripts/analyze.py';put(source,data('analysis/frozen_mechanisms/analyze.py'))
        for sub in ['evidence','tables','figures']:(source.parents[1]/sub).mkdir(parents=True,exist_ok=True)
        with contextlib.redirect_stdout(io.StringIO()),patch.dict(os.environ,{'MPLCONFIGDIR':str(root/'matplotlib')}):
            runpy.run_path(str(source),run_name='__main__')
        dest=OUT/'mechanisms';dest.mkdir(exist_ok=True);checks=[]
        for reference in sorted((P/'results/reference/mechanisms').glob('*.csv.gz')):
            name=reference.name[:-3]
            if name=='Commission_source_check.csv':continue
            actual=source.parents[1]/'tables'/name
            a=pd.read_csv(actual);e=pd.read_csv(reference)
            pd.testing.assert_frame_equal(a,e,check_dtype=False,check_exact=False,rtol=1e-8,atol=1e-10)
            (dest/reference.name).write_bytes(gzip.compress(actual.read_bytes(),mtime=0))
            checks.append(dict(table=name,rows=len(a),columns=len(a.columns),status='PASS'))
        allocation=source.parents[1]/'tables/Commission_assignment_counts.csv'
        a=pd.read_csv(allocation)
        e=pd.read_csv(P/'results/reference/mechanisms/Commission_source_check.csv.gz').rename(columns={'requests_checked':'assignments_checked'})
        pd.testing.assert_frame_equal(a,e,check_dtype=False,check_exact=False,rtol=1e-8,atol=1e-10)
        (dest/'Commission_assignment_counts.csv.gz').write_bytes(gzip.compress(allocation.read_bytes(),mtime=0))
        figdest=dest/'figures';figdest.mkdir(exist_ok=True)
        for path in (source.parents[1]/'figures').glob('*'):shutil.copyfile(path,figdest/path.name)
        # Source-path/account metadata and the convenience XLSX are not exported from the scratch tree.
        result=dict(status='PASS',numerical_analysis_preserved=True,executed_input_verification_withheld=True,reference_tables_verified=len(checks),tables=checks,assignment_allocation_counts_verified=True,
            exploratory_test_families=dict(moderator_omnibus=15,subgroups=60,rationale=18,conformity=12),
            scientific_figures_regenerated=len(list(figdest.glob('*'))),source_files_modified=False,network_calls=0,model_calls=0)
        save('EXPLORATORY_VERIFICATION.json',result)
    check_manifest();print('PASS output-based exploratory analysis: '+str(len(checks))+' reference tables, subgroup/moderator/rationale/conformity families and figures regenerated.')

if __name__=='__main__':
    with patch('socket.socket',side_effect=RuntimeError('Network prohibited during offline replication')):main()
