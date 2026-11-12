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
# v14.2 (Paul 2026-11-02 18:08 voice call): the homepage video band; it adds no words to the page.
# v14.2.2 (Grace relay 7:23 PM Nov 2, Paul 7:08 PM approval): each media URL carries ?v=<first 8 hex of that file's own
# sha256>, so a changed file always gets a new URL.
# v14.3 (Grace relay 8:42 AM Nov 3, Paul voice call): the video has no captions: no <track> and no .vtt in the build.
VIDEO='/assets/video/gl-home-explainer.mp4';VIDEO_POSTER='/assets/video/gl-home-explainer-poster.webp'
def video_url(root,path):
    """The cache-busted URL for a video file: path?v=<first 8 hex of its sha256>."""
    f=root/path[1:]
    return path+'?v='+(hashlib.sha256(f.read_bytes()).hexdigest()[:8] if f.is_file() else 'missing')
def video_errors(root):
    errors=[];home=(root/'index.html').read_text(encoding='utf-8')
    band=re.search(r'</section>\s*<section class="gl-video">([\s\S]*?)</section>\s*<section class="gl-core">',home)
    if not band:return ['Homepage video band is not directly under the hero and before the core section']
    b=band.group(1);v=re.search(r'<video\b([^>]*)>',b)
    if not v or len(re.findall(r'<video\b',home))!=1:return ['Homepage video band: expected exactly one <video>']
    va=v.group(1)
    for need in (' controls',' playsinline','preload="metadata"',f'poster="{video_url(root,VIDEO_POSTER)}"',' width="1280"',' height="720"'):
        if need not in va:errors.append('Homepage video lacks '+need.strip())
    if re.search(r'\b(autoplay|loop|muted)\b',va):errors.append('Homepage video must not autoplay, loop or start muted')
    if f'<source src="{video_url(root,VIDEO)}" type="video/mp4">' not in b:errors.append('Homepage video source is not '+video_url(root,VIDEO))
    if len(re.findall(r'<source\b',b))!=1:errors.append('Homepage video must have exactly one <source>')
    if re.search(r'<track\b',home):errors.append('Homepage video must have no <track> element (no captions since v14.3)')
    vtts=sorted(str(f.relative_to(root)) for f in root.rglob('*') if f.is_file() and (f.suffix.lower()=='.vtt' or (f.suffix=='.html' and re.search(r'\.vtt\b',f.read_text(encoding='utf-8',errors='replace')))))
    if vtts:errors.append('No .vtt may be published or referenced (no captions since v14.3): '+', '.join(vtts))
    # The player's accessible name is the hero h1, by reference: no aria-label, no new words.
    h1=re.findall(r'<h1\b([^>]*)>([\s\S]*?)</h1>',home)
    if 'aria-labelledby="organization"' not in va or 'aria-label=' in va or 'title=' in va:errors.append('Homepage video must be named by aria-labelledby="organization" only')
    if len(h1)!=1 or not re.search(r'\sid="organization"',h1[0][0]) or re.sub(r'<[^>]+>','',h1[0][1]).strip()!='Governed Logic Reasoning Systems':errors.append('Homepage video name target is not the hero h1 "Governed Logic Reasoning Systems"')
    if re.sub(r'<[^>]+>','',b).strip():errors.append('Homepage video band adds words to the page: '+repr(re.sub(r'<[^>]+>','',b).strip()))
    for f in (VIDEO,VIDEO_POSTER):
        if not (root/f[1:]).is_file():errors.append('Homepage video file missing: '+f)
    if (root/VIDEO_POSTER[1:]).is_file() and (root/VIDEO_POSTER[1:]).read_bytes()[8:12]!=b'WEBP':errors.append('Homepage video poster is not a WebP image')
    return errors
# Visual refresh, structural part (Paul, first hand: no mid-page Seed of Life, no fly-up): the logo fly-up
# (home-chime.js) is gone, the hero Seed of Life <img> and its preload are gone, div.gl-hero-art stays empty as the
# signature field, and the signature (home-signature.js and .css) loads on the homepage only. Its colours are custom
# properties, its motion sits inside prefers-reduced-motion: no-preference, and class gl-cool swaps the warm set.
SIG_JS='assets/home-signature.js';SIG_CSS='assets/home-signature.css';SIG_JS_MAX=3000
# SPEC.md line 107: gl-cool swaps the four warm values. The gold defaults are declared in :root too.
COOL={'--gl-warm':'#9cc8ff','--gl-warm-ink':'#1657c2','--gl-warm-glow':'rgba(200,225,255,.9)','--gl-warm-line':'rgba(111,178,255,.6)'}
WARM={'--gl-warm':'#d7b57e','--gl-warm-ink':'#8a5f1f','--gl-warm-glow':'rgba(255,226,170,.9)','--gl-warm-line':'rgba(215,181,126,.6)'}
WARM_USED=('--gl-warm','--gl-warm-line','--gl-warm-glow')
def _blocks(css,head):
    """(start,end) of every block whose prelude matches head, braces balanced."""
    out=[]
    for m in re.finditer(head,css):
        i=css.index('{',m.start());depth=0
        for j in range(i,len(css)):
            depth+=css[j]=='{';depth-=css[j]=='}'
            if depth==0:out.append((m.start(),j+1));break
    return out
def _cut(css,spans):
    for a,b in sorted(spans,reverse=True):css=css[:a]+css[b:]
    return css
def signature_errors(root):
    errors=[];home=(root/'index.html').read_text(encoding='utf-8')
    if (root/'assets/home-chime.js').exists():errors.append('Logo fly-up script published: assets/home-chime.js')
    for f in sorted(root.rglob('*.html')):
        if re.search(r'home-chime|gl-chime',f.read_text(encoding='utf-8')):errors.append('Logo fly-up referenced: '+f.relative_to(root).as_posix())
    if re.search(r'<link\b[^>]*rel="preload"[^>]*hero-geometry\.svg',home):errors.append('Homepage still preloads the hero Seed of Life')
    art=re.findall(r'<div class="gl-hero-art"([^>]*)>([\s\S]*?)</div>',home)
    if len(art)!=1:errors.append('Homepage signature field: expected exactly one div.gl-hero-art')
    elif art[0][1].strip() or 'aria-hidden="true"' not in art[0][0]:errors.append('Homepage signature field div.gl-hero-art must be empty and aria-hidden in the built HTML')
    hero=re.search(r'<section class="gl-hero"[\s\S]*?</section>',home)
    if hero and re.search(r'<(img|svg|picture)\b[^>]*(hero-geometry|seed-of-life)',hero.group(0)):errors.append('Homepage hero still shows a Seed of Life')
    js_url='/'+SIG_JS+'?v='+(hashlib.sha256((root/SIG_JS).read_bytes()).hexdigest()[:8] if (root/SIG_JS).is_file() else 'missing')
    if len(re.findall(r'<script src="/assets/home-signature\.js[^"]*" defer></script>',home))!=1:errors.append('Homepage does not load the signature script once (defer)')
    elif f'<script src="{js_url}" defer></script>' not in home:errors.append('Homepage signature script is not '+js_url+' (stale or missing ?v= key)')
    if len(re.findall(r'<link rel="stylesheet" href="/assets/home-signature\.css\?v=[0-9a-f]{12}">',home))!=1:errors.append('Homepage does not load the signature stylesheet once')
    for f in sorted(root.rglob('*.html')):
        rel=f.relative_to(root).as_posix()
        if rel!='index.html' and 'home-signature' in f.read_text(encoding='utf-8'):errors.append('Signature loaded outside the homepage: '+rel)
    js=(root/SIG_JS).read_bytes() if (root/SIG_JS).is_file() else b''
    if not js:errors.append('Signature script missing: '+SIG_JS)
    elif len(js)>SIG_JS_MAX:errors.append(f'Signature script is {len(js)} bytes, over {SIG_JS_MAX}')
    else:
        t=js.decode('utf-8')
        for need,why in (("setAttribute('aria-hidden','true')",'its SVG is not aria-hidden'),("sessionStorage",'it does not play once per session'),("prefers-reduced-motion: no-preference",'it ignores reduced motion')):
            if need not in t:errors.append('Signature script: '+why)
        if re.search(r'#[0-9a-fA-F]{3,8}\b|rgba?\(',t):errors.append('Signature script hard-codes a colour (colours belong to CSS custom properties)')
        if re.search(r'textContent|innerHTML|innerText|createTextNode|insertAdjacent',t):errors.append('Signature script may add words to the page')
        if re.search(r'setInterval|requestAnimationFrame|\binfinite\b',t):errors.append('Signature script must not loop')
    css=(root/SIG_CSS).read_text(encoding='utf-8') if (root/SIG_CSS).is_file() else ''
    if not css:errors.append('Signature stylesheet missing: '+SIG_CSS);return errors
    css=re.sub(r'/\*[\s\S]*?\*/','',css)
    roots=_blocks(css,r':root(?:\.gl-cool)?\s*\{')
    cool=[css[a:b] for a,b in _blocks(css,r':root\.gl-cool\s*\{')]
    for k,v in COOL.items():
        if not cool or not re.search(re.escape(k)+r'\s*:\s*'+re.escape(v)+r'\s*[;}]',cool[0]):errors.append(f'Cool switch :root.gl-cool does not set {k}: {v}')
    gold=[css[a:b] for a,b in _blocks(css,r':root\s*\{')]
    for k,v in WARM.items():
        if not gold or not re.search(re.escape(k)+r'\s*:\s*'+re.escape(v)+r'\s*[;}]',gold[0]):errors.append(f':root does not declare the gold default {k}: {v}')
    for k in WARM_USED:
        if 'var('+k+')' not in _cut(css,roots):errors.append(f'Signature does not use {k}, so gl-cool would not reach it')
    rest=_cut(css,roots+_blocks(css,r'@keyframes\s+[\w-]+\s*\{'))
    if re.search(r'#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(',rest):errors.append('Signature stylesheet hard-codes a colour outside :root (use a custom property)')
    motion=_blocks(css,r'@media\s*\(prefers-reduced-motion:\s*no-preference\)\s*\{')
    if re.search(r'\banimation(-name)?\s*:\s*(?!none)',_cut(css,motion)):errors.append('Signature animation outside prefers-reduced-motion: no-preference')
    if re.search(r'\binfinite\b',css):errors.append('Signature stylesheet must not loop')
    if re.search(r'content\s*:\s*"[^"]',css):errors.append('Signature stylesheet adds words (content)')
    return errors
# /page-two/ is frozen: its built HTML and every file it loads (stylesheets with their ?v= values, images, fonts and the
# files those stylesheets reference) stay byte-identical to the d1ba24d build.
PAGE_TWO_BYTES={'page-two/index.html':'282bb8baf502dab1906db4137bc0243274414de1852d4cc2c84a38ba65dc38fe',
    'assets/brand/favicon.png':'7e6becfd1d282d7468b1cf0d8e042210dd080577533d6276f2d51f5b72ade3b3',
    'assets/brand/gl-logo.webp':'3e5df9209172c96e6626f8dd06fcb2d52be30e865b5d6bb4a40429376437241a',
    'assets/brand-chrome.css':'ef5dc6ad7f9b01cbbae5b79466eab8bd3c020ba658003dcbbf56695b4f2cd6dd',
    'assets/brand-nav.js':'88099384ae1f52a8e1bfb409bda6ef8f32b821842ca103be8074a47a6c439104',
    'assets/governed-logic-mark.webp':'7498a49a67a36f6dfcbe87ecba5262df2d8904f71cae9b4250fa449f31d7469c',
    'assets/home.css':'1af20a24a1b5836fdac5b70ba1b249c7aaf7893144c56b1c010a7d566b18a710',
    'assets/materials/ibm-plex-sans.ttf':'160f6c6ae5cd9426005fe12c60f202243aeedba9a2002ff150368aac9d75d9eb',
    'assets/materials/inter-latin-wght.woff2':'3100e775e8616cd2611beecfa23a4263d7037586789b43f035236a2e6fbd4c62',
    'assets/materials/source-serif-4-latin-opsz.woff2':'f2ea9c12d2fe9bd3a9589b02ad2c0909da88f30938c91adc838c4f4098f9f9e0',
    'assets/provisional/grain.png':'af219d0072d73fd88c23ee263c3bf26d99b6dcc7636ef19b64acc1f4390e754e',
    'assets/provisional/problem-network.webp':'a1ec26c2bf20a96b1c0f0a39da3d2e90f34342531236e2155005b624b1e33eea',
    'assets/provisional/seed-of-life.png':'168a65a80aef7635e3c7217df42d81f5e6665f09936fd70984184e595fb1bdff',
    'assets/restored-site.css':'06b90c3646f9b879ae13b08e9f7bb83cda89b82efe90cd5a20b774906ea2372d',
    'assets/site.css':'37343039c5d081ed9ed9afd237447d6135c0a30a8a6c42778805798f54acb004',
    'assets/the-groundless-machine.webp':'25558336437765d16d44267c380f0852b8efe0ecd3ad1ed17dfd5e3e3345cbe5',
    'paul-portrait.png':'47cdf400e9c924b27a0f2d98df03f69c7bb4dc2b9f89f1c3b2d5a6b0499087e8'}
def page_two_files(root):
    """Every local file /page-two/ loads, followed through stylesheets: path -> sha256 (or 'missing')."""
    seen={};todo=['page-two/index.html']
    while todo:
        p=todo.pop()
        if p in seen:continue
        f=root/p
        if not f.is_file():seen[p]='missing';continue
        b=f.read_bytes();seen[p]=hashlib.sha256(b).hexdigest()
        if p.endswith('.html'):
            for r in re.findall(r'<(?:link|script|img|source|video)\b[^>]*?\s(?:href|src|poster)="([^"]+)"',b.decode('utf-8')):
                u=urlsplit(r)
                if not u.netloc and u.path.startswith('/'):todo.append(unquote(u.path.lstrip('/')))
        elif p.endswith('.css'):
            base=p.rsplit('/',1)[0]
            for r in re.findall(r"url\(['\"]?([^'\")]+)['\"]?\)",b.decode('utf-8')):
                if r.startswith('data:') or '//' in r:continue
                todo.append(r.lstrip('/') if r.startswith('/') else Path(base,r).as_posix())
    return seen
def page_two_errors(root):
    got=page_two_files(root)
    return [f'/page-two/ is frozen, but {p} differs from the d1ba24d build' for p in sorted(set(got)|set(PAGE_TWO_BYTES)) if got.get(p)!=PAGE_TWO_BYTES.get(p)]
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
    errors+=video_errors(root)
    errors+=signature_errors(root)
    errors+=page_two_errors(root)
    sitemap=(root/'sitemap.xml').read_text(encoding='utf-8')
    for p in V14_PAGES:
        if '<loc>'+BASE+route(p)+'</loc>' not in sitemap:errors.append('Page missing from sitemap: '+p)
    if 'href="/the-truth-with-paul/"' not in (root/'index.html').read_text(encoding='utf-8').split('<footer',1)[-1]:errors.append('The Truth with Paul is not in the footer')
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