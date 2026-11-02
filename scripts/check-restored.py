"""Check substantive content, navigation, artifacts, and deployed bytes."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from concurrent.futures import ThreadPoolExecutor
import argparse,hashlib,json,re,tempfile,time
from site_layout import TWP_URL
from render_site import PRINCIPLES,ROOT,PAGES,PUBLIC_FILES,ASSETS,RETIRED_ASSETS,WITHHELD_LINK_TARGETS,SOURCE_FILES,build,route,main_text,BASE
V14_PAGES=('articles/index.html','the-truth-with-paul/index.html')
TWP='the-truth-with-paul/index.html'
TWP_COPY=('The Truth with Paul','Coming soon','Subscribe on YouTube')
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
    # v14 (Paul 2026-11-01 22:34 and 22:36): /articles/ and /the-truth-with-paul/ are checked as pages too.
    for p in (*PAGES,'library/index.html','publication/index.html',*V14_PAGES):
        source=(root/p).read_text(encoding='utf-8');d=Doc();d.feed(source);docs[p]=d
        if d.canonical!=[BASE+route(p)]:errors.append('Canonical mismatch: '+p)
        if sum(t=='main' for t,a in d.tags)!=1:errors.append('Main landmark count: '+p)
        if sum(t=='h1' for t,a in d.tags)!=1:errors.append('H1 count: '+p)
        if not any(t=='nav' and a.get('aria-label')=='Primary' for t,a in d.tags):errors.append('Missing primary navigation: '+p)
        if not d.json:errors.append('Missing machine data: '+p)
        if len(d.ids)!=len(set(d.ids)):errors.append('Duplicate IDs: '+p+' '+str([i for i in set(d.ids) if d.ids.count(i)>1]))
        if p==TWP:
            # The Truth with Paul placeholder (Paul 2026-11-01 22:36): exactly its three strings, the h1 the channel name,
            # and the Subscribe button a plain link to the channel.
            if main_text(source)!=' '.join(TWP_COPY):errors.append('The Truth with Paul copy is not exactly its three strings: '+repr(main_text(source)))
            if [re.sub('<[^>]+>','',x).strip() for x in re.findall(r'<h1[^>]*>([\s\S]*?)</h1>',source)]!=[TWP_COPY[0]]:errors.append('The Truth with Paul h1 is not the channel name')
            if not re.search(r'<a href="'+re.escape(TWP_URL)+r'"[^>]*>Subscribe on YouTube<',source):errors.append('Subscribe on YouTube is not a plain link to '+TWP_URL)
        elif p=='articles/index.html':
            # v14.1 (Vera's nit a): the index is a featured card plus the Latest rail, each live article once; its words
            # are the articles' own titles and ledes, so it has no 45-word floor.
            cards=re.findall(r'<h3 id="gl-(?:art-featured|rail-\d+)">([^<]*)</h3>',source)
            if len(cards)<1 or len(cards)!=len(set(cards)):errors.append('Articles index does not list each article exactly once: '+repr(cards))
        elif len(main_text(source).split())<45:errors.append('Insufficient page content: '+p)
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
    # C1 reversed (Paul, Nov 1 2026, 12:31 PM ET: "Yes normal links so Google can follow them."). Was: no page may
    # contain an anchor. Now link coverage: navigation is <a href> only (no GET-form navigation left), every internal
    # href resolves to a published file (the Broken link/asset check above), nothing links to a withheld, unpublished
    # or retired path, and every published page is linked from at least one other page (no orphans).
    published_pages={route(p) for p in docs}
    inbound={r:set() for r in published_pages}
    for p,d in docs.items():
        for tag,attrs in d.tags:
            if tag=='form' and 'gl-go' in (attrs.get('class') or '').split():errors.append('GET-form navigation remains (C1 reversed): '+p)
            if tag=='area' and attrs.get('href') is not None:errors.append(f'Unexpected anchor area: {p} -> {attrs.get("href")}')
            if 'data-href' in attrs:errors.append(f'Unexpected anchor data-href: {p} -> {attrs.get("data-href")}')
        for href in d.anchors:
            u=urlsplit(urljoin(BASE+route(p),href))
            if u.scheme not in ('http','https'):errors.append(f'Unexpected link scheme: {p} -> {href}');continue
            if u.netloc!=urlsplit(BASE).netloc:continue
            target=unquote(u.path.lstrip('/'))
            if target.endswith('/') or not target:target+='index.html'
            if target not in PUBLIC_FILES or target in RETIRED_ASSETS or target in WITHHELD_LINK_TARGETS:errors.append(f'Link to an unpublished or withheld path: {p} -> {href}')
            r=route(target) if target.endswith('.html') else None
            if r in inbound and r!=route(p):inbound[r].add(route(p))
    for r,src in sorted(inbound.items()):
        if r!='/' and not src:errors.append('Orphan page (no inbound link): '+r)
    faq=json.loads((root/'faq/index.json').read_text(encoding='utf-8'))
    visible=main_text((root/'faq/index.html').read_text(encoding='utf-8'))
    for q in faq['mainEntity']:
        if q['name'] not in visible or q['acceptedAnswer']['text'] not in visible:errors.append('FAQ human/machine mismatch')
    for p in SOURCE_FILES:
        if (root/p).read_bytes()!=(ROOT/p).read_bytes():errors.append('Source edition altered: '+p)
    # v12 round 2 (QA L1): the opening assets are no longer published (render_site.RETIRED_ASSETS); one reappearing in
    # the artifact fails here as well as on the boundary check above. Was: each opening asset byte-equal to source.
    for p in RETIRED_ASSETS:
        if (root/p).exists():errors.append('Retired asset published: '+p)
    # Principle pages (Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified)): each published page
    # has its canonical, one main, one h1 equal to the principle's name, a sitemap entry, and at least one ordinary
    # <a href> link from another page; no other /principles/ page exists (Truth is withheld, see live()).
    principle_routes=PRINCIPLES.routes()
    for p in sorted(x for x in actual if x.startswith('principles/') and x not in principle_routes):errors.append('Unpublished principle page in the artifact: '+p)
    sitemap=(root/'sitemap.xml').read_text(encoding='utf-8')
    for p in V14_PAGES:
        if '<loc>'+BASE+route(p)+'</loc>' not in sitemap:errors.append('Page missing from sitemap: '+p)
    if 'href="/the-truth-with-paul/"' not in (root/'index.html').read_text(encoding='utf-8').split('</header>')[0]:errors.append('The Truth with Paul is not in the header nav')
    linked={}
    for path in sorted(root.rglob('*.html')):
        d=Doc();d.feed(path.read_text(encoding='utf-8'));rel=path.relative_to(root).as_posix()
        for href in d.anchors:
            u=urlsplit(urljoin(BASE+route(rel),href))
            if u.netloc==urlsplit(BASE).netloc and u.path.startswith('/principles/'):linked.setdefault(u.path.lstrip('/')+('index.html' if u.path.endswith('/') else ''),set()).add(rel)
    for p in principle_routes:
        if not (root/p).is_file():errors.append('Principle page missing: '+p);continue
        source=(root/p).read_text(encoding='utf-8');d=Doc();d.feed(source)
        if d.canonical!=[BASE+route(p)]:errors.append('Canonical mismatch: '+p)
        if sum(t=='main' for t,a in d.tags)!=1:errors.append('Main landmark count: '+p)
        h1=re.findall(r'<h1[^>]*>([\s\S]*?)</h1>',source)
        if [re.sub('<[^>]+>','',x).strip() for x in h1]!=[PRINCIPLES.NAMES[p.split('/')[1]]]:errors.append('Principle h1 is not exactly its name: '+p)
        if '<loc>'+BASE+route(p)+'</loc>' not in sitemap:errors.append('Principle page missing from sitemap: '+p)
        if not (linked.get(p,set())-{p}):errors.append('Principle page not linked from another page: '+p)
    if errors:raise AssertionError('\n'.join(sorted(set(errors))))
    print(f'Principle pages: {len(principle_routes)} published, each linked and in the sitemap; withheld: '+', '.join(t for t in WITHHELD_LINK_TARGETS if t.startswith('principles/')))
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
        # QA v12-live-187fdb4 G1 (WEB-227 SIXTH): the 9 retired files (QA v12-0347ff2 L1) must stay 404 live as well.
        # Governor 2:16 PM ET ruling (Nov 1 2026; GL QA F12): every withheld link target, including each unpublished
        # /principles/ route (as its file and as its directory URL), must be 404 live too.
        withheld=[*WITHHELD_LINK_TARGETS,*(t[:-len('index.html')] for t in WITHHELD_LINK_TARGETS if t.endswith('/index.html'))]
        for p in dict.fromkeys((*withheld,*RETIRED_ASSETS)):
            try:
                with urlopen(base.rstrip('/')+'/'+p,timeout=15) as r:errors.append('Internal file exposed: '+p)
            except HTTPError as e:
                if e.code!=404:errors.append('Unexpected boundary status: '+p)
        # Published principle pages and the v14 pages must be served (200, built bytes) at their directory URL too.
        for p in (*PRINCIPLES.routes(),*V14_PAGES):
            try:
                with urlopen(Request(base.rstrip('/')+'/'+p[:-len('index.html')],headers={'Cache-Control':'no-cache'}),timeout=30) as r:
                    if r.read()!=(root/p).read_bytes():errors.append('Stale bytes: '+p[:-len('index.html')])
            except (HTTPError,URLError,TimeoutError) as e:errors.append(p[:-len('index.html')]+': '+str(e))
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