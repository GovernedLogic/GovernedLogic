"""Mechanical extraction of existing source wording into shared build data."""
import json,re
from render_site import ROOT,PAGES
definitions={}
for slug in ('governed-logic','governed-intelligence','sufficient-grounding','ultimate-grounding','governing-referent','alpha-and-omega-reasoning'):
    source=(ROOT/f'concepts/{slug}/index.html').read_text(encoding='utf-8')
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>',source,re.S):
        data=json.loads(raw)
        for item in data.get('@graph',[]):
            if item.get('@type')=='DefinedTerm':
                definitions[slug]=item['description']
definitions.setdefault('ultimate-grounding','An ultimate ground is not grounded by something more fundamental in the same relevant respect.')
(ROOT/'content/definitions.json').write_text(json.dumps(definitions,ensure_ascii=False,indent=2),encoding='utf-8')
for relative in (*PAGES,'content/home.html','faq/index.json'):
    p=ROOT/relative
    source=p.read_text(encoding='utf-8')
    if relative in ('faq/index.html','faq/index.json'):
        source=source.replace('Governed Intelligence is the artificial intelligence implementation of Governed Logic.',definitions['governed-intelligence'])
    for key,value in definitions.items():
        source=source.replace(value,'{{definition:'+key+'}}')
    p.write_text(source,encoding='utf-8',newline='\n')
print('Centralized',len(definitions),'existing definitions without rewriting their wording.')
