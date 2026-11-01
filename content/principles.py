"""Principle pages (Paul, Nov 1 2026, 12:31 PM ET: "I want a page for each individual principle"). Data-driven and OFF.

Status (Rigel 12:36 PM ET; Governor): the copy register is DRAFT, not approved, and Paul has not chosen between set A
(the live six) and set B (the library seven). The text is on HOLD. Until PUBLISH is True nothing about these pages is
published: no route in the artifact allowlist, no sitemap entry, no link or nav slot, no machine-layer entry, and every
route is a withheld link target, so check-restored fails if anything links to one. Local previews only:
    python3 scripts/preview_principles.py --register <PRINCIPLE_PAGES_COPY.md> --output <new dir>

To publish once Paul approves: commit the approved register at content/principle-register.md, set SET to his choice
(one line) and PUBLISH = True. render_site.py then adds, from this same list, the routes, the link from each principle
on /concepts/, the sitemap entries, the llms.txt lines and the term url in the machine layer.

Words come only from the register, verbatim, in its order. Register headers (sources, Drive ids, library lines,
statuses) stay build-side and are never rendered. Items whose title is MISSING in the register are skipped, not filled.
"""
from html import escape
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
SETS={
    'A':('truth','logic','being','meaning','intelligibility','obligation'),                         # live six, /concepts/ order
    'B':('being','identity','meaning','intelligibility','logic','correspondence','obligation'),     # library seven (MB01)
}
SET='A'          # Paul has not chosen (register: DECISION NEEDED). Switching to B is this one line.
PUBLISH=False    # text on HOLD until Paul picks the set and approves the register.
REGISTER=ROOT/'content/principle-register.md'
INCLUDE_SUPPORTING=True   # the register's "Supporting (older prior set, optional)" blocks; its word counts include them.
TEMPLATE=ROOT/'components/principle.html'
def route_path(slug):return f'principles/{slug}/index.html'
def withheld():return () if PUBLISH else tuple(route_path(s) for s in SETS[SET])
def parse(text):
    """{slug: {'title', 'blocks': [{'header', 'paragraphs'}], 'count', 'skipped'}} from the register, verbatim."""
    out={}
    for sec in re.split(r'^### ',text,flags=re.M)[1:]:
        head,_,rest=sec.partition('\n');slug=head.strip().lower()
        if not re.fullmatch(r'[a-z]+',slug):continue
        title=re.search(r'^\*\*Page title[^*]*:\*\* (.*)$',rest,re.M)
        if not title or title.group(1).startswith('MISSING'):out[slug]={'skipped':'Page title MISSING in the register'};continue
        t=re.match(r'"(.*?)"\.',title.group(1))
        if not t:out[slug]={'skipped':'Page title not quoted in the register'};continue
        blocks=[];cur=None;count=None
        for line in rest.split('\n'):
            if line.startswith('**Passage') or (INCLUDE_SUPPORTING and line.startswith('**Supporting')):cur={'header':line,'paragraphs':[]};blocks.append(cur)
            elif line.startswith('**Supporting'):cur=None
            elif line.startswith('_Word count'):count=int(re.search(r'(\d+)',line).group(1));cur=None
            elif line.startswith(('**','#','>','- ')):cur=None
            elif cur is not None and line.strip():cur['paragraphs'].append(line)
        if not blocks:out[slug]={'skipped':'No passages in the register'};continue
        out[slug]={'title':t.group(1),'blocks':blocks,'count':count}
    return out
def heading(p):
    """A chapter or step heading line of the treatise (all capitals, or "WHY ONE: ...?"): an h2, words unchanged."""
    letters=re.sub(r'[^A-Za-z]','',p)
    return bool(letters) and (letters.isupper() or re.match(r'WHY [A-Z]+:',p) is not None)
def body(entry):
    html=[]
    for b in entry['blocks']:
        html.append('<section class="principle-passage">'+''.join(('<h2>' if heading(p) else '<p>')+escape(p,quote=False)+('</h2>' if heading(p) else '</p>') for p in b['paragraphs'])+'</section>')
    return ''.join(html)
def page(slug,entry,base,published):
    t=TEMPLATE.read_text(encoding='utf-8')
    return (t.replace('{{title}}',escape(entry['title'])).replace('{{canonical}}',base+'/'+route_path(slug)[:-10])
             .replace('{{robots}}','index,follow' if published else 'noindex,nofollow').replace('{{body}}',body(entry)))
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
