"""Check substantive content, navigation, artifacts, and deployed bytes."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import argparse,hashlib,json,re,tempfile,time
from render_site import ROOT,PAGES,PUBLIC_FILES,ASSETS,SOURCE_FILES,build,route,main_text,BASE
class Doc(HTMLParser):
    def __init__(self):
        super().__init__();self.tags=[];self.ids=[];self.refs=[];self.canonical=[];self.json=[];self.capture=None
        self.forms=[];self._form=None;self.anchors=[];self.hidden=[];self.button_query=[];self.blank=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.tags.append((tag,a))
        if 'id' in a:self.ids.append(a['id'])
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
        for key in ('href','src'):
            if a.get(key) and tag not in ('form','button'):self.refs.append(a[key])
        if tag=='a' and a.get('href') is not None:self.anchors.append(a.get('href'))
        if tag=='form':
            self._form={'method':(a.get('method') or 'get').strip().lower(),'action':a.get('action'),'named':0,'target':(a.get('target') or '')}
            self.forms.append(self._form)
        if tag=='input' and (a.get('type') or '').lower()=='hidden':self.hidden.append(a.get('name') or '')
        if tag in ('button','input'):
            kind=(a.get('type') or ('submit' if tag=='button' else '')).lower()
            if kind in ('submit','button','') and (a.get('name') or a.get('value') is not None and tag=='button'):
                if a.get('name') or (tag=='button' and 'value' in a):self.button_query.append((a.get('name'),a.get('value')))
            if tag in ('button','input') and self._form is not None and a.get('name') and kind=='submit':self._form['named']+=1
        if (a.get('target') or '').lower()=='_blank' and (a.get('href') or a.get('action')):self.blank.append(a.get('href') or a.get('action'))
        if a.get('formaction') is not None:
            self.forms.append({'method':(a.get('formmethod') or (self._form or {}).get('method') or 'get').strip().lower(),'action':a.get('formaction'),'named':1 if a.get('name') else 0,'formaction':True,'inform':self._form is not None})
        if tag=='script' and a.get('type') in ('application/ld+json','application/json'):self.capture=''
    def handle_data(self,data):
        if self.capture is not None:self.capture+=data
    def handle_endtag(self,tag):
        if tag=='form':self._form=None
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
        for form in d.forms:
            raw=form['action'];where=f'{p} form action={raw!r}'
            if form['method']!='get':errors.append('Form method must be get: '+where)
            if raw is not None and '?' in raw:errors.append('Form action must not contain a query: '+where)
            if form['named']:errors.append('Named submit is not allowed: '+where)
            if form.get('formaction') and not form.get('inform'):errors.append('formaction outside a form: '+where)
            if raw is None:continue
            u=urlsplit(urljoin(BASE+route(p),raw))
            if u.netloc!=urlsplit(BASE).netloc:errors.append('External form action: '+where);continue
            target=unquote(u.path.lstrip('/'))
            if target.endswith('/') or not target:target+='index.html'
            if not (root/target).is_file():errors.append(f'Form action is not a built route or file: {p} -> {raw}')
            if (form.get('target') or '').lower()=='_blank':errors.append('Internal form target=_blank: '+where)
        if d.hidden:errors.append('Hidden input is not allowed: '+p)
        if d.button_query:errors.append('Button name or value is not allowed: '+p)
        for tag,attrs in d.tags:
            if tag=='button' and 'href' in attrs:errors.append('Button href is not allowed: '+p+' -> '+str(attrs.get('href')))
        for href in d.blank:
            u=urlsplit(urljoin(BASE+route(p),href))
            if u.netloc in ('',urlsplit(BASE).netloc):errors.append(f'Internal target=_blank: {p} -> {href}')
    catalog=json.loads((root/'publication/catalog.json').read_text(encoding='utf-8'))
    listing=Counter(record['path'] for record in catalog['records'] if record.get('path')!='/')
    # Home has zero anchors: #explore is a scroll button (Governor 16:46), stricter than one #explore.
    # Library and publication listings are still the anchors render_site.py emits.
    # Every other page, including mechanism.html, has an empty anchor set.
    expected_anchors={
        'library/index.html':listing,
        'publication/index.html':listing,
    }
    for p,d in docs.items():
        for tag,attrs in d.tags:
            if tag=='area' and attrs.get('href') is not None:errors.append(f'Unexpected anchor area: {p} -> {attrs.get("href")}')
            if 'data-href' in attrs:errors.append(f'Unexpected anchor data-href: {p} -> {attrs.get("data-href")}')
        got=Counter(d.anchors)
        exp=expected_anchors.get(p, Counter())
        if got!=exp:errors.append(f'Unexpected anchor set: {p} expected {dict(exp)} got {dict(got)}')
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
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        root=Path(args.root) if args.root else Path(temp)/'site'
        if not args.root:build(root)
        check(root)
        if args.live:live(root,args.live,args.attempts,args.delay)