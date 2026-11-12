// Whole-site look: no text over text or art, and no text under 4.5:1, at 390, 768, 1440 and 1920.
import {test, expect} from '@playwright/test';
import {mkdir, writeFile} from 'node:fs/promises';
import path from 'node:path';

const WIDTHS = [320, 390, 768, 1440, 1920];
const OUT = process.env.FAMILY_SHOTS || '/opt/cursor/artifacts/family-shots';

test('Every page: text does not overlap, contrast is at least 4.5:1', async ({page, request}, info) => {
  test.setTimeout(900_000);
  test.skip(info.project.name !== 'desktop-1440', 'sets its own viewports');
  const sitemap = await (await request.get('/sitemap.xml')).text();
  const routes = [...sitemap.matchAll(/<loc>https:\/\/governedlogic\.com([^<]*)<\/loc>/g)].map(m => m[1] || '/');
  expect(routes.length).toBeGreaterThan(30);
  const fails = [];
  for (const width of WIDTHS) {
    await page.setViewportSize({width, height: 900});
    for (const route of routes) {
      // /page-two/ is the frozen previous homepage. It does not load the brand CSS, and only its favicon link may change.
      if (route === '/page-two/') {
        const file = path.join(OUT, String(width), 'page-two.png');
        await mkdir(path.dirname(file), {recursive: true});
        await page.goto(route, {waitUntil: 'load'});
        await page.screenshot({path: file, fullPage: true});
        continue;
      }
      await page.goto(route, {waitUntil: 'load'});
      await page.evaluate(() => document.fonts.ready);
      const slug = (route === '/' ? 'home' : route.replace(/^\/|\/$/g, '').replaceAll('/', '__')) + '.png';
      const file = path.join(OUT, String(width), slug);
      await mkdir(path.dirname(file), {recursive: true});
      await page.screenshot({path: file, fullPage: true});
      const problems = await page.evaluate(() => {
        const parse = c => {
          const raw = String(c);
          const m = raw.match(/rgba?\(([^)]+)\)/);
          if (m) {
            const p = m[1].split(',').map(x => parseFloat(x));
            return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1};
          }
          const s = raw.match(/color\(srgb\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)(?:\s*\/\s*([0-9.]+))?\)/);
          if (s) return {r: Number(s[1]) * 255, g: Number(s[2]) * 255, b: Number(s[3]) * 255, a: s[4] ? Number(s[4]) : 1};
          return null;
        };
        const lin = c => {
          c /= 255;
          return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
        };
        const L = ({r, g, b}) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
        const over = (top, bot) => ({
          r: top.r * top.a + bot.r * (1 - top.a),
          g: top.g * top.a + bot.g * (1 - top.a),
          b: top.b * top.a + bot.b * (1 - top.a),
          a: 1
        });
        const ratio = (fg, bg) => {
          const a = L(fg), b = L(bg);
          const hi = Math.max(a, b), lo = Math.min(a, b);
          return (hi + 0.05) / (lo + 0.05);
        };
        const paint = el => {
          const layers = [];
          for (let e = el; e; e = e.parentElement) {
            const c = parse(getComputedStyle(e).backgroundColor);
            if (c && c.a > 0.01) layers.push(c);
            if (c && c.a >= 0.99) break;
          }
          if (!layers.length) return {r: 3, g: 5, b: 10, a: 1};
          let acc = {r: 3, g: 5, b: 10, a: 1};
          for (let i = layers.length - 1; i >= 0; i--) acc = over(layers[i], acc);
          return acc;
        };
        const shown = el => {
          const s = getComputedStyle(el);
          if (s.display === 'none' || s.visibility === 'hidden' || Number(s.opacity) === 0) return false;
          const r = el.getBoundingClientRect();
          return r.width > 2 && r.height > 2;
        };
        const direct = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
        const textEls = [...document.querySelectorAll('h1,h2,h3,h4,p,li,a,button,summary,label,dt,dd,small,figcaption,span')].filter(el => shown(el) && direct(el));
        const artEls = [...document.querySelectorAll('img,svg')].filter(el => shown(el) && !el.closest('.gl-twp-banner, .gl-brand-hero, .gl-twp-hero'));
        const bad = [];
        for (const el of textEls) {
          const fg = parse(getComputedStyle(el).color);
          if (!fg) continue;
          const value = ratio(fg, paint(el));
          if (value < 4.5) bad.push(`contrast ${value.toFixed(2)} ${el.tagName} ${(el.textContent || '').trim().slice(0, 40)}`);
          if (bad.length > 8) break;
        }
        const pieces = nodes => nodes.flatMap(el => [...el.getClientRects()].map(r => ({el, r})));
        const textPieces = pieces(textEls);
        const artPieces = pieces(artEls);
        const label = n => n.tagName + ' ' + ((n.textContent || n.getAttribute('alt') || '').trim().slice(0, 24));
        const hit = (ra, rb) => {
          const w = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
          const h = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
          return w > 3 && h > 3;
        };
        let hits = 0;
        for (let i = 0; i < textPieces.length && hits < 6; i++) {
          for (let j = i + 1; j < textPieces.length; j++) {
            const a = textPieces[i], b = textPieces[j];
            if (a.el === b.el || a.el.contains(b.el) || b.el.contains(a.el)) continue;
            if (hit(a.r, b.r)) { bad.push(`overlap ${label(a.el)} / ${label(b.el)}`); hits++; break; }
          }
        }
        for (const a of textPieces) {
          if (hits > 8) break;
          for (const b of artPieces) {
            if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
            if (hit(a.r, b.r)) { bad.push(`overlap ${label(a.el)} / art ${label(b.el)}`); hits++; break; }
          }
        }
        const toggle = document.querySelector('#gl-home-bar .gl-nav-toggle');
        if (toggle) {
          const ts = getComputedStyle(toggle);
          const tr = toggle.getBoundingClientRect();
          const toggleShown = ts.display !== 'none' && ts.visibility !== 'hidden' && Number(ts.opacity) !== 0 && tr.width > 2 && tr.height > 2;
          if (toggleShown) {
            const inside = tr.left >= -0.5 && tr.top >= -0.5 && tr.right <= innerWidth + 0.5 && tr.bottom <= innerHeight + 0.5 && tr.width >= 44 && tr.height >= 44;
            if (!inside) bad.push(`menu toggle outside viewport ${Math.round(tr.left)}..${Math.round(tr.right)} of ${innerWidth}`);
            const mid = document.elementFromPoint(tr.left + tr.width / 2, tr.top + tr.height / 2);
            if (!mid || (mid !== toggle && !toggle.contains(mid))) bad.push('menu toggle not tappable');
          }
        }
        return bad;
      });
      for (const problem of problems) fails.push(`${route}@${width} ${problem}`);
    }
  }
  await writeFile(path.join(OUT, 'failures.txt'), fails.join('\n'), 'utf8');
  expect(fails).toEqual([]);
});
