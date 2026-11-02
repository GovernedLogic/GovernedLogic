#!/usr/bin/env python3
"""Make the og:image PNGs (v14, Paul 2026-11-01 22:34): 1200x627, one per page, from the page's existing art
(scripts/site_layout.py ART; the Seed of Life on the homepage deep blue where the art is the hero SVG) and the page's
og:title, which is its visible h1. The title is the only text in the image and is also stored in the PNG's "Title"
text chunk, so check-parity can hold it equal to the page's og:title. Run after any h1 or art change, then commit
assets/og/. Usage: python3 scripts/make_og.py"""
from pathlib import Path
import re, sys, tempfile, shutil
from html import unescape
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from PIL.PngImagePlugin import PngInfo
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
W,H=1200,627
def fonts():
    from fontTools.ttLib import TTFont
    out=Path(tempfile.mkdtemp())/'serif.ttf'
    f=TTFont(ROOT/'assets/materials/source-serif-4-latin-opsz.woff2');f.flavor=None;f.save(out)
    return out
def cover(im,w,h):
    r=max(w/im.width,h/im.height);im=im.resize((round(im.width*r),round(im.height*r)),Image.LANCZOS)
    x=(im.width-w)//2;y=(im.height-h)//2;return im.crop((x,y,x+w,y+h))
def wrap(draw,text,font,width):
    words=text.split();lines=[];cur=''
    for w in words:
        t=(cur+' '+w).strip()
        if draw.textlength(t,font=font)<=width:cur=t
        else:lines.append(cur);cur=w
    lines.append(cur);return lines
def make(title,art,serif,out):
    base=Image.new('RGB',(W,H),'#00060c')
    if art.endswith('.svg'):
        g=Image.new('RGB',(W,H));d=ImageDraw.Draw(g)
        for r in range(900,0,-6):
            t=r/900;c=(int(0+10*(1-t)),int(6+73*(1-t)),int(12+126*(1-t)));d.ellipse((820-r,313-r*0.8,820+r,313+r*0.8),fill=c)
        base=g
        seed=Image.open(ROOT/'assets/provisional/seed-of-life.png').convert('RGBA').resize((440,447),Image.LANCZOS)
        glow=seed.filter(ImageFilter.GaussianBlur(18));base.paste(glow,(700,90),glow);base.paste(seed,(700,90),seed)
    else:
        im=cover(Image.open(ROOT/'assets/provisional'/art).convert('RGB'),W,H);base=im
    shade=Image.new('L',(W,H))
    for x in range(W):
        a=int(max(0,min(235,235-(x-380)*0.32)))
        ImageDraw.Draw(shade).line([(x,0),(x,H)],fill=a)
    base=Image.composite(Image.new('RGB',(W,H),'#020b13'),base,shade)
    d=ImageDraw.Draw(base)
    mark=Image.open(ROOT/'assets/provisional/seed-of-life.png').convert('RGBA').resize((64,65),Image.LANCZOS);base.paste(mark,(72,64),mark)
    d.line([(72,160),(232,160)],fill='#2f9ce6',width=3)
    for size in (84,76,68,60,54,48):
        f=ImageFont.truetype(str(serif),size);f.set_variation_by_axes([500,60])
        lines=wrap(d,title,f,760)
        if len(lines)<=3:break
    y=H-90-len(lines)*int(size*1.12)
    for ln in lines:d.text((72,y),ln,font=f,fill='#ffffff');y+=int(size*1.12)
    info=PngInfo();info.add_text('Title',title)
    out.parent.mkdir(parents=True,exist_ok=True);base.save(out,'PNG',pnginfo=info,optimize=True)
def main():
    import render_site as R, site_layout as L
    tmp=Path(tempfile.mkdtemp())/'site';R.build(tmp)
    serif=fonts();n=0
    want=set()
    for p in sorted(tmp.rglob('*.html')):
        rel=p.relative_to(tmp).as_posix()
        if rel=='page-two/index.html':continue
        s=p.read_text(encoding='utf-8')
        t=re.search(r'<meta property="og:title" content="([^"]*)"',s)
        if not t:raise SystemExit('no og:title on '+rel)
        out=ROOT/L.og_path(rel);want.add(out.name)
        make(unescape(t.group(1)),L.art_for(rel),serif,out);n+=1
    for old in (ROOT/'assets/og').glob('*.png'):
        if old.name not in want:old.unlink()
    shutil.rmtree(tmp.parent);print(f'{n} og images in assets/og/')
if __name__=='__main__':main()
