"""Principle pages (Paul, Nov 1 2026, 12:31 PM ET: "I want a page for each individual principle").

PUBLISHED as set B: Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified). The ruling: "principle
set = LIBRARY SEVEN (set B): Being, Identity, Meaning, Intelligibility, Logic, Correspondence, Obligation. Yes, publish
the draft text as written." No Truth principle page.

content/principle-register.md is Rigel's copy register (PRINCIPLE_PAGES_COPY.md, 2026-11-01), committed byte for byte.
Words come only from it, verbatim, in its order. Register headers (sources, Drive ids, library lines, statuses, word
counts, MISSING notes) stay build-side and are never rendered. Each page's title and single h1 is the principle's name
(the register's section heading). Nothing MISSING in the register is filled.

One build-side correction (CODES below): any "GL-P<n>" code at the start or end of a Supporting passage is stripped
(codes only). The corrected register (Paul 7:48 PM ET Nov 1 (via Governor, verified)) already carries none, so the strip
is a no-op kept as a guard. The Supporting passages stay exactly where the register puts them (MOVES is empty), each
under its own principle, library RES-26: Logic "Logic is binding and answerable to truth." and "Inference must
preserve valid relations ..." (L17633-17634); Intelligibility "Intelligibility is real." and "Reality has
apprehensible order ..." (L17636-17637); Obligation "Moral obligation is real and binding." and "Obligation is not
reducible to ..." (L17639-17640).

Every slug in SETS that is not in the published set (Truth) is a withheld link target: nothing may link to it, it is
not built, and the live probe requires it to 404.
"""
from html import escape
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
SETS={
    'A':('truth','logic','being','meaning','intelligibility','obligation'),                         # live six, /concepts/ order
    'B':('being','identity','meaning','intelligibility','logic','correspondence','obligation'),     # library seven (MB01)
}
SET='B'          # Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified).
PUBLISH=True
REGISTER=ROOT/'content/principle-register.md'
INCLUDE_SUPPORTING=True   # the register's "Supporting (older prior set, optional)" blocks; its word counts include them.
TEMPLATE=ROOT/'components/principle.html'
def route_path(slug):return f'principles/{slug}/index.html'
def withheld():
    """Principle routes that must not be linked or served: every set slug when unpublished; once published, every
    slug of another set that is not in the published set (Truth)."""
    if not PUBLISH:return tuple(route_path(s) for s in SETS[SET])
    return tuple(route_path(s) for s in dict.fromkeys(x for v in SETS.values() for x in v) if s not in SETS[SET])
NAMES={'being':'Being','identity':'Identity','meaning':'Meaning','intelligibility':'Intelligibility','logic':'Logic',
       'correspondence':'Correspondence','obligation':'Obligation','truth':'Truth'}
CODES=re.compile(r'^GL-P\d+ | GL-P\d+$')
# Paul 5:29 PM ET Nov 1 (via QA/Governor, verified): no Supporting passage is moved; the register's placement stands.
MOVES=()
def corrected(reg):
    """Strip the codes (and apply MOVES, now empty); fail if the register text a move relies on is not there exactly."""
    def supporting(slug):
        b=[b for b in reg[slug]['blocks'] if b['header'].startswith('**Supporting')]
        return b[0] if b else None
    for src,text,dst in MOVES:
        sb=supporting(src)
        if sb is None or text not in sb['paragraphs']:raise ValueError(f'Register Supporting passage under {src} changed; correction no longer applies')
        sb['paragraphs'].remove(text)
        db=supporting(dst)
        if db is None:db={'header':'**Supporting (relabeled)','paragraphs':[]};reg[dst]['blocks'].append(db)
        db['paragraphs'].append(text)
    for slug,e in reg.items():
        if 'blocks' not in e:continue
        e['blocks']=[b for b in e['blocks'] if b['paragraphs']]
        for b in e['blocks']:
            if b['header'].startswith('**Supporting'):b['paragraphs']=[CODES.sub('',p) for p in b['paragraphs']]
    return reg
def parse(text):
    """{slug: {'title', 'blocks': [{'header', 'paragraphs'}], 'count'}} from the register, verbatim. The title is the
    principle's name (the section heading); the register's "Page title" field is not used."""
    out={}
    for sec in re.split(r'^### ',text,flags=re.M)[1:]:
        head,_,rest=sec.partition('\n');slug=head.strip().lower()
        if not re.fullmatch(r'[a-z]+',slug):continue
        blocks=[];cur=None;count=None
        for line in rest.split('\n'):
            if line.startswith(('**Passage','Passage source:')) or (INCLUDE_SUPPORTING and line.startswith('**Supporting')):cur={'header':line,'paragraphs':[]};blocks.append(cur)
            elif line.startswith('**Supporting'):cur=None
            elif line.startswith('_Word count'):count=int(re.search(r'(\d+)',line).group(1));cur=None
            elif line.startswith(('**','#','>','- ','Article or treatise narrative')):cur=None
            elif cur is not None and line.strip():cur['paragraphs'].append(line)
        if not blocks:out[slug]={'skipped':'No passages in the register'};continue
        out[slug]={'title':NAMES[slug],'blocks':blocks,'count':count}
    return corrected(out)
def words(entry):return sum(len(p.split()) for b in entry['blocks'] for p in b['paragraphs'])
def heading(p):
    """A chapter or step heading line of the treatise (all capitals, or "WHY ONE: ...?"): an h2, words unchanged."""
    letters=re.sub(r'[^A-Za-z]','',p)
    return bool(letters) and (letters.isupper() or re.match(r'WHY [A-Z]+:',p) is not None)
# Paul 8:38 AM ET Nov 12 2026: in the section headings the em dash becomes " | ". Headings only, no other word change.
def heading_text(p):return p.replace(' \u2014 ',' | ')
def body(entry):
    html=[]
    for b in entry['blocks']:
        html.append('<section class="principle-passage">'+''.join(('<h2>'+escape(heading_text(p),quote=False)+'</h2>') if heading(p) else ('<p>'+escape(p,quote=False)+'</p>') for p in b['paragraphs'])+'</section>')
    return ''.join(html)
def description(entry):
    """The page's meta/og/JSON-LD description: the first sentence of its first passage, verbatim (visible on the page)."""
    first=entry['blocks'][0]['paragraphs'][0]
    m=re.match(r'(.+?[.!?])(?:\s|$)',first)
    return m.group(1) if m else first
# Audit batch 2: six domains, then Identity one level below. No label words. Time and the ground have no pages.
# Paul 8:38 AM ET Nov 12 2026: the ground "Jesus Christ the Logos" at the top and Time beside Identity on the bottom
# level, both unlinked plain labels, as the homepage shows Time. Three levels: ground, the six, Identity and Time.
NAV_LEVELS=(('ground',),('being','meaning','logic','intelligibility','obligation','correspondence'),('identity','time'))
LABELS={'ground':'Jesus Christ the Logos','time':'Time'}
def nav(slug,base_entries):
    """Ordinary links among the published principle pages, by name only (Identity and Correspondence have no /concepts/
    heading to carry their link)."""
    published={s for s,_ in base_entries}
    def item(s, level):
        if s in LABELS:return f'<span class="gl-principle-label">{escape(LABELS[s])}</span>'
        if s not in published:return ''
        klass='gl-go gl-principle-level-2' if level==3 else 'gl-go'
        return f'<span class="{klass}"><a href="/{route_path(s)[:-10]}" class="gl-link"'+(' aria-current="page"' if s==slug else '')+f'>{escape(NAMES[s])}</a></span>'
    # Classes: gl-principle-ground (the ground), gl-principle-level-1 (the six), gl-principle-level-2 (Identity and Time).
    names={1:'gl-principle-ground',2:'gl-principle-level gl-principle-level-1',3:'gl-principle-level gl-principle-level-2'}
    levels=''.join(f'<div class="{"gl-principle-level " if i==1 else ""}{names[i]}">{"".join(item(s, i) for s in slugs)}</div>' for i,slugs in enumerate(NAV_LEVELS,1))
    return f'<nav class="principle-nav" aria-label="Principles">{levels}</nav>'
def page(slug,entry,base,published,entries=(),term_id=None):
    import json
    url=base+'/'+route_path(slug)[:-10]
    ld={'@context':'https://schema.org','@type':'WebPage','@id':url+'#page','url':url,'name':NAMES[slug],
        'description':description(entry),'isPartOf':{'@id':base+'/#website'}}
    if term_id:ld['about']={'@id':term_id}
    t=TEMPLATE.read_text(encoding='utf-8')
    return (t.replace('{{title}}',escape(entry['title'])).replace('{{description}}',escape(description(entry)))
             .replace('{{canonical}}',url).replace('{{jsonld}}',json.dumps(ld,ensure_ascii=False))
             .replace('{{robots}}','index,follow' if published else 'noindex,nofollow').replace('{{body}}',body(entry))
             .replace('{{nav}}',nav(slug,entries) if entries else ''))
def available(text):
    reg=parse(text);return [(s,reg[s]) for s in SETS[SET] if s in reg and 'skipped' not in reg[s]]
def routes():
    if not PUBLISH:return ()
    return tuple(route_path(s) for s,_ in available(REGISTER.read_text(encoding='utf-8')))
def links():
    """{term fragment on /concepts/: (route, page title)} for the link slot on /concepts/ and the machine layer
    (published only)."""
    if not PUBLISH:return {}
    return {s:('/'+route_path(s)[:-10],e['title']) for s,e in available(REGISTER.read_text(encoding='utf-8'))}
