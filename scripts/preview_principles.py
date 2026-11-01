#!/usr/bin/env python3
"""Local, UNPUBLISHED previews of the principle pages (Rigel 12:36 PM ET; Governor: text on HOLD, publish flag off).

    python3 scripts/preview_principles.py --register <PRINCIPLE_PAGES_COPY.md> --output <new dir outside the repo>

Builds the normal site into --output, then writes principles/<slug>/index.html for each page in the active set
(content/principles.py SET) whose register entry is complete, rendered through the same template and render() as the
site, with robots noindex,nofollow. Nothing links to them, and they are not in the allowlist, sitemap, llms.txt or
terms.jsonld; never deploy this directory. Register headers (sources, ids, statuses) are written build-side to
<output>.sources.json, never into a page. Prints per page the rendered word count and whether every rendered
paragraph is byte-for-byte the register's.
"""
from html.parser import HTMLParser
from html import unescape
from pathlib import Path
import argparse, json, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_site as R
P=R.PRINCIPLES
class Body(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=False);self.depth=0;self.cur=None;self.paras=[];self.h1=''
    def handle_starttag(self,tag,attrs):
        if tag=='section' and ('class','principle-passage') in attrs:self.depth+=1
        if (self.depth and tag in('p','h2')) or tag=='h1':self.cur=[tag,'']
    def handle_endtag(self,tag):
        if self.cur and tag==self.cur[0]:
            if tag=='h1':self.h1=unescape(self.cur[1])
            else:self.paras.append(unescape(self.cur[1]))
            self.cur=None
        if tag=='section' and self.depth:self.depth-=1
    def handle_data(self,x):
        if self.cur:self.cur[1]+=x
    def handle_entityref(self,n):
        if self.cur:self.cur[1]+='&'+n+';'
    def handle_charref(self,n):
        if self.cur:self.cur[1]+='&#'+n+';'
def main():
    a=argparse.ArgumentParser();a.add_argument('--register',required=True);a.add_argument('--output',required=True);args=a.parse_args()
    text=Path(args.register).read_text(encoding='utf-8');dest=R.safe_destination(args.output);R.build(dest)
    reg=P.parse(text);sources={};rows=[]
    for slug in P.SETS[P.SET]:
        entry=reg.get(slug)
        if entry is None or 'skipped' in entry:print(f'SKIPPED {slug}: {entry["skipped"] if entry else "not in the register"}');continue
        path=P.route_path(slug);t=dest/path;t.parent.mkdir(parents=True,exist_ok=True)
        html=R.render(P.page(slug,entry,R.BASE,False),path);t.write_text(html,encoding='utf-8',newline='\n')
        b=Body();b.feed(html);want=[p for blk in entry['blocks'] for p in blk['paragraphs']]
        same=b.paras==want and b.h1==entry['title'];words=sum(len(p.split()) for p in b.paras)
        rows.append(dict(slug=slug,route='/'+path[:-10],title=entry['title'],paragraphs=len(b.paras),body_words=words,title_words=len(b.h1.split()),register_count=entry['count'],byte_match=same,h1=html.count('<h1')))
        sources[slug]=[blk['header'] for blk in entry['blocks']]
    Path(str(dest)+'.sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
    for r in rows:print(json.dumps(r,ensure_ascii=False))
    return 0 if all(r['byte_match'] and r['body_words']==r['register_count'] and r['h1']==1 for r in rows) else 1
if __name__=='__main__':sys.exit(main())
