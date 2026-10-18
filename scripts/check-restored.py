"""Check substantive content, navigation, artifacts, and deployed bytes."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from concurrent.futures import ThreadPoolExecutor
import argparse,hashlib,json,re,tempfile,time
from render_site import ROOT,PAGES,PUBLIC_FILES,ASSETS,SOURCE_FILES,build,route,main_text,BASE
class Doc(HTMLParser):
    def __init__(self):super().__init__();self.tags=[];self.ids=[];self.refs=[];self.canonical=[];self.json=[];self.capture=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.tags.append((tag,a))
        if 'id' in a:self.ids.append(a['id'])
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
        for key in ('href','src'):
            if a.get(key):self.refs.append(a[key])
        if tag=='script' and a.get('type') in ('application/ld+json','application/json'):self.capture=''
    def handle_data(self,data):
        if self.capture is not None:self.capture+=data
    def handle_endtag(self,tag):
        if tag=='script' and self.capture is not None:self.json.append(json.loads(self.capture));self.capture=None
def check(root):
    errors=[]
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual!=set(PUBLIC_FILES):errors.append('Publication boundary differs: '+str(actual.symmetric_difference(PUBLIC_FILES)))
    manifest=json.loads((root/'publication/manifest.json').read_text(encoding='utf-8'))
    for p,digest in manifest['files'].items():
        if hashlib.sha256((root/p).read_bytes()).hexdigest()!=digest:errors.append('File changed after build: '+p)
    docs={}
    for p in (*PAGES,'library/index.html','publication/index.html'):
        source=(root/p).read_text(encoding='utf-8');d=Doc();d.feed(source);docs[p]=d
        if d.canonical!=[BASE+route(p)]:errors.append('Canonical mismatch: '+p)
        if sum(t=='main' for t,a in d.tags)!=1:errors.append('Main landmark count: '+p)
        if sum(t=='h1' for t,a in d.tags)!=1:errors.append('H1 count: '+p)
        if not any(t=='nav' and a.get('aria-label')=='Primary' for t,a in d.tags):errors.append('Missing primary navigation: '+p)
        if not d.json:errors.append('Missing machine data: '+p)
        if len(d.ids)!=len(set(d.ids)):errors.append('Duplicate IDs: '+p+' '+str([i for i in set(d.ids) if d.ids.count(i)>1]))
        if len(main_text(source).split())<45:errors.append('Insufficient page content: '+p)
        for phrase in ('Substantive material remains withheld','will be linked here after publication review','Follow the Chain Challenge','<!--SITE_HEADER-->','{{definition:'):
            if phrase in source:errors.append('Placeholder or retired copy: '+p)
    for p,d in docs.items():
        for ref in d.refs:
            u=urlsplit(urljoin(BASE+route(p),ref))
            if u.netloc!=urlsplit(BASE).netloc:continue
            target=unquote(u.path.lstrip('/'))
            if target.endswith('/') or not target:target+='index.html'
            if not (root/target).is_file():errors.append(f'Broken link/asset: {p} -> {ref}')
            elif u.fragment and target in docs and u.fragment not in docs[target].ids:errors.append(f'Missing anchor: {p} -> {ref}')
    faq=json.loads((root/'faq/index.json').read_text(encoding='utf-8'))
    visible=main_text((root/'faq/index.html').read_text(encoding='utf-8'))
    for q in faq['mainEntity']:
        if q['name'] not in visible or q['acceptedAnswer']['text'] not in visible:errors.append('FAQ human/machine mismatch')
    for p in SOURCE_FILES:
        if (root/p).read_bytes()!=(ROOT/p).read_bytes():errors.append('Source edition altered: '+p)
    for p in ('assets/opening.js','assets/opening.css','assets/material-environment.js','assets/earth-renderer.js'):
        if (root/p).read_bytes()!=(ROOT/p).read_bytes():errors.append('Opening asset altered: '+p)
    if errors:raise AssertionError('\n'.join(sorted(set(errors))))
    print(f'Passed: {len(docs)} substantive pages, all links and anchors, structured data, exact source editions, and {len(PUBLIC_FILES)}-file boundary.')
def live(root,base,attempts,delay):
    # Pages consumes this hidden build marker; it is not a public resource.
    served_files=[p for p in PUBLIC_FILES if p!='.nojekyll']
    def fetch(p):
        u=base.rstrip('/')+'/'+p+'?release=20261018-substantive'
        try:
            with urlopen(Request(u,headers={'Cache-Control':'no-cache'}),timeout=30) as r:data=r.read()
            return None if data==(root/p).read_bytes() else 'Stale bytes: '+p
        except (HTTPError,URLError,TimeoutError) as e:return p+': '+str(e)
    for attempt in range(attempts):
        with ThreadPoolExecutor(max_workers=6) as pool:errors=[x for x in pool.map(fetch,served_files) if x]
        for p in ('GOVERNEDLOGIC_COM_PRD.txt','scripts/restore_content.py','components/header.html','recovery-provenance.json'):
            try:
                with urlopen(base.rstrip('/')+'/'+p,timeout=15) as r:errors.append('Internal file exposed: '+p)
            except HTTPError as e:
                if e.code!=404:errors.append('Unexpected boundary status: '+p)
        if not errors:print(f'Live verification passed: all {len(served_files)} served files match the built release; internal sources remain excluded.');return
        if attempt+1<attempts:time.sleep(delay)
    raise AssertionError('\n'.join(errors))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root');a.add_argument('--artifact',action='store_true');a.add_argument('--live');a.add_argument('--attempts',type=int,default=1);a.add_argument('--delay',type=float,default=10);args=a.parse_args()
    with tempfile.TemporaryDirectory(dir=ROOT.parent,ignore_cleanup_errors=True) as temp:
        root=Path(args.root) if args.root else Path(temp)/'site'
        if not args.root:build(root)
        check(root)
        if args.live:live(root,args.live,args.attempts,args.delay)