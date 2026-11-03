#!/usr/bin/env python3
"""Audit file contents, nested archives and document/image metadata.
Private identity terms can be supplied from a local JSON array; they are never
printed or copied into the public report. Scientific citations and synthetic
record IDs are preserved. Requires Poppler pdfinfo/pdftotext for full PDF review.
"""
import argparse,gzip,hashlib,io,json,re,subprocess,tempfile,tokenize,unicodedata,zipfile
from collections import Counter
from pathlib import Path
from PIL import Image
import xml.etree.ElementTree as E

NEUTRAL={'','anonymous','anonymous authors','anonymous author','author','authors','openpyxl','python-docx','unknown'}
PLACEHOLDERS={'anonymous@example.com','noreply@github.com'}
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',str(s).casefold()) if not unicodedata.combining(c))
def main():
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);a.add_argument('--private-terms-file',type=Path);a.add_argument('--history',action='store_true');a.add_argument('--report',type=Path,required=True);args=a.parse_args()
    root=args.root.resolve();terms=json.loads(args.private_terms_file.read_text()) if args.private_terms_file else []
    terms=[norm(t) for t in terms if t];findings=[];counts=Counter();examined=set();meta_counts=Counter()
    email=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
    userpath=re.compile(r'/home/[A-Za-z0-9_.-]+/|[A-Z]:\\Users\\[A-Za-z0-9_.-]+\\')
    def finding(path,kind,member=''):
        x=dict(path=path,category=kind)
        if member:x['member']=member
        if x not in findings:findings.append(x)
    def textcheck(text,path,member=''):
        n=norm(text)
        if any(t in n for t in terms):finding(path,'private_identity_term',member)
        if userpath.search(text):finding(path,'personal_local_path',member)
        if Path(path).suffix=='.py':
            try:text='\n'.join(t.string for t in tokenize.generate_tokens(io.StringIO(text).readline) if t.type in [tokenize.STRING,tokenize.COMMENT])
            except (tokenize.TokenError,IndentationError):pass
        if any(x.casefold() not in PLACEHOLDERS for x in email.findall(text)):finding(path,'nonplaceholder_email',member)
    def inspect(data,path,historical=False):
        digest=hashlib.sha256(data).hexdigest()
        if historical and digest in examined:return
        examined.add(digest);counts['additional_historical_payloads' if historical else 'working_payloads_including_decompressed']+=1
        suffix=Path(path).suffix.lower()
        if suffix=='.gz':
            counts['gzip_archives']+=1;inspect(gzip.decompress(data),path[:-3],historical);return
        if suffix in ['.docx','.xlsx','.zip']:
            counts['office_or_zip_archives']+=1
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for name in z.namelist():
                    if suffix=='.zip' and not name.endswith('/'):
                        inspect(z.read(name),path+'!'+name,historical);continue
                    if name.endswith(('.xml','.rels')):
                        t=z.read(name).decode(errors='replace');textcheck(t,path,name)
                        if name=='docProps/core.xml':
                            for x in E.fromstring(t):
                                key=x.tag.split('}')[-1]
                                if key in ['creator','lastModifiedBy']:
                                    meta_counts['office_identity_properties']+=1
                                    if norm(x.text or '') not in NEUTRAL:finding(path,'nonneutral_office_identity',name)
            return
        if suffix=='.pdf':
            counts['pdf_documents']+=1
            with tempfile.NamedTemporaryFile(suffix='.pdf') as f:
                f.write(data);f.flush()
                info=subprocess.check_output(['pdfinfo',f.name],stderr=subprocess.DEVNULL,text=True)
                text=subprocess.check_output(['pdftotext',f.name,'-'],stderr=subprocess.DEVNULL).decode(errors='replace')
            textcheck(info+'\n'+text,path)
            for line in info.splitlines():
                if line.startswith('Author:'):
                    meta_counts['pdf_author_properties']+=1
                    if norm(line.split(':',1)[1].strip()) not in NEUTRAL:finding(path,'nonneutral_pdf_author')
            return
        if suffix in ['.png','.jpg','.jpeg']:
            counts['images']+=1
            with Image.open(io.BytesIO(data)) as im:
                info={k:str(v) for k,v in im.info.items() if k!='dpi'}
                textcheck(json.dumps(info),path)
                exif=im.getexif()
                if exif:finding(path,'image_exif_requires_review')
                meta_counts['images_with_only_generic_software_metadata']+=int(set(info)<={'Software'})
            return
        try:textcheck(data.decode(),path)
        except UnicodeDecodeError:counts['unparsed_binary_files']+=1
    try:
        tracked=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root).decode().split('\0')
        paths=sorted({p for p in tracked if p and not p.startswith('.git/')})
    except subprocess.CalledProcessError:
        paths=[str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and not any(s in p.parts for s in ['.git','__pycache__','.venv'])]
    physical_files=0
    for rel in paths:
        path=root/rel
        if path.resolve()==args.report.resolve():continue
        if path.is_file():physical_files+=1;inspect(path.read_bytes(),rel)
    history_commits=0;authors=set()
    if args.history:
        commits=subprocess.check_output(['git','rev-list','--all'],cwd=root,text=True).splitlines();history_commits=len(commits)
        # Metadata is described by neutral/alias status, never by publishing addresses.
        for line in subprocess.check_output(['git','log','--all','--format=%an%x00%ae%x00%cn%x00%ce'],cwd=root,text=True).splitlines():
            vals=line.split('\0')
            for name,address in [vals[:2],vals[2:]]:
                authors.add('neutral' if norm(name) in NEUTRAL else 'platform_alias')
                if any(t in norm(name+' '+address) for t in terms):finding('(git history)','private_identity_in_commit_metadata')
                if address.casefold() not in PLACEHOLDERS and not address.endswith('@users.noreply.github.com'):finding('(git history)','nonanonymous_commit_email')
        blobs={}
        for commit in commits:
            for line in subprocess.check_output(['git','ls-tree','-r',commit],cwd=root,text=True).splitlines():
                meta,path=line.split('\t',1);mode,kind,sha=meta.split()
                if kind=='blob':blobs.setdefault(sha,path)
        for sha,path in blobs.items():inspect(subprocess.check_output(['git','cat-file','blob',sha],cwd=root),path,historical=True)
    result=dict(status='PASS' if not findings else 'REVIEW_REQUIRED',physical_working_files_scanned=physical_files,scope='working files, gzip/Office archives, PDF text/author metadata, image metadata'+(' and reachable Git history' if args.history else ''),counts=dict(counts),metadata_checks=dict(meta_counts),private_identity_terms_checked=bool(terms),private_identity_values_not_published=True,reachable_commits_checked=history_commits,commit_identity_categories=sorted(authors),findings=findings,
        platform_limit='GitHub account/actor aliases, repository ownership, external copies, cached history and cross-repository linkability are not removed by file anonymization. No absolute non-reidentification guarantee is made.')
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if findings:raise SystemExit(1)
if __name__=='__main__':main()
