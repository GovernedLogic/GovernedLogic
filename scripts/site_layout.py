"""v14 design rollout (Paul 2026-11-01 22:34 "Let's get this big push out."; QA layout assessment 2026-11-01, canvas
a829e55d): the homepage design system on every inner page, by page type. Presentation and machine layer only: every
visible word below is either the page's own text, an existing page name, or one of the UI labels listed in UI_LABELS.

Page types (QA "right look by page type"): principle and concept pages get an enlarged homepage principle tile and the
related-principles band; the two treatises are micro-sites (masthead, sticky contents rail / drawer, reading progress,
chapter pager; chapters stay anchors on the one page); articles get a dark hero with their card art, a wide measure
and a plain-link share row; company, research and the prototype get alternating bands; library, sources, FAQ,
publication and challenge keep the document template with a small art band. page-two is never touched here.
Art is existing approved art only (assets/provisional/*, no new or religious imagery)."""
from html import escape, unescape
from pathlib import Path
import json, re
ROOT=Path(__file__).resolve().parents[1]
BASE='https://governedlogic.com'
# UI labels this module may add (Governor review list). Nothing else visible is new.
UI_LABELS=('Contents','Article','LinkedIn','Reddit','X','Copy link','Copied','←','→')
P='/assets/provisional/'
TREATISES=('concepts/ultimate-grounding/index.html','concepts/governed-logic/index.html')
ARTICLES=('articles/why-anything/index.html','articles/integrity-in-artificial-intelligence/index.html')
BANDS=('company/index.html','research/index.html','mechanism.html')
DOCS=('library/index.html','sources/index.html','publication/index.html','faq/index.html','challenge/index.html','concepts/index.html')
ART={'concepts/ultimate-grounding/index.html':'card-grounding.webp','concepts/governed-logic/index.html':'card-framework.webp',
     'concepts/governed-intelligence/index.html':'card-mathematics.webp','concepts/alpha-and-omega-reasoning/index.html':'card-framework.webp',
     'concepts/governing-referent/index.html':'card-grounding.webp','concepts/sufficient-grounding/index.html':'card-mathematics.webp',
     'articles/why-anything/index.html':'card-mathematics.webp','articles/integrity-in-artificial-intelligence/index.html':'problem-network.webp',
     'company/index.html':'problem-network.webp','research/index.html':'card-mathematics.webp','mechanism.html':'card-framework.webp',
     'articles/index.html':'card-grounding.webp'}
DEFAULT_ART='hero-geometry.svg'
SIZES={'card-grounding.webp':(867,291),'card-framework.webp':(864,291),'card-mathematics.webp':(861,291),'problem-network.webp':(472,618),'hero-geometry.svg':(1200,900)}
def page_type(path):
    if path in ('index.html','page-two/index.html'):return None
    if path.startswith('principles/'):return 'principle'
    if path in TREATISES:return 'treatise'
    if path in ARTICLES:return 'article'
    if path=='articles/index.html':return 'articles'
    if path=='the-truth-with-paul/index.html':return 'media'
    if path in BANDS:return 'bands'
    if path=='about/index.html':return 'about'
    if path in DOCS:return 'doc'
    if path.startswith('concepts/'):return 'concept'
    return 'doc'
def route(path):return '/'+path[:-10] if path.endswith('index.html') else '/'+path
def og_slug(path):
    r=route(path).strip('/')
    return (r.replace('/','-').replace('.html','') or 'home')
def og_path(path):return f'assets/og/{og_slug(path)}.png'
def art_for(path):return ART.get(path,DEFAULT_ART)
def art_img(path,cls='gl-art'):
    a=art_for(path);w,h=SIZES[a]
    return f'<img class="{cls}" src="{P}{a}" alt="" width="{w}" height="{h}" decoding="async" fetchpriority="high">'
# The homepage's principle tiles (content/home.html), by name; principles without a homepage tile use the Seed of Life.
def _home():return (ROOT/'content/home.html').read_text(encoding='utf-8')
# Paul 6:40 AM ET Nov 11 2026 by voice: older homepage principle tiles removed.
# Those tiles were the scrape source for other pages' icons. Keep the SVGs here so
# principle and concept pages still receive the same icons through tile() and related_band().
PRINCIPLE_ICONS = {'Being': '<svg viewBox="0 0 40 40" aria-hidden="true" focusable="false"><path d="M20 4 34 12v16L20 36 6 28V12Z"/><path d="M6 12l14 8 14-8M20 20v16"/></svg>', 'Logic': '<svg viewBox="0 0 40 40" aria-hidden="true" focusable="false"><circle cx="20" cy="9" r="4.5"/><circle cx="8" cy="30" r="4.5"/><circle cx="32" cy="30" r="4.5"/><path d="M17.7 12.9 10.3 26.1M22.3 12.9l7.4 13.2M12.5 30h15"/></svg>', 'Meaning': '<svg viewBox="0 0 40 40" aria-hidden="true" focusable="false"><path d="M10 4h14l8 8v24H10Z"/><path d="M24 4v8h8M15 19h12M15 25h12M15 31h8"/></svg>', 'Intelligibility': '<svg viewBox="0 0 40 40" aria-hidden="true" focusable="false"><path d="M20 7c-2-3-8-3-9.5.5C6.5 8 5 12 6.5 15 4 17 4 22 6.5 24 5 28 8 32 12 32c1 3 5.5 4 8 1.5V7Z"/><path d="M20 7c2-3 8-3 9.5.5 4 .5 5.5 4.5 4 7.5 2.5 2 2.5 7 0 9 1.5 4-1.5 8-5.5 8-1 3-5.5 4-8 1.5"/><path d="M20 12h-4l-2-3M20 19h-6l-3 3M20 26h-4l-2 3M20 15h5l2-3M20 22h6l3 3M20 29h4"/></svg>', 'Obligation': '<svg viewBox="0 0 40 40" aria-hidden="true" focusable="false"><path d="M20 5v29M12 36h16M8 10h24M20 5v5"/><path d="M8 10 3 22h10ZM32 10l-5 12h10Z"/><path d="M3 22a5 3.5 0 0 0 10 0M27 22a5 3.5 0 0 0 10 0"/></svg>'}
def principle_icons():
    found={m.group(2):m.group(1) for m in re.finditer(r'<li>(<svg viewBox="0 0 40 40"[\s\S]*?</svg>)<div><h3>([^<]+)</h3>',_home())}
    return found or PRINCIPLE_ICONS
def problem_icons():
    return {m.group(1):m.group(2) for m in re.finditer(r'action="([^"]+)"><button type="submit"><svg class="gl-picon" (viewBox="0 0 40 40"[\s\S]*?</svg>)',_home())}
SEED=f'<img src="{P}seed-of-life.png" alt="" width="244" height="248">'
def tile(name=None,href=None):
    if name:svg=principle_icons().get(name)
    else:svg=problem_icons().get(href)
    if svg and not svg.startswith('<svg'):svg='<svg '+svg
    return f'<div class="gl-tile" aria-hidden="true">{svg or SEED}</div>'
def h1_text(source):
    m=re.search(r'<h1[^>]*>([\s\S]*?)</h1>',source)
    return re.sub(r'\s+',' ',unescape(re.sub(r'<[^>]+>',' ',re.sub(r'<br\s*/?>',' ',m.group(1))))).strip() if m else ''
def _in_intro(source,html,first=True):
    """Put html at the start (or end) of the first gl-intro band."""
    i=source.find('<div class="gl-intro">')
    if i<0:return source
    if first:j=i+len('<div class="gl-intro">');return source[:j]+html+source[j:]
    j=_close(source,i);return source[:j]+html+source[j:]
def _close(source,i):
    """Index just before the </div> that closes the div opening at i."""
    depth=0
    for m in re.finditer(r'<(/?)div\b[^>]*>',source[i:]):
        depth+=-1 if m.group(1) else 1
        if depth==0:return i+m.start()
    raise ValueError('unclosed div')
def related_band(source):
    """The related-principles band: the principle pages' names-only nav (content/principles.py nav()), each name with
    its homepage tile. Principle pages already carry it; concept pages get the same nav (existing page names)."""
    icons=principle_icons()
    def item(m):
        name=m.group(3)
        icon=icons.get(name)
        icon=icon if icon else SEED
        return f'{m.group(1)}<span class="gl-rel-icon" aria-hidden="true">{icon}</span><span class="gl-rel-name">{name}</span>{m.group(4)}'
    return re.sub(r'(<a href="/principles/[a-z]+/" class="gl-link"(?: aria-current="page")?>)()([A-Za-z]+)(</a>)',item,source)
def chapters(source):
    """Chapters: each <section class="business-section" id=...> and its first h2, verbatim; (id, heading, start, end)."""
    out=[]
    for m in re.finditer(r'<section class="business-section" id="([^"]+)">',source):
        e=source.index('</section>',m.end());h=re.search(r'<h2[^>]*>([\s\S]*?)</h2>',source[m.end():e])
        if h:out.append((m.group(1),re.sub(r'\s+',' ',unescape(re.sub(r'<[^>]+>','',h.group(1)))).strip(),m.start(),e))
    return out
def treatise(source,path):
    title=h1_text(source)
    # chapter pager at the end of each chapter (from the last, so offsets hold): previous and next chapter names, verbatim
    ch=chapters(source)
    for k in range(len(ch)-1,-1,-1):
        prev=ch[k-1] if k else None;nxt=ch[k+1] if k+1<len(ch) else None
        pager=('<nav class="gl-pager" aria-label="Chapter">'+(f'<a class="gl-prev" href="#{prev[0]}"><span aria-hidden="true">←</span> {escape(prev[1],quote=False)}</a>' if prev else '<span></span>')
               +(f'<a class="gl-next-ch" href="#{nxt[0]}">{escape(nxt[1],quote=False)} <span aria-hidden="true">→</span></a>' if nxt else '')+'</nav>')
        e=ch[k][3];source=source[:e]+pager+source[e:]
    items=''.join(f'<li><a href="#{i}">{escape(t,quote=False)}</a></li>' for i,t,_,_ in ch)
    bar=(f'<div class="gl-treatise-bar"><span class="gl-progress" aria-hidden="true"><span></span></span>'
         f'<a class="gl-treatise-title" href="#top">{escape(title,quote=False)}</a>'
         f'<button type="button" class="gl-toc-toggle" aria-controls="gl-toc" aria-expanded="false">Contents</button></div>')
    rail=f'<nav class="gl-toc" id="gl-toc" aria-label="Contents"><ol>{items}</ol></nav>'
    source=source.replace('<div class="gl-intro">','<div class="gl-intro" id="top">',1)
    source=re.sub(r'(<main\b[^>]*>)',lambda m:m.group(1)+bar,source,count=1)
    i=source.find('<div class="gl-intro"');j=_close(source,i)+len('</div>')
    return source[:j]+rail+source[j:]
SHARE=('LinkedIn','https://www.linkedin.com/sharing/share-offsite/?url={u}'),('Reddit','https://www.reddit.com/submit?url={u}&amp;title={t}'),('X','https://x.com/intent/post?url={u}&amp;text={t}')
def share_row(path,title):
    from urllib.parse import quote
    u=quote(BASE+route(path),safe='');t=quote(title,safe='')
    links=''.join(f'<a href="{tpl.format(u=u,t=t)}" rel="noopener" target="_blank">{label}</a>' for label,tpl in SHARE)
    return f'<nav class="gl-share" aria-label="Share">{links}<button type="button" class="gl-copy" data-url="{BASE+route(path)}">Copy link</button><span class="gl-copied" role="status"></span></nav>'
def article_jsonld(path,source):
    title=h1_text(source)
    data={'@context':'https://schema.org','@type':'Article','@id':BASE+route(path)+'#article','headline':title,'name':title,
          'image':BASE+'/'+og_path(path),'url':BASE+route(path),'mainEntityOfPage':{'@id':BASE+route(path)+'#page'},
          'author':{'@id':BASE+'/about/#paul'},'publisher':{'@id':BASE+'/#organization'},'isPartOf':{'@id':BASE+'/#website'}}
    person={'@context':'https://schema.org','@type':'Person','@id':BASE+'/about/#paul','name':'Paul André Couchoud','url':BASE+'/about/#paul'}
    return ('<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False)+'</script>'
            +'<script type="application/ld+json">'+json.dumps(person,ensure_ascii=False)+'</script>')
def description(source):
    """The page's existing visible lede, verbatim (v14.1, Vera's nits b and d; no new prose): its og:description if it
    has one, else its meta description (both already checked visible by check-parity 3c), else None (/faq/, /articles/
    have no lede)."""
    for pat in (r'<meta property="og:description" content="([^"]*)">',r'<meta name="description" content="([^"]*)">'):
        m=re.search(pat,source)
        if m:return unescape(m.group(1))
    return None
def head_tags(source,path,kind):
    """og:title (the page's h1), og:type, og:url (the canonical URL), og:image (absolute; 1200x627 PNG of the page's art
    and its h1, assets/og/), og:description (the page's visible lede, description()), twitter:card, and twitter:title,
    twitter:description and twitter:image identical to og (v14.1, Vera's nit c). No dates."""
    title=h1_text(source)
    if path=='index.html':title='Governed Logic Reasoning Systems'
    canon=re.search(r'<link rel="canonical" href="([^"]+)"',source)
    url=canon.group(1) if canon else BASE+route(path)
    source=re.sub(r'\s*<meta property="og:(?:title|type|url|image[^"]*)" content="[^"]*">','',source)
    source=re.sub(r'\s*<meta name="twitter:[a-z:]+" content="[^"]*">','',source)
    desc=description(source)
    source=re.sub(r'\s*<meta property="og:description" content="[^"]*">','',source)
    tags=(f'<meta property="og:title" content="{escape(title)}"><meta property="og:type" content="{"article" if kind=="article" else "website"}">'
          f'<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}/{og_path(path)}">'
          f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="627">'
          +(f'<meta property="og:description" content="{escape(desc)}">' if desc else '')+
          f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(title)}">'
          +(f'<meta name="twitter:description" content="{escape(desc)}">' if desc else '')+
          f'<meta name="twitter:image" content="{BASE}/{og_path(path)}">')
    return source.replace('</head>',tags+'</head>',1)
def apply(source,path):
    """Body markup for the page's type (called after intro_band, before the header/footer are inserted)."""
    kind=page_type(path)
    if kind is None:return source
    source=re.sub(r'<body class="([^"]*)"',lambda m:f'<body class="{m.group(1)} gl-v14 gl-type-{kind}"',source,count=1)
    if kind in ('principle','concept'):
        name=h1_text(source)
        icon=tile(name) if kind=='principle' else tile(href=route(path))
        source=_in_intro(source,art_img(path)+icon)
        if kind=='concept' and 'class="principle-nav"' not in source:
            import principles as PR
            avail=PR.available(PR.REGISTER.read_text(encoding='utf-8'))
            nav=PR.nav(None,avail)
            source=source.replace('</main>',nav+'</main>',1)
        source=related_band(source)
    elif kind=='treatise':
        source=_in_intro(source,art_img(path));source=treatise(source,path)
    elif kind=='article':
        source=_in_intro(source,art_img(path))
        source=source.replace('</article></main>',share_row(path,h1_text(source))+'</article></main>',1)
    elif kind=='about':
        source=source.replace('<section class="about-hero">','<section class="about-hero">'+art_img(path),1)
    elif kind in ('bands','doc','articles'):
        source=_in_intro(source,art_img(path))
    if kind in ('treatise','article'):
        if '<meta name="author"' not in source:
            source=source.replace('</head>','<meta name="author" content="Paul André Couchoud"></head>',1)
        source=source.replace('</head>','<script src="/assets/v14.js" defer></script></head>',1)
    if kind=='article':source=source.replace('</head>',article_jsonld(path,source)+'</head>',1)
    return source
ARROW='<svg class="gl-arrow" viewBox="0 0 20 12" aria-hidden="true" focusable="false"><path d="M1 6h17M13 1l5 5-5 5"/></svg>'
def article_card(path,source,ident,featured=False):
    """The homepage card component (content/home.html .gl-card): the article's card art, the kind label "Article", its
    h1 as the title and its first paragraph (the lede) verbatim."""
    title=h1_text(source)
    i=source.find('</div>',source.find('<div class="gl-intro"'))
    lede=re.search(r'<p>([\s\S]*?)</p>',source[i:]).group(1)
    a=art_for(path);w,h=SIZES[a]
    return (f'<article class="gl-card{" gl-card-featured" if featured else ""}"><img src="{P}{a}" alt="" width="{w}" height="{h}" loading="lazy">'
            f'<div class="gl-card-body"><p class="gl-card-kind">Article</p><h3 id="{ident}">{escape(title,quote=False)}</h3><p>{lede}</p>'
            f'<form class="gl-go" method="get" action="{route(path)}"><button type="submit" class="gl-card-go" aria-labelledby="{ident}">{ARROW}</button></form></div></article>')
def _shell(title,path,main,description=None):
    data={'@context':'https://schema.org','@type':'CollectionPage' if path=='articles/index.html' else 'WebPage','@id':BASE+route(path)+'#page','name':title,'url':BASE+route(path),'isPartOf':{'@id':BASE+'/#website'}}
    desc=f'<meta name="description" content="{escape(description)}">' if description else ''
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} | Governed Logic</title>{desc}'
            f'<link rel="canonical" href="{BASE+route(path)}"><meta name="robots" content="index,follow"><link rel="stylesheet" href="/assets/restored-site.css">'
            f'<script type="application/ld+json">{json.dumps(data,ensure_ascii=False)}</script></head><body><!--SITE_HEADER-->{main}<!--SITE_FOOTER--></body></html>')
def articles_page(sources):
    """/articles/ (QA option A): a featured card and one Latest snap rail of the other articles; each live article is
    listed once (v14.1, Vera's nit a: the grid repeated them). h1 "Articles" (UI label, the index's name)."""
    paths=list(ARTICLES)
    feat=article_card(paths[0],sources[paths[0]],'gl-art-featured',True)
    rail=''.join(article_card(p,sources[p],f'gl-rail-{k}') for k,p in enumerate(paths[1:],1))
    main=('<main class="document-main gl-articles" id="content"><div class="gl-intro"><h1>Articles</h1></div>'
          f'<section class="gl-featured" aria-labelledby="gl-art-featured">{feat}</section>'
          f'<section class="gl-rail-band" aria-labelledby="gl-latest-title"><h2 id="gl-latest-title" class="gl-eyebrow">Latest</h2><div class="gl-rail" tabindex="0" role="region" aria-labelledby="gl-latest-title">{rail}</div></section></main>')
    return _shell('Articles','articles/index.html',main)
TWP_URL='https://www.youtube.com/@TheTruthwithPaul'
def truth_with_paul_page():
    """The Truth with Paul placeholder (Paul 2026-11-01 22:36, "put something cool like come in soon but make it
    awesome"): deep-blue hero, the channel name as the one h1, "Coming soon", and a plain link "Subscribe on YouTube".
    Those three strings are the page's only copy. Art: the homepage hero geometry and Seed of Life (existing, approved)."""
    # Paul's direct banner (1983x793). Alt is the banner's own visible titles, not new page copy.
    twp_alt='THE TRUTH WITH PAUL. JESUS. REASONING. ARTIFICIAL INTELLIGENCE. THE LOGOS. THE LOGIC. THE LAB. THE LABYRINTH.'
    main=('<main class="gl-twp" id="content"><section class="gl-twp-hero">'
          '<picture class="gl-twp-banner"><source type="image/webp" srcset="/assets/brand/twp-banner-960.webp 960w, /assets/brand/twp-banner-1440.webp 1440w, /assets/brand/twp-banner-1920.webp 1920w" sizes="100vw">'
          f'<img src="/assets/brand/twp-banner-1440.jpg" alt="{twp_alt}" width="1983" height="793" fetchpriority="high"></picture>'
          '<div class="gl-twp-copy"><h1>The Truth with Paul</h1><p class="gl-twp-soon">Coming soon</p>'
          f'<span class="gl-go"><a href="{TWP_URL}" class="gl-link gl-btn gl-btn-bright gl-twp-sub" rel="noopener">Subscribe on YouTube{ARROW}</a></span></div></section>'
          '<script src="/assets/brand-hold.js" defer></script></main>')
    return _shell('The Truth with Paul','the-truth-with-paul/index.html',main,'Coming soon')
def without_ui(source,path):
    """The page without the v14 navigation added by this module (treatise masthead, contents, pager, share row; the
    related-principles band on concept pages), so /library/, /publication/ and the search index keep each page's text."""
    source=re.sub(r'<div class="gl-treatise-bar">[\s\S]*?</div>','',source)
    source=re.sub(r'<nav class="(?:gl-toc|gl-pager|gl-share)"[\s\S]*?</nav>','',source)
    if page_type(path)=='concept':source=re.sub(r'<nav class="principle-nav"[\s\S]*?</nav>','',source)
    return source
