#!/usr/bin/env python3
"""Check the current tree/export for distributed model-input messages.
Generated response text and structural schemas are analytical data, not input
messages. This check does not erase historical commits or external copies.
"""
import argparse,csv,gzip,hashlib,io,json,subprocess,zipfile
from pathlib import Path
FIELDS={'system_prompt','user_prompt','system_exact','user_exact','raw_user','user_request','system_message','user_message'}
def main():
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);a.add_argument('--report',type=Path,required=True);args=a.parse_args()
    root=args.root.resolve();findings=[];counts=dict(files=0,gzip_payloads=0,zip_members=0)
    def flag(path,kind):
        item=dict(path=path,category=kind)
        if item not in findings:findings.append(item)
    def obj(x,path):
        if isinstance(x,dict):
            if x.get('role') in ['system','user','developer'] and x.get('content'):flag(path,'model_input_message')
            for k,v in x.items():
                if k in FIELDS and isinstance(v,str) and v.strip():flag(path,'input_text_field')
                if k=='system' and isinstance(v,str) and v.strip():flag(path,'system_message_field')
                if k=='instructions' and isinstance(v,str) and v.strip():flag(path,'instruction_echo_field')
                obj(v,path)
        elif isinstance(x,list):
            for v in x:obj(v,path)
    def inspect(b,path):
        suffix=Path(path).suffix.lower()
        if suffix=='.gz':counts['gzip_payloads']+=1;inspect(gzip.decompress(b),path[:-3]);return
        if suffix=='.zip':
            with zipfile.ZipFile(io.BytesIO(b)) as z:
                for name in z.namelist():
                    if not name.endswith('/'):counts['zip_members']+=1;inspect(z.read(name),path+'!'+name)
            return
        if suffix in ['.json','.jsonl']:
            try:
                if suffix=='.json':obj(json.loads(b),path)
                else:
                    for line in b.splitlines():
                        if line.strip():obj(json.loads(line),path)
            except (ValueError,UnicodeDecodeError):flag(path,'unreadable_structured_file')
        elif suffix=='.csv':
            try:
                for row in csv.DictReader(io.StringIO(b.decode('utf-8-sig'))):
                    for k,v in row.items():
                        if k in FIELDS and v:flag(path,'input_text_column')
            except (UnicodeDecodeError,csv.Error):flag(path,'unreadable_table')
    try:paths=[p for p in subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root).decode().split('\0') if p]
    except subprocess.CalledProcessError:paths=[str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ['.git','__pycache__'])]
    for rel in paths:
        p=root/rel
        if not p.is_file() or p.resolve()==args.report.resolve():continue
        counts['files']+=1;inspect(p.read_bytes(),rel)
    materials=root/'revised_8000/experimental_materials'
    if materials.exists() and any(p.is_file() for p in materials.rglob('*')):flag('revised_8000/experimental_materials','executed_materials_present')
    result=dict(status='PASS' if not findings else 'FAIL',scope='current tree and nested export only; historical/public access is separate',counts=counts,findings=findings,input_messages_distributed=False if not findings else None,generated_outputs_preserved=True,full_protocol_replication='PARTIEL because executed model-input messages are withheld')
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    if findings:raise SystemExit(1)
if __name__=='__main__':main()
