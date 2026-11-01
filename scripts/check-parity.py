#!/usr/bin/env python3
"""v13 parity check (Paul's v13 approval, Nov 1 2026, 12:30 PM ET; Paul's parity rule: no hidden text, every machine
string identical to visible text). Usage: python3 scripts/check-parity.py <built site>. Exit 1 on any mismatch.

Checks the built artifact against content/terms.py (the one source per term):
  1. terms.jsonld and the term lines of llms.txt are exactly what the source generates;
  2. every term: its fragment id exists on its page, its <dfn> wraps the source's words inside the visible definition
     (concept pages: <dfn id="concept">), its definition is visible on its page, its name on its page or /concepts/;
  3. every name/description/text/headline-like string in every JSON-LD block (and in terms.jsonld) is visible on the
     page it describes; termCode is an identifier and must equal the slug of its own URI;
  4. llms.txt: every link resolves to a published, non-withheld file, and its label and text are visible there;
  5. ScholarlyArticle on /sources/: name, author and date line visible in its own section, which links its file;
  6. sitemap lastmod equals the page's own dateModified.
Comparison folds typographic quotes, dashes and whitespace only; it reports and never rewrites.

BASELINE pins the JSON-LD strings that already differed from the visible text at 187fdb4 (before v13; none of them is
in a machine surface v13 adds). They are reported on every run and await Paul's ruling; any new or changed mismatch
fails, and so does a pinned entry that no longer occurs (remove it from BASELINE when it is resolved).
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import hashlib, json, re, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import render_site as R
BASELINE={}  # Emptied: all 14 pre-existing mismatches are aligned to the visible text (Paul's parity rule, Nov 1 2026; Governor 1:51 PM ET relay).
INLINE={'a','abbr','b','cite','code','dfn','em','i','q','small','span','strong','sub','sup','time','wbr'}
KEYS={'name','description','text','headline','alternateName','abstract','caption','alternativeHeadline','disambiguatingDescription','slogan','version','jobTitle'}
def norm(x):
    for a,b in (('\u2019',"'"),('\u2018',"'"),('\u201c','"'),('\u201d','"'),('\u2014','-'),('\u2013','-'),('\u00a0',' ')):x=x.replace(a,b)
    return re.sub(r'\s+',' ',x).strip()
class Page(HTMLParser):
    def __init__(self,source):
        super().__init__();self.text=[];self.skip=0;self.inld=False;self.ld=[];self.ids=set();self.dfn=[];self.stack=[];self.sections={};self.hrefs={}
        self.feed(source);self.close()
    def gap(self,tag):
        if tag not in INLINE and not self.skip:self.text.append(' ');[s['text'].append(' ') for s in self.stack]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.gap(tag)
        if a.get('id'):self.ids.add(a['id'])
        if tag in('script','style','template'):self.skip+=1;self.inld=a.get('type')=='application/ld+json';self.ld.append('') if self.inld else None
        if tag=='dfn':self.dfn.append({'id':a.get('id'),'text':'','context':self.stack[-1]['text'] if self.stack else None,'node':self.stack[-1] if self.stack else None})
        if tag not in R.VOID:self.stack.append({'tag':tag,'id':a.get('id'),'text':[]})
        if tag=='a':
            for s in self.stack:
                if s['id']:self.hrefs.setdefault(s['id'],[]).append(a.get('href'))
    def handle_endtag(self,tag):
        if tag in('script','style','template'):self.skip-=1;self.inld=False
        self.gap(tag)
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]['tag']==tag:
                for s in self.stack[i:]:
                    if s['id']:self.sections[s['id']]=norm(''.join(s['text']))
                del self.stack[i:];break
    def handle_data(self,x):
        if self.inld:self.ld[-1]+=x;return
        if self.skip:return
        self.text.append(x)
        for s in self.stack:s['text'].append(x)
        if self.dfn and self.stack and self.stack[-1]['tag']=='dfn':self.dfn[-1]['text']+=x
    @property
    def visible(self):return norm(''.join(self.text))
def strings(o,out,path=''):
    if isinstance(o,dict):
        for k,v in o.items():
            if k in KEYS and isinstance(v,str):out.append((k,v))
            elif k=='termCode':out.append(('termCode',v,o.get('@id')))
            else:strings(v,out)
    elif isinstance(o,list):
        for v in o:strings(v,out)
def pin(page,key,value):return hashlib.sha256(f'{page}\t{key}\t{value}'.encode()).hexdigest()[:16]
def target(url):
    u=urlsplit(url)
    if u.netloc!=urlsplit(R.BASE).netloc:return None
    t=u.path.lstrip('/');return t+'index.html' if (t.endswith('/') or not t) else t
def main(root):
    root=Path(root);errors=[];seen=set();report=[]
    pages={p.relative_to(root).as_posix():Page(p.read_text(encoding='utf-8')) for p in root.rglob('*.html')}
    terms=R.term_records()
    # 1. generated surfaces equal the source
    if (root/'terms.jsonld').read_text(encoding='utf-8')!=R.terms_jsonld():errors.append('terms.jsonld differs from content/terms.py')
    llms=(root/'llms.txt').read_text(encoding='utf-8')
    for t in terms:
        if f'- [{t["name"]}]({t["url"]}): {t["definition"]}\n' not in llms:errors.append('llms.txt term line differs from source: '+t['code'])
    codes=[t['code'] for t in terms];ids=[t['id'] for t in terms]
    if len(set(codes))!=len(codes) or len(set(ids))!=len(ids):errors.append('Duplicate term code or URI')
    # 2. terms on their pages
    for t in terms:
        pg=pages.get(t['page'])
        if pg is None:errors.append('Term page missing: '+t['page']);continue
        if t['fragment'] not in pg.ids:errors.append(f'Term URI does not resolve: {t["id"]}')
        if norm(t['definition']) not in pg.visible:errors.append(f'Definition not visible on {t["page"]}: {t["code"]}')
        if t['name'] not in pg.visible and t['name'] not in pages[R.TERMS.SET_PAGE].visible:errors.append(f'Name not visible: {t["name"]}')
        want='concept' if t['fragment']=='concept' else None
        d=[x for x in pg.dfn if x['text']==t['dfn'] and x['id']==want]
        if len(d)!=1:errors.append(f'<dfn> for {t["code"]} on {t["page"]}: expected exactly one, found {len(d)}')
    # 3. JSON-LD strings visible on their page
    for name,pg in sorted(pages.items()):
        for block in pg.ld:
            out=[];strings(json.loads(block),out)
            for item in out:
                if item[0]=='termCode':
                    code,uri=item[1],item[2]
                    t=next((x for x in terms if x['id']==uri),None)
                    if t is None or t['code']!=code or (t['fragment']!=code and not uri.endswith('/'+code+'/#concept')):errors.append(f'termCode {code!r} does not match its URI {uri} on {name}')
                    continue
                k,v=item
                if norm(v) in pg.visible:continue
                h=pin(name,k,v)
                if h in BASELINE:seen.add(h);report.append(f'  pinned (pre-existing, awaiting Paul): {name} {k}: {v[:90]}')
                else:errors.append(f'JSON-LD {k} not visible on {name} [{h}]: {v[:120]}')
    tj=json.loads((root/'terms.jsonld').read_text(encoding='utf-8'))
    if tj['name'] not in pages[R.TERMS.SET_PAGE].visible:errors.append('terms.jsonld set name not visible on /concepts/')
    for node in tj['hasDefinedTerm']:
        page=next(t['page'] for t in terms if t['id']==node['@id'])
        if norm(node['description']) not in pages[page].visible:errors.append('terms.jsonld description not visible: '+node['@id'])
    # 4. llms.txt links
    for label,url,text in re.findall(r'^- \[(.+?)\]\((\S+?)\)(?:: (.*))?$',llms,re.M):
        t=target(url)
        if t is None or not (root/t).is_file():errors.append('llms.txt link does not resolve: '+url);continue
        if t in R.WITHHELD_LINK_TARGETS or t in R.RETIRED_ASSETS or t not in R.PUBLIC_FILES:errors.append('llms.txt links a withheld or unpublished path: '+url);continue
        if t.endswith('.html'):
            if norm(label) not in pages[t].visible and not (text and any(x['name']==label for x in terms) and norm(label) in pages[R.TERMS.SET_PAGE].visible):errors.append(f'llms.txt label not visible on {t}: {label}')
            if text and norm(text) not in pages[t].visible:errors.append(f'llms.txt text not visible on {t}: {text[:80]}')
        elif not any(urlsplit(url).path in (h or '') for p in pages.values() for hs in p.hrefs.values() for h in hs):errors.append('llms.txt file not linked from any page: '+url)
    # 5. ScholarlyArticle
    src=pages['sources/index.html']
    for d in R.TERMS.SOURCE_DOCS:
        sec=src.sections.get(d['section'],'')
        for want in (d['name'],d['shown'],'Paul André Couchoud',d['file'].split('/')[-1]):
            if norm(want) not in sec:errors.append(f'ScholarlyArticle {d["section"]}: {want!r} not visible in its section')
        if '/'+d['file'] not in src.hrefs.get(d['section'],[]):errors.append(f'ScholarlyArticle {d["section"]}: section does not link {d["file"]}')
        if not (root/d['file']).is_file():errors.append('ScholarlyArticle file missing: '+d['file'])
    # 6. sitemap lastmod
    for loc,mod in re.findall(r'<url><loc>([^<]+)</loc>(?:<lastmod>([^<]+)</lastmod>)?</url>',(root/'sitemap.xml').read_text(encoding='utf-8')):
        t=target(loc)
        want=R.lastmod((root/t).read_text(encoding='utf-8'),loc) if (root/t).is_file() else None
        if (mod or None)!=want:errors.append(f'sitemap lastmod for {loc}: {mod!r}, page dateModified {want!r}')
    stale=set(BASELINE)-seen
    for h in sorted(stale):errors.append(f'Pinned baseline entry no longer occurs (resolved? remove it): {h} {BASELINE[h]}')
    print(f'Parity: {len(terms)} terms, {len(pages)} pages, {len(seen)} pinned pre-existing JSON-LD mismatches (awaiting Paul):')
    print('\n'.join(sorted(set(report))))
    if errors:print('PARITY FAILED:\n'+'\n'.join('  '+e for e in errors));return 1
    print('Parity OK');return 0
if __name__=='__main__':sys.exit(main(sys.argv[1] if len(sys.argv)>1 else 'dist'))
