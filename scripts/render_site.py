"""Build a componentized public site from an explicit allowlist."""
from pathlib import Path
from html.parser import HTMLParser
from html import escape, unescape
import argparse, hashlib, json, re, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'content'))
import terms as TERMS, principles as PRINCIPLES
sys.path.insert(0,str(ROOT/'scripts'))
import site_layout as LAYOUT
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
WITHHELD_LINK_TARGETS=('GOVERNEDLOGIC_COM_PRD.txt','scripts/restore_content.py','components/header.html','recovery-provenance.json',*PRINCIPLES.withheld())
# Visual refresh, structural part: the homepage signature (home-signature.js and its stylesheet, homepage only) replaces
# the logo fly-up (home-chime.js, removed). home.css and site.css stay byte-identical because /page-two/ loads them.
ASSETS=('assets/home-signature.js','assets/home-signature.css','assets/restored-site.css','assets/site.css','assets/library.js','assets/materials/Cinzel-OFL.txt','assets/materials/IBM-Plex-OFL.txt','assets/materials/ibm-plex-sans.ttf','assets/materials/SOURCES.txt','assets/governed-logic-mark.webp','assets/home.css','assets/materials/source-serif-4-latin-opsz.woff2','assets/materials/inter-latin-wght.woff2','assets/materials/SourceSerif4-OFL.txt','assets/materials/Inter-OFL.txt','assets/provisional/seed-of-life.png','assets/provisional/grain.png','assets/provisional/hero-geometry.svg','assets/provisional/card-grounding.webp','assets/provisional/card-mathematics.webp','assets/provisional/card-framework.webp','assets/provisional/problem-network.webp','assets/gl-reasoning-systems.webp','assets/the-groundless-machine.webp','paul-portrait.png',
# v14.2 (Paul 2026-11-02 18:08 voice call): the homepage video band: the video (720p H.264/AAC, faststart) and its
# poster (the video's own 'You exist.' frame). v14.3 (Grace relay 8:42 AM Nov 3, Paul voice call): no caption file.
'assets/video/gl-home-explainer.mp4','assets/video/gl-home-explainer-poster.webp',
# v14 (Paul 2026-11-01 22:34 "Let's get this big push out."): the page-type layer and the og images (assets/og/, made by
# scripts/make_og.py from each page's art and visible h1).
'assets/v14.css','assets/v14.js',*sorted(f'assets/og/{p.name}' for p in (ROOT/'assets/og').glob('*.png')))
GENERATED=('library/index.html','publication/index.html','publication/catalog.json','publication/search-index.json','publication/manifest.json','feed.xml','robots.txt','sitemap.xml',
# v13 machine layer (Paul's v13 approval, Nov 1 2026, 12:30 PM ET; Paul's parity rule): generated from content/terms.py.
'terms.jsonld','llms.txt',
# Principle pages (Paul, Nov 1 2026, 12:31 PM ET: "I want a page for each individual principle"): routes come from the
# data list in content/principles.py and exist only while its PUBLISH flag is on (off: text on hold; Governor, Rigel).
*PRINCIPLES.routes(),
# v14: the articles index (QA option A) and The Truth with Paul placeholder (Paul 2026-11-01 22:36).
'articles/index.html','the-truth-with-paul/index.html')
PUBLIC_FILES=(*PAGES,*SOURCE_FILES,*ASSETS,'challenge/index.json','faq/index.json','CNAME','.nojekyll',*GENERATED)
BASE='https://governedlogic.com'
# The source editions' titles as the library and publication pages list them (with their September 2026 edition date).
SOURCE_TITLES=('On the Nature of Ultimate Grounding','Governed Logic','Alpha and Omega Reasoning','Governed Intelligence','Business strategy — additional direction')
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
        if re.search(r'\b(about-hero|front-door|gl-intro|gl-twp-hero)\b',a['cls']):return source
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
# v13 machine layer (Paul's v13 approval, Nov 1 2026, 12:30 PM ET; Paul's parity rule: no hidden text, every machine
# string identical to visible text). content/terms.py is the one source per term; from it this file prints the <dfn>
# markup, the additive JSON-LD, /terms.jsonld and /llms.txt. scripts/check-parity.py fails on any mismatch.
def term_records():
    out=TERMS.terms(json.loads((ROOT/'content/definitions.json').read_text(encoding='utf-8')))
    published=PRINCIPLES.links()
    for t in out:
        # A published principle page is linked as the term's subjectOf; the term URI and url stay on /concepts/,
        # where its definition is visible.
        if t['page']==TERMS.SET_PAGE and t['code'] in published:t['subject']=(BASE+published[t['code']][0],published[t['code']][1])
    return out
def dfn(source,path):
    """Wrap the term's words, inside the first occurrence of its definition in <main>, in <dfn>. Markup only: the
    rendered words do not change (site.css: dfn{font-style:inherit}). Concept pages give it id="concept", so the
    term URI .../#concept resolves on its existing page; principles already have their article ids on /concepts/."""
    for t in term_records():
        if t['page']!=path:continue
        start=source.index('<main');end=source.index('</main>',start)
        node=next((m for m in re.finditer(r'>([^<]+)',source[start:end]) if t['definition'][:40] in m.group(1)),None)
        if node is None:raise ValueError(f'Definition of {t["code"]} not found in <main> of {path}')
        i=start+node.start(1)+node.group(1).index(t['dfn'])
        tag='<dfn id="concept">' if t['fragment']=='concept' else '<dfn>'
        source=source[:i]+tag+t['dfn']+'</dfn>'+source[i+len(t['dfn']):]
    return source
def machine_block(path):
    """Additive JSON-LD (a second block; the page's existing block stays byte-identical): termCode on each term and,
    on /concepts/, the url of each principle; on /sources/, the four source PDFs as ScholarlyArticle with only what
    the page shows (heading, author line, date line, file)."""
    nodes=[]
    for t in term_records():
        if t['page']!=path:continue
        n={'@type':'DefinedTerm','@id':t['id'],'termCode':t['code']}
        if path==TERMS.SET_PAGE:n['url']=t['url']
        if t.get('subject'):n['subjectOf']={'@type':'WebPage','url':t['subject'][0],'name':t['subject'][1]}
        nodes.append(n)
    if path=='sources/index.html':
        for d in TERMS.SOURCE_DOCS:
            nodes.append({'@type':'ScholarlyArticle','@id':BASE+'/sources/#'+d['section'],'name':d['name'],'author':{'@id':BASE+'/about/#paul'},'datePublished':d['date'],'url':BASE+'/'+d['file'],'encodingFormat':'application/pdf','isPartOf':{'@id':BASE+'/sources/#page'}})
    if not nodes:return ''
    return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':nodes},ensure_ascii=False)+'</script>'
def terms_jsonld():
    return json.dumps({'@context':'https://schema.org','@type':'DefinedTermSet','@id':TERMS.SET_ID,'name':TERMS.SET_NAME,'url':BASE+'/concepts/',
        'hasDefinedTerm':[{'@type':'DefinedTerm','@id':t['id'],'termCode':t['code'],'name':t['name'],'description':t['definition'],'url':t['url'],'inDefinedTermSet':{'@id':TERMS.SET_ID},**({'subjectOf':{'@type':'WebPage','url':t['subject'][0],'name':t['subject'][1]}} if t.get('subject') else {})} for t in term_records()]},ensure_ascii=False,indent=2)+'\n'
def llms_txt(records):
    """llms.txt (llmstxt.org layout): the site title, the defined terms with their visible definitions, and the pages
    by their visible h1. Nothing here is not on the page it links to."""
    lines=['# Governed Logic Reasoning Systems','','## '+TERMS.SET_NAME,'']
    lines+=[f'- [{t["name"]}]({t["url"]}): {t["definition"]}' for t in term_records()]
    lines+=['','## Pages','']+[f'- [{r["title"]}]({r["url"]})' for r in records if r['type'] not in ('source','principle')]
    principles=[r for r in records if r['type']=='principle']
    # Published principle pages (Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified)): name (the
    # page's h1) and the page's own description (its first visible sentence).
    if principles:lines+=['','## Principles','']+[f'- [{r["title"]}]({r["url"]}): {r["description"]}' for r in principles]
    lines+=['','## Sources','']+[f'- [{d["name"]}]({BASE}/{d["file"]})' for d in TERMS.SOURCE_DOCS]
    return '\n'.join(lines)+'\n'
# Paul 4:50 PM ET Nov 1, no page dates, source editions kept (via QA/Governor, verified): the sitemap carries no lastmod.
def lastmod(source,url):
    """Kept for callers: pages carry no dates, so there is never a lastmod."""
    return None
FONT_PRELOADS=''.join(f'<link rel="preload" href="/assets/materials/{font}" as="font" type="font/woff2" crossorigin>' for font in ('source-serif-4-latin-opsz.woff2','inter-latin-wght.woff2'))
def anchors(source,path):
    """Governor's 2:01 PM ET ruling (a) on Paul's parity rule: no JSON-LD @id or url may point at a missing anchor.
    The existing node identifiers get an id on the element they name, markup only (no word changes): <url>#page on
    the page's <body>; /#website on the homepage <body> and /#organization on its h1 (the company name);
    #breadcrumb on the breadcrumb nav; /concepts/#terms on the h1 "Canonical definitions"."""
    own=BASE+route(path)
    def add(pattern,ident):
        nonlocal source
        if re.search(r'\sid="'+ident+'"',source):return
        source,n=re.subn(pattern,lambda m:m.group(0)[:-1]+f' id="{ident}">',source,count=1)
        if not n:raise ValueError(f'No element for #{ident} on {path}')
    jsonld=''.join(re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>',source))
    if path=='index.html':
        add(r'<body\b[^>]*>','website');add(r'<h1\b[^>]*>','organization')
    elif f'"{own}#page"' in jsonld:add(r'<body\b[^>]*>','page')
    if f'"{own}#breadcrumb"' in jsonld:add(r'<nav\b[^>]*aria-label="Breadcrumb"[^>]*>','breadcrumb')
    if path==TERMS.SET_PAGE:add(r'<h1\b[^>]*>','terms')
    # v14 Article JSON-LD (site_layout.article_jsonld): <url>#article names the article element.
    if f'"{own}#article"' in jsonld:add(r'<article\b[^>]*>','article')
    return source
def render(source,path):
    if path=='index.html':
        source=re.sub(r'<main\b[\s\S]*?</main>',lambda _: (ROOT/'content/home.html').read_text(encoding='utf-8').strip(),source,count=1)
    if path=='page-two/index.html':
        source=re.sub(r'<main\b[\s\S]*?</main>',lambda _: (ROOT/'content/page-two.html').read_text(encoding='utf-8').strip(),source,count=1)
    source=definitions(source)
    source=dfn(source,path)
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
        source=source.replace('</head>','<link rel="stylesheet" href="/assets/home.css"><link rel="stylesheet" href="/assets/site.css">'+('<link rel="stylesheet" href="/assets/v14.css">' if path!='page-two/index.html' else '')+FONT_PRELOADS+'</head>',1)
        # v14 (Paul 2026-11-01 22:34): the homepage design system by page type (scripts/site_layout.py). page-two: none.
        source=LAYOUT.apply(source,path)
    if path!='page-two/index.html':source=LAYOUT.head_tags(source,path,LAYOUT.page_type(path))
    for sheet in ('restored-site.css','home.css','site.css','v14.css','home-signature.css'):
        style_version=hashlib.sha256((ROOT/'assets'/sheet).read_bytes()).hexdigest()[:12]
        source=source.replace(f'href="/assets/{sheet}"',f'href="/assets/{sheet}?v={style_version}"')
    main=re.search(r'<main\b[^>]*\bid="([^"]+)"',source)
    anchor=main.group(1) if main else 'content'
    header=(ROOT/'components/header.html').read_text(encoding='utf-8').replace('href="#content"',f'href="#{anchor}"')
    # v14 one header (Paul 2026-11-01 22:34; QA layout 2026-11-01): the homepage bar on every page but page-two, which
    # keeps its own header exactly as it was. Home is the current item only on the homepage; elsewhere the page's own
    # nav item (if it has one) is.
    current=route(path)
    if path!='page-two/index.html':
        bar=(ROOT/'components/home-bar.html').read_text(encoding='utf-8').strip()
        if path!='index.html':
            bar=bar.replace(' aria-current="page">Home<','>Home<')
            bar=re.sub(r'(<form class="gl-go" method="get" action="'+re.escape(current)+r'"><button type="submit")>',r'\1 aria-current="page">',bar,count=1)
        header=re.sub(r'<header class="site-bar"[^>]*>[\s\S]*?</header>',lambda _: bar,header,count=1)
    elif current!='/':header=header.replace(f'href="{current}"',f'href="{current}" aria-current="page"')
    footer=(ROOT/'components/footer.html').read_text(encoding='utf-8')
    if 'id="paul"' in source:footer=footer.replace(' id="paul"','')
    source=source.replace('</head>',machine_block(path)+'</head>',1)
    if path==TERMS.SET_PAGE:
        # Link slot (published principle pages only): each principle heading on /concepts/ links to its page.
        for slug,(href,_) in PRINCIPLES.links().items():
            if f'<article id="{slug}"><h3>' not in source:continue   # Identity, Correspondence: no heading on /concepts/
            source=re.sub(r'(<article id="'+slug+r'"><h3>)([\s\S]*?)(</h3>)',lambda m:m.group(1)+f'<span class="gl-go"><a href="{href}" class="gl-link">'+m.group(2)+'</a></span>'+m.group(3),source,count=1)
    source=source.replace('type="application/atom+xml" href="/feed.xml"','type="application/rss+xml" href="/feed.xml"')
    return anchors(links(source.replace('<!--SITE_HEADER-->',header).replace('<!--SITE_FOOTER-->',footer)),path)
# Governor's 2:01 PM ET ruling (c) on Paul's parity rule: a generated page's meta description is its own visible lede,
# verbatim (was one shared sentence that appears on neither page).
DOCUMENT_DESCRIPTIONS={'library/index.html':'Explore the reasoning architecture, the research, and the original source editions.',
    'publication/index.html':'Source editions and the works they support.'}
def document(title,path,body,extra=''):
    data={'@context':'https://schema.org','@type':'CollectionPage','name':title,'url':BASE+route(path),'isPartOf':{'@id':BASE+'/#website'}}
    source=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} | Governed Logic</title><meta name="description" content="{escape(DOCUMENT_DESCRIPTIONS[path])}"><link rel="canonical" href="{BASE+route(path)}"><meta name="robots" content="index,follow"><link rel="stylesheet" href="/assets/restored-site.css"><script type="application/ld+json">{json.dumps(data)}</script>{extra}</head><body><!--SITE_HEADER--><main class="document-main" id="content"><p class="eyebrow">GOVERNED LOGIC REASONING SYSTEMS</p><h1>{escape(title)}</h1>{body}</main><!--SITE_FOOTER--></body></html>'
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
    principle_pages=[]
    if PRINCIPLES.PUBLISH:
        # Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified).
        available=PRINCIPLES.available(PRINCIPLES.REGISTER.read_text(encoding='utf-8'))
        term_ids={t['code']:t['id'] for t in term_records() if t['page']==TERMS.SET_PAGE}
        for slug,entry in available:
            p=PRINCIPLES.route_path(slug);target=destination/p;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(render(PRINCIPLES.page(slug,entry,BASE,True,available,term_ids.get(slug)),p),encoding='utf-8',newline='\n');principle_pages.append(p)
    # v14 generated pages (Paul 2026-11-01 22:34 and 22:36): /articles/ from the two live articles' own card art, h1 and
    # lede; /the-truth-with-paul/ placeholder. Neither is listed on /library/ or /publication/ (no visible change there).
    v14_pages=['articles/index.html','the-truth-with-paul/index.html']
    v14_src={'articles/index.html':LAYOUT.articles_page({a:(destination/a).read_text(encoding='utf-8') for a in LAYOUT.ARTICLES}),'the-truth-with-paul/index.html':LAYOUT.truth_with_paul_page()}
    for p in v14_pages:
        target=destination/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(links(render(v14_src[p],p)),encoding='utf-8',newline='\n')
    unlisted={'/articles/','/the-truth-with-paul/'}
    records=[];ledes={}
    for p in (*PAGES,*principle_pages,*v14_pages):
        source=(destination/p).read_text(encoding='utf-8');ledes[BASE+route(p)]=LAYOUT.description(source) if p!='page-two/index.html' else None;title=re.search(r'<h1[^>]*>(.*?)</h1>',source,re.S)
        title=unescape(re.sub('<[^>]+>','',title.group(1))).strip() if title else 'Governed Logic Reasoning Systems'
        if p=='index.html':title='Governed Logic Reasoning Systems'
        records.append({'id':BASE+route(p),'title':title,'url':BASE+route(p),'path':route(p),'type':'concept' if p.startswith('concepts/') else 'principle' if p in principle_pages else 'page','text':main_text(LAYOUT.without_ui(source,p)),**({'description':unescape(re.search(r'<meta name="description" content="([^"]*)"',source).group(1))} if p in principle_pages else {}),'sha256':hashlib.sha256((destination/p).read_bytes()).hexdigest()})
    for p,title in zip(SOURCE_FILES,SOURCE_TITLES):records.append({'id':BASE+'/'+p,'title':title+' · Source edition','url':BASE+'/'+p,'path':'/'+p,'type':'source','text':title+' · September 2026','sha256':hashlib.sha256((destination/p).read_bytes()).hexdigest()})
    entries=''.join(f'<article class="library-item" data-record="{r["id"]}" data-kind="{r["type"]}"><span class="eyebrow">{r["type"]}</span><h2 style="font-size:27px"><form class="gl-go" method="get" action="{r["path"]}"><button type="submit">{escape(r["title"])} →</button></form></h2><p>{escape(r["text"][:200])}…</p></article>' for r in records if r['path']!='/' and r['type']!='principle' and r['path'] not in unlisted)
    form='<p class="lede">Explore the reasoning architecture, the research, and the original source editions.</p><form class="library-search" role="search" action="/library/"><div class="library-query"><label for="library-query">Search the library</label><input id="library-query" name="q" type="search" placeholder="A concept, title, or phrase" aria-controls="library-results"></div><div><label for="library-kind">Show</label><select id="library-kind" name="type"><option value="">All works</option><option value="concept">Concepts</option><option value="page">Pages &amp; articles</option><option value="source">Source editions</option></select></div><button id="library-clear" type="button" hidden>Clear</button></form><p id="library-search-mode">All works are available below.</p><p id="library-count" role="status"></p><p id="library-empty" hidden>No matching works. Try a different term.</p>'
    generated={'library/index.html':document('The library','library/index.html',form+'<div id="library-results">'+entries+'</div>','<script src="/assets/library.js" defer></script>'),
    'publication/index.html':document('Publication record','publication/index.html','<p class="lede">Source editions and the works they support.</p><p>The source documents retain their original September 2026 edition dates. The October 2026 articles remain separately identifiable.</p>'+entries),
    'publication/catalog.json':json.dumps({'records':records},ensure_ascii=False,indent=2),'publication/search-index.json':json.dumps({'records':records},ensure_ascii=False),
    'robots.txt':'User-agent: *\nAllow: /\nSitemap: '+BASE+'/sitemap.xml\n',
    'sitemap.xml':'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+BASE+route(p)+'</loc>'+''+'</url>' for p in (*PAGES,*principle_pages,'library/index.html','publication/index.html',*v14_pages))+'</urlset>',
    'terms.jsonld':terms_jsonld(),'llms.txt':llms_txt(records),
    # v14 queued (WEB-227 SIXTH; Paul 4:50 PM ET Nov 1, no page dates): RSS 2.0 at the same URL, no dates. The channel
    # description is /publication/'s visible lede. Each item's description is its page's visible lede, verbatim (its
    # og:description; v14.1, Vera's nit d); pages without a lede (/faq/, the source files) carry none, nor does
    # /page-two/ (kept exactly as it was, so it gets no og:description either).
    'feed.xml':'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Governed Logic publications</title><link>'+BASE+'/</link><description>'+escape(DOCUMENT_DESCRIPTIONS['publication/index.html'])+'</description>'+''.join('<item><title>'+escape(r['title'])+'</title><link>'+r['url']+'</link>'+('<description>'+escape(ledes[r['id']])+'</description>' if ledes.get(r['id']) else '')+'<guid isPermaLink="true">'+r['id']+'</guid></item>' for r in records if r['type']!='principle' and r['path'] not in unlisted)+'</channel></rss>\n'}
    for p,value in generated.items():
        target=destination/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(value,encoding='utf-8',newline='\n')
    manifest={'release':'substantive-restoration','files':{p:hashlib.sha256((destination/p).read_bytes()).hexdigest() for p in PUBLIC_FILES if p!='publication/manifest.json'}}
    (destination/'publication/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    actual={p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()}
    if actual!=set(PUBLIC_FILES):raise ValueError('Artifact differs from explicit allowlist')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args();dest=safe_destination(args.output);build(dest);print(f'Built {len(PUBLIC_FILES)} files, {len(PAGES)+2} substantive routes: {dest}')
if __name__=='__main__':main()
