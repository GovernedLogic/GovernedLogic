#!/usr/bin/env python3
"""v13 parity check (Paul's v13 approval, Nov 1 2026, 12:30 PM ET; Paul's parity rule: no hidden text, every machine
string identical to visible text). Usage: python3 scripts/check-parity.py <built site>. Exit 1 on any mismatch.

Checks the built artifact against content/terms.py (the one source per term):
  1. terms.jsonld and the term lines of llms.txt are exactly what the source generates;
  2. every term: its fragment id exists on its page, its <dfn> wraps the source's words inside the visible definition
     (concept pages: <dfn id="concept">), its definition is visible on its page, its name on its page or /concepts/;
  3. every name/description/text/headline-like string in every JSON-LD block (and in terms.jsonld) is visible on the
     page it describes; termCode is an identifier and must equal the slug of its own URI;
  3b. every same-site URL in JSON-LD (@id, url, item, citation, image, ...) resolves to a published file, and its
     fragment is an id on that page (Governor's 2:01 PM ET ruling (a): nothing points at a missing anchor);
  3c. every <meta name=description>, og:description and twitter:description is visible on its page and equals the
     page's JSON-LD description where it has one (Governor's 2:01 PM ET ruling (c));
  4. llms.txt: every link resolves to a published, non-withheld file, and its label and text are visible there;
  5. ScholarlyArticle on /sources/: name, author and date line visible in its own section, which links its file;
  6. no page dates anywhere (sitemap lastmod, gl-date-* meta, dated gl-approval* meta, visible "Published / modified",
     dated "Canonical website checklist" line, JSON-LD dates), except the
     /sources/ ScholarlyArticle edition dates, which must equal the visible edition dates; edition dates still shown on
     /sources/, /library/ and /publication/ (Paul 4:50 PM ET Nov 1, no page dates, source editions kept);
  7. v14 social tags (Paul 2026-11-01 22:34; WEB-070 parity), on every page but /page-two/ (kept exactly as it was):
     og:title is the page's visible h1 (the homepage: its brand name), og:url its canonical URL, og:image an absolute
     URL of a published 1200x627 PNG whose Title text chunk (the only words drawn on it) equals og:title,
     twitter:card summary_large_image, no twitter:title/description that is not visible, no date in any og/twitter tag;
     the two articles carry Article JSON-LD whose headline and name are the h1 and whose image is the og:image;
     /articles/ lists each live article by its own h1, card art and first paragraph, once each;
  7b. v14.1 (Vera's nits b, c): og:description is each page's visible lede (its meta description) verbatim, absent only
     on pages with no lede (/faq/, /articles/); twitter:title, twitter:description and twitter:image equal og;
  7c. v14.1 (Vera's nit d): each RSS item's description is its page's visible lede verbatim.
Comparison folds typographic quotes, dashes and whitespace only (keywords also fold case: they are tags); it
reports and never rewrites.

No allowlist (Paul's parity rule, Nov 1 2026; Governor's 1:51 PM ET relay): any JSON-LD name, description, text,
headline-like string or keyword not visible on its own page fails, including strings that predate v13.
Identifiers, URLs and dates are not text claims and are not compared here (dates: see the v13 report).
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json, re, sys
from html import unescape
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import render_site as R
INLINE={'a','abbr','b','cite','code','dfn','em','i','q','small','span','strong','sub','sup','time','wbr'}
PAGE_TYPES={'WebPage','WebSite','CollectionPage','AboutPage','FAQPage','ProfilePage','Article','BlogPosting','ScholarlyArticle'}
KEYS={'name','description','text','headline','alternateName','abstract','caption','alternativeHeadline','disambiguatingDescription','slogan','version','jobTitle'}
def norm(x):
    for a,b in (('\u2019',"'"),('\u2018',"'"),('\u201c','"'),('\u201d','"'),('\u2014','-'),('\u2013','-'),('\u00a0',' ')):x=x.replace(a,b)
    return re.sub(r'\s+',' ',x).strip()
class Page(HTMLParser):
    def __init__(self,source):
        super().__init__();self.text=[];self.skip=0;self.inld=False;self.ld=[];self.ids=set();self.dfn=[];self.stack=[];self.sections={};self.hrefs={};self.meta=[]
        self.feed(source);self.close()
    def gap(self,tag):
        if tag not in INLINE and not self.skip:self.text.append(' ');[s['text'].append(' ') for s in self.stack]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.gap(tag)
        if tag=='meta' and (a.get('name') or a.get('property') or '').lower() in ('description','og:description','twitter:description'):
            self.meta.append(((a.get('name') or a.get('property')).lower(),a.get('content') or ''))
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
            elif k=='keywords':out+=[('keywords',x) for x in (v if isinstance(v,list) else [v]) if isinstance(x,str)]
            elif k=='termCode':out.append(('termCode',v,o.get('@id')))
            else:strings(v,out)
    elif isinstance(o,list):
        for v in o:strings(v,out)
def target(url):
    u=urlsplit(url)
    if u.netloc!=urlsplit(R.BASE).netloc:return None
    t=u.path.lstrip('/');return t+'index.html' if (t.endswith('/') or not t) else t
def main(root):
    root=Path(root);errors=[]
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
                if k=='keywords':
                    if norm(v).lower() not in pg.visible.lower():errors.append(f'JSON-LD keyword not visible on {name}: {v}')
                    continue
                if norm(v) not in pg.visible:errors.append(f'JSON-LD {k} not visible on {name}: {v[:120]}')
    tj=json.loads((root/'terms.jsonld').read_text(encoding='utf-8'))
    if tj['name'] not in pages[R.TERMS.SET_PAGE].visible:errors.append('terms.jsonld set name not visible on /concepts/')
    for node in tj['hasDefinedTerm']:
        page=next(t['page'] for t in terms if t['id']==node['@id'])
        if norm(node['description']) not in pages[page].visible:errors.append('terms.jsonld description not visible: '+node['@id'])
    # 3b. Governor's 2:01 PM ET ruling (a): every same-site URL in JSON-LD (@id, url, item, citation, image, ...)
    # resolves to a published file, and its fragment, if any, is an id on that page. Nothing points at a missing anchor.
    def urls(o,out):
        if isinstance(o,dict):
            for k,v in o.items():
                if k!='@context':urls(v,out)
        elif isinstance(o,list):
            for v in o:urls(v,out)
        elif isinstance(o,str) and o.startswith(R.BASE):out.append(o)
    sources=[(name,json.loads(b)) for name,pg in sorted(pages.items()) for b in pg.ld]+[('terms.jsonld',tj)]
    for name,data in sources:
        found=[];urls(data,found)
        for u in sorted(set(found)):
            t=target(u);frag=urlsplit(u).fragment
            if t is None or not (root/t).is_file():errors.append(f'JSON-LD URL on {name} does not resolve: {u}');continue
            if frag and (t not in pages or frag not in pages[t].ids):errors.append(f'JSON-LD URL on {name} points at a missing anchor: {u}')
    # 3c. Governor's 2:01 PM ET ruling (c): meta, og and twitter descriptions are machine claims too. Each must be
    # visible on its page and, where the page has a page-level JSON-LD description, be that same text.
    for name,pg in sorted(pages.items()):
        url=R.BASE+R.route(name)
        own=[]
        def page_desc(o):
            if isinstance(o,dict):
                if o.get('url')==url and isinstance(o.get('description'),str) and o.get('@type') in PAGE_TYPES:own.append(o['description'])
                for v in o.values():page_desc(v)
            elif isinstance(o,list):
                for v in o:page_desc(v)
        for b in pg.ld:page_desc(json.loads(b))
        for kind,text in pg.meta:
            if norm(text) not in pg.visible:errors.append(f'{kind} not visible on {name}: {text[:120]}')
            elif own and norm(text)!=norm(own[0]):errors.append(f'{kind} differs from the JSON-LD description on {name}: {text[:80]}')
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
    # 6. No page dates; source edition dates kept (Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via
    # QA/Governor, verified)). No sitemap lastmod, no gl-date-* meta, no visible "Published / modified" line, and no
    # JSON-LD date on any node except the /sources/ ScholarlyArticle editions, whose datePublished must be their visible
    # edition date. The edition dates on /sources/, /library/ and /publication/ must still be shown.
    sm=(root/'sitemap.xml').read_text(encoding='utf-8')
    locs=re.findall(r'<loc>([^<]+)</loc>',sm)
    mods=re.findall(r'<lastmod>([^<]*)</lastmod>',sm)
    # Paul 2026-11-11: one release lastmod on every public URL. Visible page dates stay forbidden.
    if len(locs)!=len(mods) or any(m!=R.SITEMAP_LASTMOD for m in mods):errors.append('sitemap lastmod must be '+R.SITEMAP_LASTMOD+' on every public URL')
    DATE_KEYS=('datePublished','dateModified','dateCreated','uploadDate')
    PAGE_DATE=re.compile(r'(?:\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}|\d{4}-\d\d-\d\d)')
    editions={R.BASE+'/sources/#'+d['section']:d['date'] for d in R.TERMS.SOURCE_DOCS}
    for name,pg in sorted(pages.items()):
        if re.search(r'Published\s*/\s*modified',pg.visible,re.I):errors.append(f'Visible page date line on {name} (no page dates)')
        raw=(root/name).read_text(encoding='utf-8')
        for m in re.finditer(r'<meta\s+name="gl-date-[^"]*"',raw):errors.append(f'gl-date meta on {name} (no page dates)')
        # Paul 5:29 PM ET Nov 1 (via QA/Governor, verified): no approval date in gl-approval* meta, and no dated
        # "Canonical website checklist" line.
        for m in re.finditer(r'<meta\s+name="(gl-approval[^"]*)"\s+content="([^"]*)"',raw):
            if PAGE_DATE.search(m.group(2)):errors.append(f'Dated {m.group(1)} meta on {name} (no page dates)')
        if re.search(r'Canonical website checklist\s*·\s*'+PAGE_DATE.pattern,pg.visible):errors.append(f'Dated checklist line on {name} (no page dates)')
        for b in pg.ld:
            stack=[json.loads(b)]
            while stack:
                n=stack.pop()
                if isinstance(n,list):stack+=n;continue
                if not isinstance(n,dict):continue
                stack+=list(n.values())
                for k in DATE_KEYS:
                    if k not in n:continue
                    if name=='sources/index.html' and n.get('@type')=='ScholarlyArticle' and k=='datePublished' and editions.get(n.get('@id'))==n[k]:continue
                    errors.append(f'JSON-LD {k} on {name} ({n.get("@type")} {n.get("@id","")}): no page dates')
    found={n.get('@id'):n.get('datePublished') for b in pages['sources/index.html'].ld for n in (lambda d:d.get('@graph',[d]))(json.loads(b)) if isinstance(n,dict) and n.get('@type')=='ScholarlyArticle'}
    for i,d in editions.items():
        if found.get(i)!=d:errors.append(f'Source edition date missing from JSON-LD: {i} {d}')
    for name in ('library/index.html','publication/index.html'):
        for title in R.SOURCE_TITLES:
            if norm(title+' · September 2026') not in pages[name].visible:errors.append(f'Edition date not shown on {name}: {title} · September 2026')
    if norm('The source documents retain their original September 2026 edition dates.') not in pages['publication/index.html'].visible:errors.append('Edition-date sentence missing on publication/index.html')
    # 7. v14 social tags.
    import struct,zlib
    def png_info(path):
        # Stdlib PNG reader (no Pillow on the CI runner): format, size, text chunks.
        b=path.read_bytes()
        if b[:8]!=b'\x89PNG\r\n\x1a\n':return None,None,{}
        i=8;size=None;text={}
        while i+8<=len(b):
            ln,typ=struct.unpack('>I4s',b[i:i+8]);d=b[i+8:i+8+ln];i+=12+ln
            if typ==b'IHDR':size=struct.unpack('>II',d[:8])
            elif typ==b'tEXt':k,_,v=d.partition(b'\0');text[k.decode('latin-1')]=v.decode('latin-1')
            elif typ==b'zTXt':k,_,v=d.partition(b'\0');text[k.decode('latin-1')]=zlib.decompress(v[1:]).decode('latin-1')
            elif typ==b'iTXt':
                k,_,r=d.partition(b'\0');cf,cm=r[0],r[1];r=r[2:];_,_,r=r.partition(b'\0');_,_,r=r.partition(b'\0')
                text[k.decode('latin-1')]=(zlib.decompress(r) if cf else r).decode('utf-8')
            elif typ==b'IEND':break
        return 'PNG',size,text
    import site_layout as L
    raw_pages={p.relative_to(root).as_posix():p.read_text(encoding='utf-8') for p in root.rglob('*.html')}
    def metas(raw):
        out={}
        for m in re.finditer(r'<meta\s+(?:property|name)="((?:og|twitter):[^"]+)"\s+content="([^"]*)"',raw):out.setdefault(m.group(1),[]).append(unescape(m.group(2)))
        return out
    NO_LEDE=('faq/index.html','articles/index.html')
    ogd={}
    for name,raw in sorted(raw_pages.items()):
        if name=='page-two/index.html':continue
        mt=metas(raw);h1=L.h1_text(raw) if name!='index.html' else 'Governed Logic Reasoning Systems'
        canon=re.search(r'<link rel="canonical" href="([^"]+)"',raw)
        for k in ('og:title','og:url','og:image','og:type','twitter:card'):
            if len(mt.get(k,[]))!=1:errors.append(f'{k} on {name}: expected exactly one, found {len(mt.get(k,[]))}')
        if mt.get('og:title',[None])[0]!=h1:errors.append(f'og:title on {name} is not its visible h1: {mt.get("og:title")} vs {h1!r}')
        if not canon or mt.get('og:url',[None])[0]!=canon.group(1):errors.append(f'og:url on {name} is not its canonical URL')
        if mt.get('twitter:card',[None])[0]!='summary_large_image':errors.append(f'twitter:card on {name} is not summary_large_image')
        for k in ('twitter:title','twitter:description','og:image:alt'):
            for v in mt.get(k,[]):
                if norm(v) not in pages[name].visible:errors.append(f'{k} not visible on {name}: {v[:80]}')
        for k,vs in mt.items():
            for v in vs:
                if PAGE_DATE.search(v) or re.search(r'\b20\d\d-\d\d-\d\d\b',v):errors.append(f'Date in {k} on {name} (no page dates)')
        # 7b. v14.1 (Vera's nits b, c): og:description is the page's existing visible lede, verbatim: its meta description
        # (visible per 3c). Only pages with no lede (NO_LEDE) carry none. twitter:title, twitter:description and
        # twitter:image are exactly og:title, og:description and og:image.
        md=[unescape(m) for m in re.findall(r'<meta name="description" content="([^"]*)"',raw)]
        if md:
            if mt.get('og:description')!=md[:1]:errors.append(f'og:description on {name} is not its visible lede (meta description): {mt.get("og:description")}')
        elif name not in NO_LEDE:errors.append(f'{name} has no visible lede for og:description (not in NO_LEDE)')
        elif 'og:description' in mt:errors.append(f'og:description on {name}, which has no visible lede')
        for t,o in (('twitter:title','og:title'),('twitter:description','og:description'),('twitter:image','og:image')):
            if mt.get(t,[])!=mt.get(o,[]):errors.append(f'{t} on {name} is not its {o}: {mt.get(t)} vs {mt.get(o)}')
        ogd[R.BASE+R.route(name)]=(mt.get('og:description') or [None])[0]
        img=mt.get('og:image',[''])[0]
        if not img.startswith(R.BASE+'/'):errors.append(f'og:image on {name} is not an absolute {R.BASE} URL: {img}');continue
        f=root/img[len(R.BASE)+1:]
        if not f.is_file():errors.append(f'og:image on {name} is not published: {img}');continue
        fmt,size,text=png_info(f)
        if fmt!='PNG' or size!=(1200,627):errors.append(f'og:image on {name} is not a 1200x627 PNG: {fmt} {size}')
        if text.get('Title')!=h1:errors.append(f'og:image on {name} draws {text.get("Title")!r}, not its og:title {h1!r}')
    # 7c. v14.1 (Vera's nit d): each RSS item's description is its page's og:description (the visible lede), verbatim;
    # a page with no lede has an item without one.
    feed=(root/'feed.xml').read_text(encoding='utf-8')
    for m in re.finditer(r'<item>([\s\S]*?)</item>',feed):
        link=re.search(r'<link>([^<]*)</link>',m.group(1)).group(1);d=re.search(r'<description>([^<]*)</description>',m.group(1))
        d=unescape(d.group(1)) if d else None
        if link in ogd:
            if d!=ogd[link]:errors.append(f'feed.xml item {link}: description is not the page\'s visible lede: {d!r:.80}')
        elif d is not None:errors.append(f'feed.xml item {link}: description on an item that is not a page')
    # /articles/ lists each live article exactly once (Vera's nit a).
    idx_raw=raw_pages['articles/index.html']
    for a in L.ARTICLES:
        n=re.findall(r'<a href="([^"]+)"[^>]*\bgl-card-go\b',idx_raw).count(L.route(a))
        if n!=1:errors.append(f'/articles/ lists {a} {n} times (expected once)')
    for a in L.ARTICLES:
        raw=raw_pages[a];h1=L.h1_text(raw)
        arts=[n for blk in re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>',raw) for n in [json.loads(blk)] if n.get('@type')=='Article']
        if len(arts)!=1:errors.append(f'Article JSON-LD on {a}: expected one, found {len(arts)}');continue
        n=arts[0]
        if n.get('headline')!=h1 or n.get('name')!=h1:errors.append(f'Article headline/name on {a} is not its h1')
        if n.get('image')!=metas(raw).get('og:image',[None])[0]:errors.append(f'Article image on {a} is not its og:image')
        if any(k.startswith('date') for k in n):errors.append(f'Article JSON-LD on {a} carries a date (no page dates)')
        idx=pages['articles/index.html'].visible
        if norm(h1) not in idx:errors.append(f'/articles/ does not list {a} by its h1')
        lede=re.search(r'<p>([\s\S]*?)</p>',raw[raw.find('</div>',raw.find('<div class="gl-intro"')):]).group(1)
        if norm(unescape(re.sub(r'<[^>]+>','',lede))) not in idx:errors.append(f'/articles/ card for {a} does not carry its first paragraph verbatim')
    print(f'Parity: {len(terms)} terms, {len(pages)} pages, no allowlist')
    if errors:print('PARITY FAILED:\n'+'\n'.join('  '+e for e in errors));return 1
    print('Parity OK');return 0
if __name__=='__main__':sys.exit(main(sys.argv[1] if len(sys.argv)>1 else 'dist'))
