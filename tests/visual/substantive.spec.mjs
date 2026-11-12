// C1 reversed (Paul, Nov 1 2026, 12:31 PM ET): navigation is <a href> links now, not GET-form buttons; selectors follow.
import {test,expect} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
const routes=['/','/challenge/','/company/','/research/','/about/','/the-treatises/','/ai-safety/','/mimicry/','/faq/','/concepts/','/concepts/governed-logic/','/concepts/governed-intelligence/','/concepts/ultimate-grounding/','/concepts/alpha-and-omega-reasoning/','/concepts/governing-referent/','/concepts/sufficient-grounding/','/mechanism.html','/sources/','/articles/why-anything/','/articles/integrity-in-artificial-intelligence/','/page-two/','/library/','/publication/',
 // v14 (Paul 2026-11-01 22:34 and 22:36): the articles index and The Truth with Paul placeholder.
 '/articles/','/the-truth-with-paul/'];
// WEB-205/WEB-231: '/page-two/' keeps Paul's previous homepage main reachable.
for(const route of routes){
 test(`${route} substantive content and usable layout`,async({page},info)=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
  const response=await page.goto(route,{waitUntil:'networkidle'});expect(response.ok()).toBeTruthy();
  await expect(page.locator('main')).toHaveCount(1);await expect(page.locator('h1')).toHaveCount(1);
  if(route==='/faq/')for(const summary of await page.locator('main details summary').all())await summary.click();
  // The Truth with Paul placeholder carries exactly its three strings (Paul 2026-11-01 22:36); see its own test.
  // v14.1: /articles/ lists each article once (featured card + Latest rail), so it has no 45-word floor; check-restored
  // and v13.spec check its cards instead.
  if(route!=='/the-truth-with-paul/'&&route!=='/articles/')expect((await page.locator('main').innerText()).split(/\s+/).length).toBeGreaterThan(45);
  await expect(page.getByRole('navigation',{name:'Primary',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
  const images=await page.locator('img').evaluateAll(imgs=>imgs.filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src));expect(images).toEqual([]);
  const headings=await page.locator('main h1,main h2,main h3').evaluateAll(nodes=>nodes.filter(n=>n.scrollWidth>n.clientWidth+1).map(n=>n.textContent));expect(headings).toEqual([]);
  await expect(page.locator('nav[aria-label="Primary"] summary')).toHaveCount(0);
  const links=page.getByRole('navigation',{name:'Primary',exact:true}).getByRole('link');
  for(const link of await links.all()){await link.scrollIntoViewIfNeeded();const box=await link.boundingBox();expect(box.height).toBeGreaterThanOrEqual(43);expect(box.x).toBeGreaterThanOrEqual(0);expect(box.x+box.width).toBeLessThanOrEqual(page.viewportSize().width+1);}
  if(route==='/')await page.locator('#explore').scrollIntoViewIfNeeded();
  const dir=path.resolve('visual-qa/screenshots',info.project.name);await mkdir(dir,{recursive:true});
  await page.screenshot({path:path.join(dir,route==='/'?'home.png':route.slice(1).replace(/\/$/,'').replaceAll('/','-')+'.png'),fullPage:true});
  expect(errors).toEqual([]);
 });
}
test('Library searches restored full text',async({page})=>{
 await page.goto('/library/');await page.getByLabel('Search the library').fill('borrowed authority');
 await expect(page.locator('#library-search-mode')).toContainText('exact text');
 await expect(page.locator('.library-item:visible')).not.toHaveCount(0);
 await page.getByLabel('Search the library').fill('zzzznomatchzzzz');await expect(page.locator('#library-empty')).toBeVisible();
 await page.getByRole('button',{name:'Clear',exact:true}).click();await expect(page.locator('.library-item:visible')).toHaveCount(26); // WEB-205/WEB-231: the library lists /page-two/. Overnight 2026-11-10: The Treatises, AI Safety, Mimicry. Paul 2026-11-11: The Groundless Machine.
});
test('FAQ answers open and match machine data',async({page})=>{
 await page.goto('/faq/');await page.getByText('What exists today?',{exact:true}).click();
 await expect(page.locator('details[open]')).toContainText('working instruction-level prototype');
});
test('Homepage and navigation work without JavaScript',async({browser})=>{
 const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});const page=await context.newPage();
 // WEB-205/WEB-231: the previous homepage text ('Governed Intelligence') is one button away, at /page-two/.
 await page.goto((process.env.BASE_URL || 'http://127.0.0.1:4173')+'/');
 await page.locator('main .gl-go > a[href="/page-two/"]').click();await expect(page).toHaveURL(/\/page-two\/\??$/);await expect(page.locator('main')).toContainText('Governed Intelligence');
 // WEB-228/C9; PLACEMENT_MAP 2026-11-01 (WEB-227 FIFTH) (N6): the homepage header names /concepts/governed-logic/ 'Governed Logic' (L21431).
 await page.goto((process.env.BASE_URL || 'http://127.0.0.1:4173')+'/');
 await page.getByRole('navigation',{name:'Primary',exact:true}).getByRole('link',{name:'The Treatises',exact:true}).click();
 await expect(page.locator('h1')).toHaveText('The Treatises');await context.close();
});
test('Homepage lands on the hero with no opening',async({page})=>{
 // WEB-215 + Paul's C8 ruling (2026-11-01, "drop the old opening"): replaces the opening-completion test. There is no
 // opening region or overlay; the hero headline is the page's one h1 and is on the first screen at load.
 await page.goto('/');
 await expect(page.locator('#site')).toHaveCount(0);
 await expect(page.locator('#glIntro')).toHaveCount(0);
 await expect(page.locator('.scroll-invite')).toHaveCount(0);
 await expect(page.locator('h1')).toHaveCount(1);
 await expect(page.locator('#explore h1.gl-hero-title')).toHaveCount(1);
 await expect(page.locator('#explore h1.gl-hero-title')).toBeInViewport();
});
// WEB-215 + Paul's C8 ruling (2026-11-01): the opening filmstrip test ("Opening records its chronological visual
// sequence") is removed with the opening it recorded; contact-sheet.mjs no longer expects motion frames.
const widths=[320,360,390,768,1440,1920];
test('Headlines do not break or overflow a word',async({page})=>{
 test.setTimeout(300000);
 const offenders=[];
 for(const route of routes){
  for(const width of widths){
   await page.setViewportSize({width,height:900});
   await page.goto(route,{waitUntil:'domcontentloaded'});
   const found=await page.evaluate(()=>{
    const bad=[];
    for(const heading of document.querySelectorAll('h1,h2,h3')){
     const style=getComputedStyle(heading);
     if(style.display==='none'||style.visibility==='hidden')continue;
     if(heading.scrollWidth>heading.clientWidth+1)bad.push(`${heading.tagName} overflow: ${(heading.textContent||'').trim().slice(0,80)}`);
     const walker=document.createTreeWalker(heading,NodeFilter.SHOW_TEXT);
     while(walker.nextNode()){
      const node=walker.currentNode;const text=node.textContent||'';const re=/[^\s\-–—]+/g;let match;
      while((match=re.exec(text))){
       const range=document.createRange();range.setStart(node,match.index);range.setEnd(node,match.index+match[0].length);
       const tops=new Set([...range.getClientRects()].filter(rect=>rect.width>0&&rect.height>0).map(rect=>Math.round(rect.top)));
       if(tops.size>1)bad.push(`wrapped ${match[0]}`);
      }
     }
    }
    return bad;
   });
   for(const item of found)offenders.push(`${route} @${width}: ${item}`);
  }
 }
 expect(offenders).toEqual([]);
});

test('Section 01 text clears 4.5:1 over its scrim',async({page})=>{
 test.setTimeout(120000);
 const failures=[];
 for(const width of widths){
  await page.setViewportSize({width,height:900});
  await page.goto('/',{waitUntil:'domcontentloaded'});
  const ratios=await page.evaluate(()=>{
   const parse=value=>{const m=value.match(/[\d.]+/g);return m?m.slice(0,3).map(Number):null;};
   const lin=c=>{const v=c/255;return v<=0.03928?v/12.92:((v+0.055)/1.055)**2.4;};
   const L=rgb=>0.2126*lin(rgb[0])+0.7152*lin(rgb[1])+0.0722*lin(rgb[2]);
   const contrast=(a,b)=>{const x=L(a),y=L(b);const hi=Math.max(x,y),lo=Math.min(x,y);return (hi+0.05)/(lo+0.05);};
   const out=[];
   // WEB-233/WEB-220: section 01 is the 2026-10-31 hero; the same 4.5:1 rule covers its heading, copy and chain labels.
   // WEB-215 + Paul's C8 ruling (2026-11-01): the hero heading is now h1, so h1 is added to keep it covered.
   for(const node of document.querySelectorAll('#explore h1, #explore h2, #explore p, #explore .gl-chain strong, #explore .gl-chain span')){
    const style=getComputedStyle(node);
    const fg=parse(style.color);const bg=parse(style.backgroundColor);
    if(!fg||!bg){out.push({text:(node.textContent||'').slice(0,40),ratio:0});continue;}
    out.push({text:(node.textContent||'').trim().slice(0,48),ratio:contrast(fg,bg),color:style.color,background:style.backgroundColor});
   }
   return out;
  });
  for(const item of ratios)if(item.ratio<4.5)failures.push(`${width}: ${item.ratio.toFixed(2)} ${item.text} ${item.color} on ${item.background}`);
 }
 expect(failures).toEqual([]);
});

test('Phone nav stays visible at 360px',async({page})=>{
 await page.setViewportSize({width:360,height:800});
 await page.goto('/',{waitUntil:'domcontentloaded'});
 await page.locator('header.site-bar').scrollIntoViewIfNeeded();
 const metrics=await page.evaluate(()=>{
  const bar=document.querySelector('header.site-bar');
  const buttons=[...document.querySelectorAll('nav[aria-label="Primary"] .gl-go > a')];
  const boxes=buttons.map(button=>{const r=button.getBoundingClientRect();return {w:r.width,h:r.height,top:r.top,name:(button.textContent||'').trim()};});
  const tops=boxes.map(box=>Math.round(box.top));
  return {
   count:buttons.length,
   summary:document.querySelector('nav[aria-label="Primary"] summary')?1:0,
   details:document.querySelector('nav[aria-label="Primary"] details')?1:0,
   overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,
   headerHeight:bar?bar.getBoundingClientRect().height:0,
   oneRow:tops.length>0&&tops.every(top=>top===tops[0]),
   boxes
  };
 });
 expect(metrics.summary).toBe(0);
 expect(metrics.details).toBe(0);
 expect(metrics.count).toBe(6); // Home, The Treatises, AI Safety, Mimicry, Research, About.
 expect(metrics.overflow).toBe(false);
 // Phone nav is a drawer (2026-11-11). Closed header is one 64px row. Open it and every target is at least 44px.
 expect(metrics.headerHeight).toBeLessThanOrEqual(64);
 expect(metrics.headerHeight).toBeGreaterThanOrEqual(44);
 const toggle=page.locator('#gl-home-bar .gl-nav-toggle');
 await expect(toggle).toBeVisible();
 const toggleBox=await toggle.boundingBox();
 expect(toggleBox.height).toBeGreaterThanOrEqual(44);
 expect(toggleBox.width).toBeGreaterThanOrEqual(44);
 await toggle.click();
 const open=await page.evaluate(()=>{
  const buttons=[...document.querySelectorAll('nav[aria-label="Primary"] .gl-go > a')];
  return {overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,
   boxes:buttons.map(button=>{const r=button.getBoundingClientRect();return {w:r.width,h:r.height,name:(button.textContent||'').trim()};})};
 });
 expect(open.overflow).toBe(false);
 expect(open.boxes).toHaveLength(6);
 for(const box of open.boxes){
  expect(box.h,box.name).toBeGreaterThanOrEqual(44);
  expect(box.w,box.name).toBeGreaterThanOrEqual(44);
 }
});

test('Phone header wraps the nav from 320 to 899: every item whole, in view and one tap away',async({page})=>{
 // v14 (Paul 2026-11-01 22:34; QA layout 2026-11-01, the 390 nav strip cut words off): at every phone width the header
 // keeps the full brand, Search (/library/) and the CTA in view, and the nav wraps onto 44px rows (v14.1: two at every
 // phone width, 132px; it was three at 320) with every item whole and in view without scrolling; nothing scrolls sideways.
 for(const [width,maxH] of [[320,64],[360,64],[390,64],[600,64],[899,64]]){
  await page.setViewportSize({width,height:800});
  await page.goto('/',{waitUntil:'domcontentloaded'});
  const m=await page.evaluate(()=>{
   const bar=document.querySelector('header#gl-home-bar');
   const inView=el=>{const r=el.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=0&&r.right<=innerWidth+0.5&&r.top>=0&&r.bottom<=bar.getBoundingClientRect().bottom+0.5;};
   const fixed=['.gl-brand-name','.site-brand small','.gl-go > a[href="/library/"]','.gl-bar-cta'].map(sel=>inView(bar.querySelector(sel)));
   return {h:bar.getBoundingClientRect().height,fixed,scroll:bar.scrollWidth>bar.clientWidth+1,pageX:scrollX,overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};
  });
  expect(m.h,`header height at ${width}`).toBeLessThanOrEqual(maxH);
  expect(m.fixed,`brand, subline, search and CTA in view at ${width}`).toEqual([true,true,true,true]);
  expect(m.scroll,`header scrolls sideways at ${width}`).toBe(false);
  expect(m.pageX).toBe(0);
  expect(m.overflow).toBe(false);
  await page.locator('#gl-home-bar .gl-nav-toggle').click();
  const open=await page.evaluate(()=>{
   const items=[...document.querySelectorAll('#gl-home-bar nav .gl-go > a')];
   const whole=items.filter(a=>{const r=a.getBoundingClientRect();return !(r.width>0&&r.height>0&&r.left>=0&&r.right<=innerWidth+0.5&&a.scrollWidth<=a.clientWidth+1);}).map(a=>a.textContent.trim());
   const hit=items.filter(a=>{const r=a.getBoundingClientRect();return !a.contains(document.elementFromPoint(r.left+r.width/2,r.top+r.height/2));}).map(a=>a.textContent.trim());
   const current=[...items].filter(a=>a.getAttribute('aria-current')==='page').map(a=>a.textContent.trim());
   return {whole,hit,count:items.length,current,overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};
  });
  expect(open.count,`nav count at ${width}`).toBe(6);
  expect(open.whole,`nav items cut off at ${width}`).toEqual([]);
  expect(open.hit,`nav items not clickable at ${width}`).toEqual([]);
  expect(open.current,`only the current page is active at ${width}`).toEqual(['Home']);
  expect(open.overflow).toBe(false);
 }
});

test('Mid-width header is one row of 72px or less from 900 to 1279',async({page})=>{
 // Round 4 (WEB-214, WEB-223, WEB-226): like the mockup, 900-1279 keeps one header row at or under 72px, with the
 // brand, all six nav items (Company and About included; PLACEMENT_MAP dropped Applications; QA-4 restored About), Search and the CTA side by side, in view, unclipped and 44px tall.
 for(const width of [900,1024,1279]){
  await page.setViewportSize({width,height:900});
  await page.goto('/',{waitUntil:'domcontentloaded'});
  const m=await page.evaluate(()=>{
   const bar=document.querySelector('header#gl-home-bar');const b=bar.getBoundingClientRect();
   const items=[bar.querySelector('.site-brand'),...bar.querySelectorAll('nav a'),bar.querySelector('.gl-go > a[href="/library/"]')];
   const boxes=items.map(el=>el.getBoundingClientRect());
   let ordered=true;for(let i=1;i<boxes.length;i++)if(boxes[i].left<boxes[i-1].right-0.5)ordered=false;
   return {h:b.height,count:items.length,ordered,
    inView:boxes.every(r=>r.left>=0&&r.right<=innerWidth+0.5&&r.top>=b.top-0.5&&r.bottom<=b.bottom+0.5),
    tall:boxes.slice(1).every(r=>r.height>=43.5&&r.width>=43.5),
    hit:items.every(el=>{const r=el.getBoundingClientRect();return el.contains(document.elementFromPoint(r.left+r.width/2,r.top+r.height/2));}),
    company:!!bar.querySelector('nav .gl-go > a[href="/about/"]'),
    cta:bar.querySelector('.gl-bar-cta').textContent.trim(),
    scroll:bar.scrollWidth>bar.clientWidth+1,
    overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};
  });
  expect(m.h,`header height at ${width}`).toBeLessThanOrEqual(72);
  expect(m.count).toBe(8); // brand, six nav items, Search. Homepage header CTA is hidden (2032).
  expect(m.ordered,`one row, no overlap at ${width}`).toBe(true);
  expect(m.inView,`every header item in view at ${width}`).toBe(true);
  expect(m.tall).toBe(true);
  expect(m.hit,`every header item clickable at ${width}`).toBe(true);
  expect(m.company).toBe(true);
  expect(m.cta).toBe('Explore the research method'); // N11 (PLACEMENT_MAP, L21394; Round 5b)
  expect(m.scroll).toBe(false);
  expect(m.overflow).toBe(false);
 }
});

test('Header CTA reads the N11 text and never collides with brand or Search',async({page})=>{
 // N11 (PLACEMENT_MAP, L21394; Round 5b): "Explore the research method" in full, at every width; it sets on two lines
 // at 390-599 and is the compact arrow button (same accessible name) below 390 and at 900-1099 (v14: was 900-1023).
 // v14: the phone header grows by the wrapped nav rows (v14.1: two at every phone width, 132px; was 180 at 320, 136 from 360).
 const heights={320:64,360:64,390:64,414:64,440:64,899:64,900:72,1024:72,1279:72,1440:108};
 for(const [w,hh] of Object.entries(heights)){
  const width=Number(w);
  await page.setViewportSize({width,height:900});
  await page.goto('/',{waitUntil:'domcontentloaded'});
  const m=await page.evaluate(()=>{
   const bar=document.querySelector('header#gl-home-bar');
   const brand=bar.querySelector('.site-brand'),search=bar.querySelector('.gl-go > a[href="/library/"]'),cta=bar.querySelector('.gl-bar-cta');
   const [b,s,c]=[brand,search,cta].map(el=>el.getBoundingClientRect());
   const sub=bar.querySelector('.site-brand small'),sr=sub.getBoundingClientRect(),ss=getComputedStyle(sub);
   const lum=x=>{const v=x.match(/[\d.]+/g).slice(0,3).map(n=>{n/=255;return n<=.03928?n/12.92:((n+.055)/1.055)**2.4});return .2126*v[0]+.7152*v[1]+.0722*v[2]};
   const fg=lum(getComputedStyle(cta).color),bg=lum(getComputedStyle(bar).backgroundColor);
   return {h:Math.round(bar.getBoundingClientRect().height),text:cta.textContent.replace(/\s+/g,' ').trim(),
    gaps:[s.left-b.right,c.left-s.right],ctaW:c.width,ctaH:c.height,
    hit:cta.contains(document.elementFromPoint(c.left+c.width/2,c.top+c.height/2)),
    sub:ss.display!=='none'&&ss.visibility!=='hidden'&&sr.width>0&&sr.right<=s.left,
    clipped:cta.querySelector('.gl-cta-label').getBoundingClientRect().width>2&&(cta.scrollWidth>cta.clientWidth+1||cta.scrollHeight>cta.clientHeight+1),
    contrast:(Math.max(fg,bg)+.05)/(Math.min(fg,bg)+.05),
    overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};
  });
  expect(m.text).toBe('Explore the research method');
  const a11y=await page.evaluate(()=>{const cta=document.querySelector('#gl-home-bar .gl-bar-cta');cta.focus();return{visibility:getComputedStyle(cta).visibility,focused:document.activeElement===cta};});
  expect(a11y.visibility,`CTA hidden from view at ${width}`).toBe('hidden');
  expect(a11y.focused,`CTA not focusable at ${width}`).toBe(false);
  expect(await page.locator('#gl-home-bar').ariaSnapshot(),`CTA absent from header a11y tree at ${width}`).not.toMatch(/Explore the research method/);
  expect(m.h,`header height at ${width}`).toBe(hh);
  expect(m.gaps[0],`brand clears Search at ${width}`).toBeGreaterThanOrEqual(0);
  expect(m.sub,`REASONING SYSTEMS visible at ${width}`).toBe(true);
  expect(m.overflow).toBe(false);
 }
});

test('Homepage buttons hold their text at every width',async({page})=>{
 // QA-1, QA-2 (Round 5b): no homepage button's label or arrow may spill out of its box, including the Problem button
 // "Large Language Model Defects", both "Explore the research method" buttons and the header CTA.
 for(const width of [320,390,1024,1280,1440]){
  await page.setViewportSize({width,height:900});
  await page.goto('/',{waitUntil:'domcontentloaded'});
  const bad=await page.evaluate(()=>{
   const out=[];
   for(const b of document.querySelectorAll('header#gl-home-bar button, main button, header#gl-home-bar a.gl-link, main a.gl-link')){
    const r=b.getBoundingClientRect();if(!r.width||b.closest('.site-brand')||b.matches('.site-brand')||b.classList.contains('gl-nav-toggle'))continue;
    const label=b.querySelector('.gl-cta-label');if(label&&label.getBoundingClientRect().width<=2)continue; // compact CTA: label is visually hidden on purpose
    const range=document.createRange();range.selectNodeContents(b);const t=range.getBoundingClientRect();
    if(b.scrollWidth>b.clientWidth+1||b.scrollHeight>b.clientHeight+1||t.left<r.left-0.5||t.right>r.right+0.5||t.top<r.top-0.5||t.bottom>r.bottom+0.5)
     out.push(`${b.textContent.trim()} sw=${b.scrollWidth} cw=${b.clientWidth}`);
   }
   return out;
  });
  expect(bad,`buttons spilling at ${width}`).toEqual([]);
  for(const name of ['Large Language Model Defects','Explore the research method']){
   const count=await page.locator('main a.gl-link, main button',{hasText:name}).count();
   expect(count,`${name} present at ${width}`).toBeGreaterThan(0);
  }
 }
});

test('Phone nav does not scroll sideways and shows no edge fade',async({page})=>{
 // v14 (Paul 2026-11-01 22:34): the wrapped phone nav replaces the sideways-scrolling row (Round 4, WEB-214, WEB-226),
 // so its edge fades are gone: no header scroll range and no fade pseudo-element at 320, 390 or 899, on any page type.
 for(const route of ['/','/about/','/concepts/ultimate-grounding/','/the-truth-with-paul/'])for(const width of [320,390,899]){
  await page.setViewportSize({width,height:800});
  await page.goto(route,{waitUntil:'domcontentloaded'});
  const m=await page.evaluate(()=>{const bar=document.querySelector('header#gl-home-bar');const a=getComputedStyle(bar,'::after'),b=getComputedStyle(bar,'::before');
   return {scrolls:bar.scrollWidth>bar.clientWidth+1,after:a.content==='none'||a.display==='none'||+a.opacity===0,before:b.content==='none'||b.display==='none'||+b.opacity===0};});
  expect(m,`${route} at ${width}`).toEqual({scrolls:false,after:true,before:true});
 }
});

// WEB-215 + Paul's C8 ruling (2026-11-01): "Intro skip is immediate and the first click still lands" is removed with the
// opening overlay (#glIntro) and its scroll invite.
test('No logo fly-up: no .gl-chime ever, the hero h1 is visible at load and the first click lands',async({page})=>{
 // Visual refresh, structural part (Paul, first hand: no fly-up): home-chime.js is removed. With and without reduced
 // motion there is never a .gl-chime element, the hero h1 is in view at load, and the first click on the hero action lands.
 for(const motion of ['reduce','no-preference']){
  await page.emulateMedia({reducedMotion:motion});
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('.gl-chime')).toHaveCount(0);
  await expect(page.locator('h1')).toHaveCount(1);
  await expect(page.locator('#explore h1.gl-hero-title')).toBeInViewport();
  await page.waitForTimeout(400);
  await expect(page.locator('.gl-chime')).toHaveCount(0);
  const cta=page.locator('#explore .gl-actions .gl-go > a[href="/research/"]');
  expect(await cta.evaluate(b=>{const r=b.getBoundingClientRect();return b.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}),motion).toBe(true);
  await cta.click();
  await expect(page).toHaveURL(/\/research\/\??$/);
 }
 expect(await page.evaluate(()=>[...document.scripts].some(s=>/home-chime/.test(s.src)))).toBe(false);
});
test('Labels are at least 12px and controls at least 44px',async({page})=>{
 test.setTimeout(180000);
 const problems=[];
 for(const width of [320,390,1440]){
  await page.setViewportSize({width,height:900});
  for(const route of ['/','/about/','/concepts/governed-logic/','/publication/','/articles/','/articles/why-anything/','/the-truth-with-paul/','/principles/logic/','/company/']){
   await page.goto(route,{waitUntil:'domcontentloaded'});
   const found=await page.evaluate(()=>{
    const bad=[];
    const seen=document.body.querySelectorAll('header,main,footer,p,span,a,button,h1,h2,h3,small,figcaption,li,dt,dd,label');
    for(const node of seen){
     if(node.closest('svg,script,style'))continue;
     const style=getComputedStyle(node);
     if(style.display==='none'||style.visibility==='hidden')continue;
     const size=parseFloat(style.fontSize);
     if(node.childNodes.length&&[...node.childNodes].some(child=>child.nodeType===3&&child.textContent.trim())&&size<11.5)bad.push(`size ${size} ${(node.textContent||'').trim().slice(0,40)}`);
    }
    for(const node of document.querySelectorAll('a,button')){
     const style=getComputedStyle(node);
     if(style.display==='none'||style.visibility==='hidden')continue;
     if(!node.getClientRects().length)continue; // not rendered (inside the closed v14 treatise contents drawer)
     const rect=node.getBoundingClientRect();
     if(rect.width<43.5||rect.height<43.5)bad.push(`target ${Math.round(rect.width)}x${Math.round(rect.height)} ${(node.textContent||node.getAttribute('aria-label')||'').trim().slice(0,40)}`);
    }
    return bad;
   });
   for(const item of found)problems.push(`${route}@${width} ${item}`);
  }
 }
 expect(problems).toEqual([]);
});

test('Every route has the shared header and no horizontal overflow at 390 and 1440',async({page})=>{
 // v12 site-wide look (Paul, Nov 1 2026; WEB-227 SIXTH): all 20 routes carry the homepage header (header#gl-home-bar)
 // and footer, and no route scrolls sideways at the phone or desktop width (viewports set explicitly).
 for(const width of [390,1440]){
  await page.setViewportSize({width,height:900});
  for(const route of routes){
   await page.goto(route,{waitUntil:'domcontentloaded'});
   const m=await page.evaluate(()=>{const h=document.querySelector('header#gl-home-bar.site-bar');const r=h&&h.getBoundingClientRect();
    return {header:!!h&&r.height>=44&&r.top<=0.5&&getComputedStyle(h).visibility!=='hidden',footer:!!document.querySelector('footer.site-footer'),
     brand:!!(h&&h.querySelector('.site-brand img')),overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};});
   expect(m.header,`header on ${route} at ${width}`).toBe(true);
   expect(m.brand,`brand mark on ${route} at ${width}`).toBe(true);
   expect(m.footer,`footer on ${route} at ${width}`).toBe(true);
   expect(m.overflow,`horizontal overflow on ${route} at ${width}`).toBe(false);
  }
 }
});

test('Inner pages: dark title band, full-width footer, Sources sidebar and button gaps hold at 390 and 1440',async({page})=>{
 test.setTimeout(120_000);
 // v12 round 2 (QA F4, Q1, Q2; WEB-227 SIXTH). Every inner route opens on a dark band behind its h1 (homepage hero
 // rhythm) with light h1 text, the footer spans the page, nothing (body included) is wider than the viewport, the
 // two buttons atop /mechanism.html are at least 8px apart (QA v12-cc71761 T1: CSS gap is 32px across, 8px when wrapped), and Sources-sidebar URLs never overflow or break mid-word.
 for(const width of [390,1440]){
  await page.setViewportSize({width,height:900});
  for(const route of routes.filter(r=>r!=='/'&&r!=='/the-truth-with-paul/')){ // The Truth with Paul: its own deep-blue hero (v14 test)
   await page.goto(route,{waitUntil:'load'});await page.waitForTimeout(300);
   const m=await page.evaluate(()=>{
    const h1=document.querySelector('h1');const band=h1.closest('.gl-intro,.about-hero')||document.querySelector('main .front-door');
    const bg=band?getComputedStyle(band,'::before').backgroundImage:'';
    const f=document.querySelector('footer.site-footer').getBoundingClientRect();
    const urls=[...document.querySelectorAll('aside.provenance a')].filter(b=>/^https:\/\//.test(b.textContent));
    const midword=urls.some(b=>{const r=document.createRange();const t=b.firstChild&&b.textContent;let lines=new Map();
     for(const n of b.childNodes){if(n.nodeType!==3)continue;for(let i=0;i<n.length;i++){r.setStart(n,i);r.setEnd(n,i+1);const y=Math.round(r.getBoundingClientRect().top);const prev=lines.get('last');
      if(prev!==undefined&&y>prev+2&&i>0&&n.data[i-1]!=='/')return true;lines.set('last',y);}}return false;});
    const head=band&&!band.contains(h1)?band.querySelector('h2'):h1; // /page-two/ keeps its visually hidden h1 outside main; its band headline is the h2
    return {band:!!band&&bg.includes('rgb(0, 5, 10)'),h1:getComputedStyle(head).color,footer:Math.abs(f.width-document.documentElement.clientWidth)<=1,
     body:document.body.scrollWidth<=document.documentElement.clientWidth+1,urlOverflow:urls.some(b=>b.scrollWidth>b.clientWidth+1),midword};});
   expect(m.band,`dark title band on ${route} at ${width}`).toBe(true);
   expect(m.h1,`light h1 on the band on ${route} at ${width}`).toBe('rgb(255, 255, 255)');
   expect(m.footer,`full-width footer on ${route} at ${width}`).toBe(true);
   expect(m.body,`body wider than the viewport on ${route} at ${width}`).toBe(true);
   expect(m.urlOverflow,`Sources URL overflow on ${route} at ${width}`).toBe(false);
   expect(m.midword,`Sources URL broken mid-word on ${route} at ${width}`).toBe(false);
  }
  await page.goto('/mechanism.html',{waitUntil:'load'});await page.waitForTimeout(300);
  const gap=await page.evaluate(()=>{const b=[...document.querySelectorAll('main .gl-intro>nav .gl-go>a')].map(x=>x.getBoundingClientRect());
   return b.length===2?(Math.abs(b[0].top-b[1].top)<2?b[1].left-b[0].right:b[1].top-b[0].bottom):-1;});
  expect(gap,`gap between the /mechanism.html buttons at ${width}`).toBeGreaterThanOrEqual(8);
 }
});
