"""v13 machine layer (Paul's v13 approval, Nov 1 2026, 12:30 PM ET; Paul's parity rule): the one source for the site's
defined terms. render_site.py prints every machine surface from this list: the visible <dfn> markup (around words already
on the page; rendered words do not change), the additive JSON-LD (termCode, url), /terms.jsonld and llms.txt.
scripts/check-parity.py fails the build if any of them differs from the visible page text.

Only the terms the site already publishes (QA research 2026-11-01, machine-inventory candidates "In the set"),
with their existing wording. No new terms; the defect groups and other candidates need visible definitions and Paul's
sign-off first. A definition is either the existing content/definitions.json entry (concept pages) or the exact
visible sentence on the page (principles, /concepts/).

Fields: code (termCode: the slug the site already uses for the term), name (the term's name in the existing JSON-LD),
page (source page), fragment (one URI per term: a fragment id on its existing page), dfn (the visible words the <dfn>
wraps, inside the first occurrence of the definition in <main>), definition (or definition_key into definitions.json).
"""
BASE='https://governedlogic.com'
SET_ID=BASE+'/concepts/#terms'
SET_NAME='Canonical definitions'
SET_PAGE='concepts/index.html'
# Grace scoping of Vera's 75860ad gate (V1225, V1226): the six-article list on /concepts/ is now the single Coming soon,
# so no principle term is defined there and none is printed on any machine surface.
PRINCIPLES=()
CONCEPTS=(
    dict(code='governed-logic',name='Governed Logic',dfn='Governed Logic'),
    dict(code='governed-intelligence',name='Governed Intelligence',dfn='Governed Intelligence'),
    dict(code='alpha-and-omega-reasoning',name='Alpha and Omega Reasoning',dfn='Alpha and Omega reasoning'),
    dict(code='governing-referent',name='Governing referent',dfn='referent'),
    dict(code='sufficient-grounding',name='Sufficient grounding',dfn='Sufficiency'),
    # Governor 2:16 PM ET ruling (Nov 1 2026; GL QA F5): one name for this term on every machine surface, the page's
    # visible title (its h1 and its own JSON-LD DefinedTerm name); was 'Ultimate grounding' in terms.jsonld and llms.txt.
    dict(code='ultimate-grounding',name='On the Nature of Ultimate Grounding',dfn='ultimate ground'),
)
# The four September 22 source PDFs on /sources/, described as ScholarlyArticle with only what that page shows: the
# heading, the author and date line, and the file. section is the entry's existing fragment id.
SOURCE_DOCS=(
    dict(section='source-01',name='On the Nature of Ultimate Grounding',file='sources/01_Ultimate_Grounding_2026-09-22_172847_EDT.pdf',date='2026-09-22',shown='22 September 2026'),
    dict(section='source-02',name='Governed Logic',file='sources/02_Governed_Logic_2026-09-22_172847_EDT.pdf',date='2026-09-22',shown='22 September 2026'),
    dict(section='source-03',name='Alpha and Omega Reasoning',file='sources/03_Alpha_and_Omega_Reasoning_2026-09-22_172847_EDT.pdf',date='2026-09-22',shown='22 September 2026'),
    dict(section='source-04',name='Governed Intelligence',file='sources/04_Governed_Intelligence_2026-09-22_172847_EDT.pdf',date='2026-09-22',shown='22 September 2026'),
)

def terms(definitions):
    """The term records, resolved: page, uri (@id), url, definition."""
    out=[]
    for t in PRINCIPLES:
        out.append(dict(t,page=SET_PAGE,id=BASE+'/concepts/#'+t['fragment'],url=BASE+'/concepts/#'+t['fragment']))
    for t in CONCEPTS:
        page='concepts/'+t['code']+'/index.html'
        out.append(dict(t,page=page,fragment='concept',id=BASE+'/concepts/'+t['code']+'/#concept',url=BASE+'/concepts/'+t['code']+'/',definition=definitions[t['code']]))
    return out
