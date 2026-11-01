"""Build a componentized public site from an explicit allowlist."""
from pathlib import Path
from html.parser import HTMLParser
from html import escape, unescape
import argparse, hashlib, json, re, shutil
ROOT=Path(__file__).resolve().parents[1]
PAGES=('index.html','challenge/index.html','company/index.html','research/index.html','about/index.html','faq/index.html','concepts/index.html','concepts/governed-logic/index.html','concepts/governed-intelligence/index.html','concepts/ultimate-grounding/index.html','concepts/alpha-and-omega-reasoning/index.html','concepts/governing-referent/index.html','concepts/sufficient-grounding/index.html','mechanism.html','sources/index.html','articles/why-anything/index.html','articles/integrity-in-artificial-intelligence/index.html','page-two/index.html')
SOURCE_FILES=('sources/01_Ultimate_Grounding_2026-09-22_172847_EDT.pdf','sources/02_Governed_Logic_2026-09-22_172847_EDT.pdf','sources/03_Alpha_and_Omega_Reasoning_2026-09-22_172847_EDT.pdf','sources/04_Governed_Intelligence_2026-09-22_172847_EDT.pdf','sources/GovernedLogic_Business_Strategy_Addendum_v1_2026-09-23.txt')
# v12 round 2 (QA L1; WEB-227 SIXTH): no longer published, because nothing in the built site loads them (the homepage
# dropped the Earth opening under C8/WEB-215 and the head art under Paul's Nov 1 hero ruling): assets/opening.css,
# assets/opening.js, assets/earth-renderer.js, assets/material-environment.js, assets/materials/earth-{clouds,day,night}.jpg,
# assets/materials/cinzel.ttf, assets/provisional/head-artwork.webp. The files stay in the repo. Kept: governed-logic-mark.webp
# (restored-site.css .reasoning-exhibit background), Cinzel-OFL.txt and SOURCES.txt (SOURCES.txt cites the licence).
RETIRED_ASSETS=('assets/opening.css', 'assets/opening.js', 'assets/earth-renderer.js', 'assets/material-environment.js', 'assets/materials/earth-clouds.jpg', 'assets/materials/earth-day.jpg', 'assets/materials/earth-night.jpg', 'assets/materials/cinzel.ttf', 'assets/provisional/head-artwork.webp')
# C1 reversed (Paul, Nov 1 2026, 12:31 PM ET): paths no published page may link to (with RETIRED_ASSETS and anything outside
# PUBLIC_FILES). Unpublished routes (e.g. principle pages awaiting Paul's approval) are added here until published.
WITHHELD_LINK_TARGETS=('GOVERNEDLOGIC_COM_PRD.txt','scripts/restore_content.py','components/header.html','recovery-provenance.json')
ASSETS=('assets/home-chime.js','assets/restored-site.css','assets/site.css','assets/library.js','assets/materials/Cinzel-OFL.txt','assets/materials/IBM-Plex-OFL.txt','assets/materials/ibm-plex-sans.ttf','assets/materials/SOURCES.txt','assets/governed-logic-mark.webp','assets/home.css','assets/materials/source-serif-4-latin-opsz.woff2','assets/materials/inter-latin-wght.woff2','assets/materials/SourceSerif4-OFL.txt','assets/materials/Inter-OFL.txt','assets/provisional/seed-of-life.png','assets/provisional/grain.png','assets/provisional/hero-geometry.svg','assets/provisional/card-grounding.webp','assets/provisional/card-mathematics.webp','assets/provisional/card-framework.webp','assets/provisional/problem-network.webp','assets/gl-reasoning-systems.webp','assets/the-groundless-machine.webp','paul-portrait.png')
GENERATED=('library/index.html','publication/index.html','publication/catalog.json','publication/search-index.json','publication/manifest.json','feed.xml','robots.txt','sitemap.xml')
PUBLIC_FILES=(*PAGES,*SOURCE_FILES,*ASSETS,'challenge/index.json','faq/index.json','CNAME','.nojekyll',*GENERATED)
BASE='https://governedlogic.com'
def route(path):return '/'+path[:-10] if path.endswith('index.html') else '/'+path
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0;self.main=False
    def handle_starttag(self,tag,attrs):
        if tag=='main':self.main=True
        if tag in ('script','style'):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip-=1
        if tag=='main':self.main=False
    def handle_data(self,data):
        if self.main and not self.skip:self.parts.append(data)
def main_text(source):
    p=Text();p.feed(source);return re.sub(r'\s+',' ',' '.join(p.parts)).strip()
def definitions(source):
    for key,value in json.loads((ROOT/'content/definitions.json').read_text(encoding='utf-8')).items():
        source=source.replace('{{definition:'+key+'}}',value)
    return source
VOID={'area','base','br','col','embed','hr','img','input','link','meta','source','track','wbr'}
class Spans(HTMLParser):
    """Start/end offsets of every element inside the first <main>, for intro_band()."""
    def __init__(self,source):
        super().__init__(convert_charrefs=False);self.src=source;self.lines=[0]
        for m in re.finditer('\n',source):self.lines.append(m.end())
        self.stack=[];self.items=[];self.feed(source);self.close()
    def at(self):l,c=self.getpos();return self.lines[l-1]+c
    def handle_starttag(self,tag,attrs):
        start=self.at();end=start+len(self.get_starttag_text())
        item={'tag':tag,'cls':dict(attrs).get('class') or '','start':start,'open_end':end,'end':end,'parent':self.stack[-1] if self.stack else None}
        self.items.append(item)
        if tag not in VOID:self.stack.append(item)
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.stack.pop() if tag not in VOID else None
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]['tag']==tag:
                item=self.stack[i];item['end']=self.at()+len(tag)+3;del self.stack[i:];return
def intro_band(source):
    """v12 round 2 (F4; WEB-227 SIXTH): wrap each page's title block (what precedes the h1 in its parent, the h1, and
    a directly following lede/lead paragraph) in <div class="gl-intro"> so site.css can set it on a dark band like the
    homepage hero. Markup only: no text, attribute or order change. Pages whose h1 already sits in a hero section
    (about-hero) or outside main (page-two) are left as they are; site.css styles those sections."""
    sp=Spans(source);main=next((i for i in sp.items if i['tag']=='main'),None)
    h1=next((i for i in sp.items if i['tag']=='h1' and main and main['start']<i['start']<main['end']),None)
    if not h1:return source
    a=h1['parent']
    while a is not None and a is not main:
        if re.search(r'\b(about-hero|front-door)\b',a['cls']):return source
        a=a['parent']
    parent=h1['parent'];kids=[i for i in sp.items if i['parent'] is parent]
    k=kids.index(h1);start=kids[0]['start'] if k else h1['start'];end=h1['end']
    if k+1<len(kids) and kids[k+1]['tag']=='p' and re.search(r'\b(lede|lead)\b',kids[k+1]['cls']):end=kids[k+1]['end']
    return source[:start]+'<div class="gl-intro">'+source[start:end]+'</div>'+source[end:]
# C1 reversed (Paul, Nov 1 2026, 12:31 PM ET: "Yes normal links so Google can follow them."): every GET-form button
# that navigated (<form class="gl-go" method="get" action=X><button type="submit">) is replaced, not supplemented, by an
# ordinary <a href=X>. The wrapper keeps class gl-go (as a span) and the link carries class gl-link plus the button's own
# classes and attributes, so the CSS that drew the buttons (button selectors now :is(button,:where(a.gl-link))) draws the links.
GO_FORM=re.compile(r'<form class="gl-go([^"]*)" method="get" action="([^"]*)"><button type="submit"([^>]*)>([\s\S]*?)</button></form>')
def links(source):
    def one(m):
        extra,href,attrs,inner=m.groups()
        cls=re.search(r'\sclass="([^"]*)"',attrs)
        attrs=re.sub(r'\sclass="[^"]*"','',attrs)
        return f'<span class="gl-go{extra}"><a href="{href}" class="gl-link{(" "+cls.group(1)) if cls else ""}"{attrs}>{inner}</a></span>'
    return GO_FORM.sub(one,source)
FONT_PRELOADS=''.join(f'<link rel="preload" href="/assets/materials/{font}" as="font" type="font/woff2" crossorigin>' for font in ('source-serif-4-latin-opsz.woff2','inter-latin-wght.woff2'))
def render(source,path):
    if path=='index.html':
        source=re.sub(r'<main\b[\s\S]*?</main>',lambda _: (ROOT/'content/home.html').read_text(encoding='utf-8').strip(),source,count=1)
    if path=='page-two/index.html':
        source=re.sub(r'<main\b[\s\S]*?</main>',lambda _: (ROOT/'content/page-two.html').read_text(encoding='utf-8').strip(),source,count=1)
    source=definitions(source)
    if path!='index.html':
        # v12 site-wide look (Paul, Nov 1 2026; WEB-227 SIXTH): every other page shares the homepage header, footer
        # and tokens (home.css, selectors :is(body.gl-home-page,body.gl-site)) plus site.css for page content. Style only.
        source=intro_band(source)
        # v12 round 2 (Q2; WEB-227 SIXTH): let the canonical URL in the Sources sidebar wrap after a slash instead of
        # mid-word. <wbr> adds a break opportunity only; the button text is unchanged.
        # v13: the URL is marked gl-url so it can be kept off its hyphens (white-space:nowrap; Chrome, Firefox and Safari
        # still break at <wbr>), since the narrower 390px column made "alpha-" a break point.
        source=re.sub(r'(<aside class="provenance">[\s\S]*?</aside>)',lambda m: re.sub(r'(<button type="submit">)(https://[^<]+)(</button>)',lambda b: '<button type="submit" class="gl-url">'+'https://<wbr>'+re.sub(r'/(?=.)','/<wbr>',b.group(2)[8:])+b.group(3),m.group(1)),source)
        source=re.sub(r'<body(?: class="([^"]*)")?>',lambda m:'<body class="'+((m.group(1)+' ') if m.group(1) else '')+'gl-site">',source,count=1)
        # v13 CLS (QA research 2026-11-01; Paul's v13 approval, Nov 1 2026, 12:30 PM ET): inner pages preload the two
        # text fonts as the homepage does, so text lays out once instead of reflowing when the fonts arrive.
        source=source.replace('</head>','<link rel="stylesheet" href="/assets/home.css"><link rel="stylesheet" href="/assets/site.css">'+FONT_PRELOADS+'</head>',1)
    for sheet in ('restored-site.css','home.css','site.css'):
        style_version=hashlib.sha256((ROOT/'assets'/sheet).read_bytes()).hexdigest()[:12]
        source=source.replace(f'href="/assets/{sheet}"',f'href="/assets/{sheet}?v={style_version}"')
    main=re.search(r'<main\b[^>]*\bid="([^"]+)"',source)
    anchor=main.group(1) if main else 'content'
    header=(ROOT/'components/header.html').read_text(encoding='utf-8').replace('href="#content"',f'href="#{anchor}"')
    if path=='index.html':header=re.sub(r'<header class="site-bar"[^>]*>[\s\S]*?</header>',lambda _: (ROOT/'components/home-bar.html').read_text(encoding='utf-8').strip(),header,count=1)
    current=route(path)
    if current!='/':header=header.replace(f'href="{current}"',f'href="{current}" aria-current="page"')
    footer=(ROOT/'components/footer.html').read_text(encoding='utf-8')
    if 'id="paul"' in source:footer=footer.replace(' id="paul"','')
    return links(source.replace('<!--SITE_HEADER-->',header).replace('<!--SITE_FOOTER-->',footer))
def document(title,path,body,extra=''):
    data={'@context':'https://schema.org','@type':'CollectionPage','name':title,'url':BASE+route(path),'isPartOf':{'@id':BASE+'/#website'}}
    source=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} | Governed Logic</title><meta name="description" content="Governed Logic source works, concepts, research, and publications by Paul André Couchoud."><link rel="canonical" href="{BASE+route(path)}"><meta name="robots" content="index,follow"><link rel="stylesheet" href="/assets/restored-site.css"><script type="application/ld+json">{json.dumps(data)}</script>{extra}</head><body><!--SITE_HEADER--><main class="document-main" id="content"><p class="eyebrow">GOVERNED LOGIC REASONING SYSTEMS</p><h1>{escape(title)}</h1>{body}</main><!--SITE_FOOTER--></body></html>'
    return render(source,path)
def validate_sources():
    for p in PUBLIC_FILES:
        if Path(p).is_absolute() or '..' in Path(p).parts:raise ValueError('Unsafe public path: '+p)
        if p not in GENERATED and (not (ROOT/p).is_file() or (ROOT/p).is_symlink()):raise ValueError('Missing or unsafe source: '+p)
def safe_destination(value):
    p=Path(value).resolve()
    if p in {ROOT,ROOT.parent,Path(p.anchor)} or p.is_relative_to(ROOT) or p.exists():raise ValueError('Output must be a new directory outside the source checkout')
    return p
def build(destination):
    validate_sources();destination.mkdir(parents=True)
    for p in PUBLIC_FILES:
        if p in GENERATED:continue
        target=destination/p;target.parent.mkdir(parents=True,exist_ok=True)
        if p in PAGES:target.write_text(render((ROOT/p).read_text(encoding='utf-8'),p),encoding='utf-8',newline='\n')
        elif p=='faq/index.json':target.write_text(definitions((ROOT/p).read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
        else:shutil.copy2(ROOT/p,target)
    records=[]
    for p in PAGES:
        source=(destination/p).read_text(encoding='utf-8');title=re.search(r'<h1[^>]*>(.*?)</h1>',source,re.S)
        title=unescape(re.sub('<[^>]+>','',title.group(1))).strip() if title else 'Governed Logic Reasoning Systems'
        if p=='index.html':title='Governed Logic Reasoning Systems'
        records.append({'id':BASE+route(p),'title':title,'url':BASE+route(p),'path':route(p),'type':'concept' if p.startswith('concepts/') else 'page','text':main_text(source),'sha256':hashlib.sha256((destination/p).read_bytes()).hexdigest()})
    titles=['On the Nature of Ultimate Grounding','Governed Logic','Alpha and Omega Reasoning','Governed Intelligence','Business strategy — additional direction']
    for p,title in zip(SOURCE_FILES,titles):records.append({'id':BASE+'/'+p,'title':title+' · Source edition','url':BASE+'/'+p,'path':'/'+p,'type':'source','text':title+' · September 2026','sha256':hashlib.sha256((destination/p).read_bytes()).hexdigest()})
    entries=''.join(f'<article class="library-item" data-record="{r["id"]}" data-kind="{r["type"]}"><span class="eyebrow">{r["type"]}</span><h2 style="font-size:27px"><form class="gl-go" method="get" action="{r["path"]}"><button type="submit">{escape(r["title"])} →</button></form></h2><p>{escape(r["text"][:200])}…</p></article>' for r in records if r['path']!='/')
    form='<p class="lede">Explore the reasoning architecture, the research, and the original source editions.</p><form class="library-search" role="search" action="/library/"><div class="library-query"><label for="library-query">Search the library</label><input id="library-query" name="q" type="search" placeholder="A concept, title, or phrase" aria-controls="library-results"></div><div><label for="library-kind">Show</label><select id="library-kind" name="type"><option value="">All works</option><option value="concept">Concepts</option><option value="page">Pages &amp; articles</option><option value="source">Source editions</option></select></div><button id="library-clear" type="button" hidden>Clear</button></form><p id="library-search-mode">All works are available below.</p><p id="library-count" role="status"></p><p id="library-empty" hidden>No matching works. Try a different term.</p>'
    generated={'library/index.html':document('The library','library/index.html',form+'<div id="library-results">'+entries+'</div>','<script src="/assets/library.js" defer></script>'),
    'publication/index.html':document('Publication record','publication/index.html','<p class="lede">Source editions and the works they support.</p><p>The source documents retain their original September 2026 edition dates. The October 2026 articles remain separately identifiable.</p>'+entries),
    'publication/catalog.json':json.dumps({'records':records},ensure_ascii=False,indent=2),'publication/search-index.json':json.dumps({'records':records},ensure_ascii=False),
    'robots.txt':'User-agent: *\nAllow: /\nSitemap: '+BASE+'/sitemap.xml\n',
    'sitemap.xml':'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+BASE+route(p)+'</loc></url>' for p in (*PAGES,'library/index.html','publication/index.html'))+'</urlset>',
    'feed.xml':'<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Governed Logic publications</title><id>'+BASE+'/</id><updated>2026-10-18T00:00:00Z</updated>'+''.join('<entry><title>'+escape(r['title'])+'</title><id>'+r['id']+'</id><link href="'+r['url']+'"/><updated>2026-10-18T00:00:00Z</updated></entry>' for r in records)+'</feed>'}
    for p,value in generated.items():
        target=destination/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(value,encoding='utf-8',newline='\n')
    manifest={'release':'2026-10-18-substantive-restoration','files':{p:hashlib.sha256((destination/p).read_bytes()).hexdigest() for p in PUBLIC_FILES if p!='publication/manifest.json'}}
    (destination/'publication/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    actual={p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()}
    if actual!=set(PUBLIC_FILES):raise ValueError('Artifact differs from explicit allowlist')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args();dest=safe_destination(args.output);build(dest);print(f'Built {len(PUBLIC_FILES)} files, {len(PAGES)+2} substantive routes: {dest}')
if __name__=='__main__':main()
