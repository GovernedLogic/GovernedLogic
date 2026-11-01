"""Generate the colour layer of assets/site.css from assets/restored-site.css (v12, WEB-227 SIXTH).

Every colour-bearing declaration of the inner-page stylesheet is re-emitted under :where(body.gl-site), at its original specificity, with its colour
moved to the homepage palette: content sits on the homepage's white paper (#f9f8f8) with near-black ink, and light
accents become the homepage's deep blue. Header, footer and skip-link rules are left to home.css. Hand-written
layout and type rules follow the marker in site.css and are kept as they are. Run: python3 scripts/make_site_css.py
"""
import colorsys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC, OUT = ROOT / 'assets/restored-site.css', ROOT / 'assets/site.css'
MARK = '/* ---- hand-written: type, layout and fixes (kept by make_site_css.py) ---- */'
PAPER, INK = (249, 248, 248), (11, 17, 24)
COLOR_PROPS = re.compile(r'^(color|background(-color|-image)?|border(-(top|right|bottom|left))?(-color)?|outline(-color)?|box-shadow|text-shadow|fill|stroke|caret-color|text-decoration(-color)?|column-rule(-color)?|--[\w-]+)$')
SKIP_SEL = re.compile(r'site-bar|site-brand|site-footer|skip-link|footer-|#gl-home-bar')
NAMED = {'#fff': '#ffffff', '#000': '#000000', 'white': '#ffffff', 'black': '#000000'}
COLOR = re.compile(r'#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|\b(?:white|black)\b')

def parse(c):
    c = NAMED.get(c.lower(), c)
    if c.startswith('#'):
        h = c[1:]
        if len(h) in (3, 4): h = ''.join(x * 2 for x in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1
        return r, g, b, a
    v = [x.strip() for x in re.split(r'[ ,/]+', c[c.index('(') + 1:-1]) if x.strip()]
    r, g, b = (float(x) for x in v[:3])
    a = float(v[3][:-1]) / 100 if len(v) > 3 and v[3].endswith('%') else float(v[3]) if len(v) > 3 else 1
    return r, g, b, a

def fmt(r, g, b, a):
    r, g, b = (max(0, min(255, round(x))) for x in (r, g, b))
    return f'#{r:02x}{g:02x}{b:02x}' if a >= .999 else f'rgba({r},{g},{b},{a:.3g})'

def mix(c1, c2, t): return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))

def remap(c, kind):
    r, g, b, a = parse(c)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    sat = s > .22 and .08 < l < .97
    if kind == 'shadow':
        return fmt(9, 20, 32, a * .3) if l < .5 else fmt(*INK, a * .5)
    if a < .999 and not sat:                      # translucent overlays: white veils become faint ink veils
        return fmt(*INK, a * .7) if l > .5 else fmt(9, 20, 32, a * .35)
    if sat:                                       # accents: keep the hue, set it deep (homepage blue family)
        hh = .575 if .5 < h < .7 else h
        if kind == 'text': rr, gg, bb = colorsys.hls_to_rgb(hh, .34, min(1, s * 1.1))
        elif kind == 'line': rr, gg, bb = colorsys.hls_to_rgb(hh, .62, min(.8, s))
        else: rr, gg, bb = colorsys.hls_to_rgb(hh, .94 if l < .5 else .30, min(.9, s))
        return fmt(rr * 255, gg * 255, bb * 255, a)
    if kind == 'text':                            # light text -> dark ink; dark text (on light chips) -> light
        return fmt(*mix(INK, (88, 99, 110), max(0, min(1, (.95 - l) / .45))), a) if l > .5 else fmt(*mix(PAPER, (205, 212, 218), l / .5), a)
    if kind == 'line':
        return fmt(*mix((214, 221, 227), (236, 239, 242), max(0, min(1, (.2 - l) / .2))), a) if l < .5 else fmt(*mix((150, 160, 170), (60, 70, 80), (l - .5) / .5), a)
    if l < .5:                                    # dark surfaces -> paper / white cards
        if l < .02: return fmt(*PAPER, a)
        return fmt(*mix((255, 255, 255), (226, 231, 236), min(1, (l - .02) / .16)), a)
    return fmt(*mix((0, 48, 89), INK, (l - .5) / .5), a)   # light fills (inverse buttons) -> homepage navy

def kind_of(prop, value):
    if prop in ('box-shadow', 'text-shadow'): return 'shadow'
    if prop.startswith('border') or prop.startswith('outline') or prop.startswith('column-rule') or prop == 'stroke' or prop == 'text-decoration-color' or prop == 'text-decoration': return 'line'
    if prop in ('color', 'fill', 'caret-color'): return 'text'
    if prop.startswith('--'):
        n = prop[2:]
        return 'text' if re.search(r'ink|muted|accent|text|blue|green|track', n) else 'line' if re.search(r'line', n) else 'bg'
    return 'bg'

def scope(sel):
    out = []
    for s in sel.split(','):
        s = s.strip()
        if not s: continue
        if SKIP_SEL.search(s): return None
        # :where() adds no specificity, so each re-coloured rule keeps the weight and order it has in restored-site.css.
        if s in (':root', 'html', 'html:root', 'body'): out.append('body.gl-site'); continue
        if s.startswith('body'): out.append('body:where(.gl-site)' + s[4:]); continue
        if re.match(r'\.(document-page|library-page)\b', s): out.append(':where(body.gl-site)' + s); continue
        if s.startswith('html'): s = s.split(' ', 1)[1] if ' ' in s else s
        out.append(':where(body.gl-site) ' + s)
    return ','.join(out)

def rules(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    i, out, stack = 0, [], []
    while i < len(css):
        j = css.find('{', i); k = css.find('}', i)
        if j == -1 or (k != -1 and k < j):
            if k == -1: break
            if stack: stack.pop()
            i = k + 1; continue
        head = css[i:j].strip()
        if head.startswith('@media') or head.startswith('@supports'):
            stack.append(head); i = j + 1; continue
        if head.startswith('@'):                  # @font-face, @keyframes: skip whole block
            depth, m = 0, j
            while m < len(css):
                if css[m] == '{': depth += 1
                elif css[m] == '}':
                    depth -= 1
                    if depth == 0: break
                m += 1
            i = m + 1; continue
        k = css.find('}', j)
        out.append((tuple(stack), head, css[j + 1:k])); i = k + 1
    return out

def main():
    lines = []
    for media, sel, body in rules(SRC.read_text(encoding='utf-8')):
        sc = scope(sel)
        if not sc: continue
        decls = []
        for d in body.split(';'):
            if ':' not in d: continue
            p, v = d.split(':', 1); p = p.strip(); v = v.strip()
            if not COLOR_PROPS.match(p) or not COLOR.search(v): continue
            kind = kind_of(p, v)
            v2 = COLOR.sub(lambda m: remap(m.group(0), 'line' if kind == 'bg' and p.startswith('border') else kind), v)
            decls.append(f'{p}:{v2}')
        if not decls: continue
        rule = sc + '{' + ';'.join(decls) + '}'
        for m in reversed(media): rule = m + '{' + rule + '}'
        lines.append(rule)
    old = OUT.read_text(encoding='utf-8') if OUT.exists() else ''
    tail = old[old.index(MARK):] if MARK in old else MARK + '\n'
    head = ('/* Site-wide look for every page except the homepage (v12, Paul, Nov 1 2026; WEB-227 SIXTH). Style only.\n'
            '   Loaded after restored-site.css and home.css on body.gl-site pages. The colour layer below is generated by\n'
            '   scripts/make_site_css.py from restored-site.css: the homepage palette (white paper, near-black ink, deep blue). */\n')
    OUT.write_text(head + '\n'.join(lines) + '\n' + tail, encoding='utf-8')
    print(f'{len(lines)} colour rules -> {OUT.relative_to(ROOT)}')

if __name__ == '__main__':
    main()
