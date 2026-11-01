import {test,expect} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
const routes=['/','/challenge/','/company/','/research/','/about/','/faq/','/concepts/','/concepts/governed-logic/','/concepts/governed-intelligence/','/concepts/ultimate-grounding/','/concepts/alpha-and-omega-reasoning/','/concepts/governing-referent/','/concepts/sufficient-grounding/','/mechanism.html','/sources/','/articles/why-anything/','/articles/integrity-in-artificial-intelligence/','/page-two/','/library/','/publication/'];
// WEB-205/WEB-231: '/page-two/' keeps Paul's previous homepage main reachable.
for(const route of routes){
 test(`${route} substantive content and usable layout`,async({page},info)=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
  const response=await page.goto(route,{waitUntil:'networkidle'});expect(response.ok()).toBeTruthy();
  await expect(page.locator('main')).toHaveCount(1);await expect(page.locator('h1')).toHaveCount(1);
  if(route==='/faq/')for(const summary of await page.locator('main details summary').all())await summary.click();
  expect((await page.locator('main').innerText()).split(/\s+/).length).toBeGreaterThan(45);
  await expect(page.getByRole('navigation',{name:'Primary',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
  const images=await page.locator('img').evaluateAll(imgs=>imgs.filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src));expect(images).toEqual([]);
  const headings=await page.locator('main h1,main h2,main h3').evaluateAll(nodes=>nodes.filter(n=>n.scrollWidth>n.clientWidth+1).map(n=>n.textContent));expect(headings).toEqual([]);
  await expect(page.locator('nav[aria-label="Primary"] summary')).toHaveCount(0);
  const links=page.getByRole('navigation',{name:'Primary',exact:true}).getByRole('button');
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
 await page.getByRole('button',{name:'Clear',exact:true}).click();await expect(page.locator('.library-item:visible')).toHaveCount(22); // WEB-205/WEB-231: the library lists /page-two/.
});
test('FAQ answers open and match machine data',async({page})=>{
 await page.goto('/faq/');await page.getByText('What exists today?',{exact:true}).click();
 await expect(page.locator('details[open]')).toContainText('working instruction-level prototype');
});
test('Homepage and navigation work without JavaScript',async({browser})=>{
 const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});const page=await context.newPage();
 // WEB-205/WEB-231: the previous homepage text ('Governed Intelligence') is one button away, at /page-two/.
 await page.goto((process.env.BASE_URL || 'http://127.0.0.1:4173')+'/');
 await page.locator('main form.gl-go[method="get"][action="/page-two/"] button[type="submit"]').click();await expect(page).toHaveURL(/\/page-two\/\??$/);await expect(page.locator('main')).toContainText('Governed Intelligence');
 // WEB-228/C9 (provisional mockup nav): the homepage header names /concepts/governed-logic/ 'The Framework'.
 await page.goto((process.env.BASE_URL || 'http://127.0.0.1:4173')+'/');
 await page.getByRole('navigation',{name:'Primary',exact:true}).getByRole('button',{name:'The Framework',exact:true}).click();
 await expect(page.locator('h1')).toHaveText('Governed Logic');await context.close();
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
  const buttons=[...document.querySelectorAll('nav[aria-label="Primary"] form.gl-go > button')];
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
 expect(metrics.count).toBe(6); // C9/WEB-217/WEB-223: six linked items (Applications is held, not a form); Company added.
 expect(metrics.overflow).toBe(false);
 // D8 (WEB-214/WEB-223/WEB-226): the phone header is two 44px rows, brand/search/CTA over one nav row that scrolls
 // sideways inside the header, so it stays at 88px or less.
 expect(metrics.headerHeight).toBeLessThanOrEqual(88);
 expect(metrics.headerHeight).toBeGreaterThanOrEqual(44);
 expect(new Set(metrics.boxes.map(box=>Math.round(box.top))).size).toBeLessThanOrEqual(2);
 for(const box of metrics.boxes){
  expect(box.h).toBeGreaterThanOrEqual(44);
  expect(box.w).toBeGreaterThanOrEqual(44);
 }
});

test('Phone header is 88px or less from 320 to 899 with every item one tap away',async({page})=>{
 // D8 (WEB-214/WEB-223/WEB-226): at every phone width the header keeps the full brand, Search (/library/) and the CTA in
 // view, stays at or under 88px, and scrolling the header (not the page) brings Company into view.
 for(const width of [320,360,390,600,899]){
  await page.setViewportSize({width,height:800});
  await page.goto('/',{waitUntil:'domcontentloaded'});
  const m=await page.evaluate(()=>{
   const bar=document.querySelector('header#gl-home-bar');
   const inView=el=>{const r=el.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=0&&r.right<=innerWidth+0.5&&r.top>=0&&r.bottom<=bar.getBoundingClientRect().bottom+0.5;};
   const fixed=['.gl-brand-name','.site-brand small','form[action="/library/"] > button','.gl-bar-cta'].map(sel=>inView(bar.querySelector(sel)));
   const company=bar.querySelector('form[action="/company/"] > button');
   company.scrollIntoView({block:'nearest',inline:'nearest'});
   return {h:bar.getBoundingClientRect().height,fixed,company:inView(company),fixedAfter:['.gl-brand-name','.gl-bar-cta'].map(sel=>inView(bar.querySelector(sel))),pageX:scrollX,overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};
  });
  expect(m.h,`header height at ${width}`).toBeLessThanOrEqual(88);
  expect(m.fixed,`brand, subline, search and CTA in view at ${width}`).toEqual([true,true,true,true]);
  expect(m.company,`Company in view at ${width}`).toBe(true);
  expect(m.fixedAfter,`brand and CTA stay pinned at ${width}`).toEqual([true,true]);
  expect(m.pageX).toBe(0);
  expect(m.overflow).toBe(false);
 }
});

test('Mid-width header is one row of 72px or less from 900 to 1279',async({page})=>{
 // Round 4 (WEB-214, WEB-223, WEB-226): like the mockup, 900-1279 keeps one header row at or under 72px, with the
 // brand, all seven nav items (Company included), Search and the CTA side by side, in view, unclipped and 44px tall.
 for(const width of [900,1024,1279]){
  await page.setViewportSize({width,height:900});
  await page.goto('/',{waitUntil:'domcontentloaded'});
  const m=await page.evaluate(()=>{
   const bar=document.querySelector('header#gl-home-bar');const b=bar.getBoundingClientRect();
   const items=[bar.querySelector('.site-brand'),...bar.querySelectorAll('nav button'),bar.querySelector('form[action="/library/"] > button'),bar.querySelector('.gl-bar-cta')];
   const boxes=items.map(el=>el.getBoundingClientRect());
   let ordered=true;for(let i=1;i<boxes.length;i++)if(boxes[i].left<boxes[i-1].right-0.5)ordered=false;
   return {h:b.height,count:items.length,ordered,
    inView:boxes.every(r=>r.left>=0&&r.right<=innerWidth+0.5&&r.top>=b.top-0.5&&r.bottom<=b.bottom+0.5),
    tall:boxes.slice(1).every(r=>r.height>=43.5&&r.width>=43.5),
    hit:items.every(el=>{const r=el.getBoundingClientRect();return el.contains(document.elementFromPoint(r.left+r.width/2,r.top+r.height/2));}),
    company:!!bar.querySelector('nav form[action="/company/"] > button'),
    cta:bar.querySelector('.gl-bar-cta').textContent.trim(),
    scroll:bar.scrollWidth>bar.clientWidth+1,
    overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};
  });
  expect(m.h,`header height at ${width}`).toBeLessThanOrEqual(72);
  expect(m.count).toBe(10);
  expect(m.ordered,`one row, no overlap at ${width}`).toBe(true);
  expect(m.inView,`every header item in view at ${width}`).toBe(true);
  expect(m.tall).toBe(true);
  expect(m.hit,`every header item clickable at ${width}`).toBe(true);
  expect(m.company).toBe(true);
  expect(m.cta).toBe('Explore the Research');
  expect(m.scroll).toBe(false);
  expect(m.overflow).toBe(false);
 }
});

test('Phone nav edge fade follows the header scroll',async({page})=>{
 // Round 4 (WEB-214, WEB-226): the right-edge fade shows while the phone nav has more items to the right and is gone at
 // the scroll end; it never takes pointer events, and a nav that fits shows no fade.
 const fade=async(left)=>page.evaluate(async(x)=>{const bar=document.querySelector('header#gl-home-bar');if(x!==null)bar.scrollLeft=x;
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  const a=getComputedStyle(bar,'::after'),b=getComputedStyle(bar,'::before');
  return {right:+a.opacity,left:+b.opacity,events:a.pointerEvents,scrolls:bar.scrollWidth>bar.clientWidth+1,h:bar.getBoundingClientRect().height};},left);
 await page.setViewportSize({width:320,height:800});
 await page.goto('/',{waitUntil:'domcontentloaded'});
 const start=await fade(null);
 expect(start.scrolls).toBe(true);
 expect(start.h).toBeLessThanOrEqual(88);
 expect(start.events).toBe('none');
 expect(start.right).toBeGreaterThan(0.9);
 expect(start.left).toBeLessThan(0.1);
 const end=await fade(99999);
 expect(end.right).toBeLessThan(0.1);
 expect(end.left).toBeGreaterThan(0.9);
 await page.setViewportSize({width:899,height:800});
 await page.goto('/',{waitUntil:'domcontentloaded'});
 const fits=await fade(null);
 expect(fits.scrolls).toBe(false);
 expect(fits.right).toBeLessThan(0.1);
 expect(fits.left).toBeLessThan(0.1);
});

// WEB-215 + Paul's C8 ruling (2026-11-01): "Intro skip is immediate and the first click still lands" is removed with the
// opening overlay (#glIntro) and its scroll invite.
test('Logo chime never blocks content, plays once, and is skipped under reduced motion',async({page})=>{
 // Paul, 2026-11-01 (C8, WEB-215; WEB-227 FIFTH): a short logo chime replaces the old opening. Under reduced motion
 // there is none; otherwise it is aria-hidden, takes no pointer events, the hero h1 is visible at load and the first
 // click lands, and it does not replay in the same session.
 await page.goto('/',{waitUntil:'domcontentloaded'});
 await page.waitForTimeout(300);
 await expect(page.locator('.gl-chime')).toHaveCount(0);
 await page.emulateMedia({reducedMotion:'no-preference'});
 await page.goto('/',{waitUntil:'domcontentloaded'});
 const chime=page.locator('.gl-chime');
 await expect(chime).toHaveCount(1);
 await expect(chime).toHaveAttribute('aria-hidden','true');
 await expect(chime).toHaveCSS('pointer-events','none');
 await expect(page.locator('h1')).toHaveCount(1);
 await expect(page.locator('#explore h1.gl-hero-title')).toBeInViewport();
 const cta=page.locator('#explore .gl-actions form[action="/research/"] button');
 expect(await cta.evaluate(b=>{const r=b.getBoundingClientRect();return b.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})).toBe(true);
 await cta.click();
 await expect(page).toHaveURL(/\/research\/\??$/);
 await page.goto('/',{waitUntil:'domcontentloaded'});
 await page.waitForTimeout(300);
 await expect(page.locator('.gl-chime')).toHaveCount(0);
});
test('Labels are at least 12px and controls at least 44px',async({page})=>{
 test.setTimeout(180000);
 const problems=[];
 for(const width of [320,390,1440]){
  await page.setViewportSize({width,height:900});
  for(const route of ['/','/about/','/concepts/governed-logic/','/publication/']){
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
