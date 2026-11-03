#!/usr/bin/env python3
"""Check released bytes and offline results; --seal writes the input hash manifest.
No network. Never reads private workstation sources or provider credentials.
"""
import argparse,csv,gzip,hashlib,io,json,re,sys,tokenize
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x):(P/'provenance'/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
    a=argparse.ArgumentParser();a.add_argument('--seal',action='store_true');args=a.parse_args()
    exclusions={'provenance/RELEASE_SHA256.json','provenance/CONFIDENTIALITY_SCAN.json','provenance/RELEASE_VERIFICATION.json'}
    inputs={str(p.relative_to(P)):sha(p) for p in sorted(P.rglob('*')) if p.is_file() and 'results/reproduced' not in str(p.relative_to(P)) and '__pycache__' not in p.parts and str(p.relative_to(P)) not in exclusions}
    if args.seal:dump('RELEASE_SHA256.json',inputs)
    expected=json.loads((P/'provenance/RELEASE_SHA256.json').read_text());assert inputs==expected,'Released input changed or added'
    patterns={
      'provider_or_git_token':re.compile(r'\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{25,}|AKIA[A-Z0-9]{16})\b'),
      'private_key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
      'personal_local_path':re.compile(r'/home/[A-Za-z0-9_.-]+/|[A-Z]:\\Users\\[A-Za-z0-9_.-]+\\'),
      'email_address':re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')}
    findings=[];checked=0;archives=0
    for p in sorted(P.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or str(p.relative_to(P)) in exclusions:continue
        b=p.read_bytes()
        if p.suffix=='.gz':b=gzip.decompress(b);archives+=1
        try:text=b.decode('utf-8')
        except UnicodeDecodeError:continue
        checked+=1
        for kind,pat in patterns.items():
            searchtext=text
            if kind=='email_address' and p.suffix=='.py':
                # Python matrix multiplication is not an email address.
                # Hardcoded addresses must occur in string/comment tokens in valid Python.
                searchtext='\n'.join(tok.string for tok in tokenize.generate_tokens(io.StringIO(text).readline) if tok.type in [tokenize.STRING,tokenize.COMMENT])
            if pat.search(searchtext):findings.append(dict(path=str(p.relative_to(P)),category=kind))
    assert not findings,findings
    with (P/'provenance/source_to_release_manifest.csv').open() as f:manifest=list(csv.DictReader(f))
    for r in manifest:
        path=P/r['path'];assert sha(path)==r['published_sha256']
        b=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()
        if r['transformation'] in ['byte_identical','gzip_lossless']:assert hashlib.sha256(b).hexdigest()==r['source_sha256']
    core=json.loads((P/'results/reproduced/VERIFICATION.json').read_text());extended=json.loads((P/'results/reproduced/EXPLORATORY_VERIFICATION.json').read_text())
    assert core['status']==extended['status']=='PASS'
    assert (core['raw_responses'],core['recognized_selections'],core['unknown_selections'])==(8000,7995,5)
    assert core['manuscript_numeric_table_rows_checked']==24 and core['economic_comparisons']==144
    assert extended['reference_tables_verified']==25 and extended['scientific_figures_regenerated']==6
    coding=json.loads((P/'results/reproduced/coding_statistics.json').read_text())
    assert coding['initial']['agreements']==392 and coding['final_NLP_agreements']==388
    assert abs(coding['initial']['cohen_kappa']-0.9647840824052472)<1e-14
    files=[p for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    dump('CONFIDENTIALITY_SCAN.json',dict(status='PASS',scope='new revised_8000 release, including decompressed archives; excludes self/generated scan reports',utf8_files_scanned=checked,gzip_archives_opened=archives,findings=findings,binary_plot_files_not_text_scanned=True,source_exclusion_review='CONFIDENTIALITY_REVIEW.md'))
    dump('RELEASE_VERIFICATION.json',dict(status='PASS',verdict='COMPLET',scope='Offline analytical replication of the revised 8000-response experiment and existing coding control; no new generation or claims about unmeasured consumer exposure',pinned_input_files=len(inputs),source_manifest_rows=len(manifest),release_file_count_before_this_report=len(files),total_bytes=sum(p.stat().st_size for p in files),raw_responses=8000,recognized_selections=7995,matched_main_numeric_rows=24,economic_comparisons=144,exploratory_tables=25,initial_coding_agreement='392/400',cohen_kappa=coding['initial']['cohen_kappa'],final_NLP_agreement='388/400',model_API_calls=0,network_calls_during_reproduction=0))
    print('PASS release integrity/privacy and complete archived analytical replication; '+str(len(inputs))+' immutable inputs pinned.')
if __name__=='__main__':main()
