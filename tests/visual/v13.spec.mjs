// v13 (Paul's v13 approval, Nov 1 2026, 12:30 PM ET; QA research 2026-11-01): one spine, CLS, the machine layer under
// Paul's parity rule, and link coverage (C1 reversed, Paul 12:31 PM ET). Each test sets its own viewports, so it runs
// once (desktop-1440 project).
import {test,expect} from '@playwright/test';
const routes=['/','/challenge/','/company/','/research/','/about/','/faq/','/concepts/','/concepts/governed-logic/','/concepts/governed-intelligence/','/concepts/ultimate-grounding/','/concepts/alpha-and-omega-reasoning/','/concepts/governing-referent/','/concepts/sufficient-grounding/','/mechanism.html','/sources/','/articles/why-anything/','/articles/integrity-in-artificial-intelligence/','/page-two/','/library/','/publication/'];
// Principle pages, set B (Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified)). No Truth page.
const principles={'/principles/being/':'Being','/principles/identity/':'Identity','/principles/meaning/':'Meaning','/principles/intelligibility/':'Intelligibility','/principles/logic/':'Logic','/principles/correspondence/':'Correspondence','/principles/obligation/':'Obligation'};
const withheldPrinciples=['/principles/truth/'];
const norm=s=>s.replace(/[\u2018\u2019]/g,"'").replace(/[\u201c\u201d]/g,'"').replace(/[\u2013\u2014]/g,'-').replace(/\s+/g,' ').trim();
test.beforeEach(({},info)=>{test.skip(info.project.name!=='desktop-1440','sets its own viewports');});

test('Inner pages start title, cards and footer on one spine (73px at 1440, 22px at 390)',async({page})=>{
 test.setTimeout(120_000);
 // /page-two/ is Paul's previous homepage and keeps its own layout; / is the homepage hero.
 for(const [width,spine] of [[1440,73],[390,22]]){
  await page.setViewportSize({width,height:900});
  for(const route of [...routes.filter(r=>r!=='/'&&r!=='/page-two/'),...Object.keys(principles)]){
   await page.goto(route,{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
   const m=await page.evaluate(()=>{const rg=document.createRange();
    const left=e=>{if(!e)return null;rg.selectNodeContents(e);const r=[...rg.getClientRects()].filter(x=>x.width>0);return r.length?Math.round(r[0].left):null};
    // /about/ from 1100px: the portrait sits on the spine and the h1 beside it, so the band's first edge is the portrait.
    const portrait=document.querySelector('.about-hero .about-portrait');const pr=portrait&&getComputedStyle(portrait).display!=='none'?portrait.getBoundingClientRect():null;
    const t=left(document.querySelector('main h1'));
    return {title:pr&&Math.round(pr.left)<t?Math.round(pr.left):t,footer:left(document.querySelector('.site-footer .footer-name')),
     card:left(document.querySelector('main :is(.business-section,.concept-card,details.faq-item,.library-item,.source-entry) :is(h2,h3,summary,p)'))};});
   expect(Math.abs(m.title-spine),`h1 left edge ${m.title} on ${route} at ${width}`).toBeLessThanOrEqual(1);
   expect(Math.abs(m.footer-spine),`footer left edge ${m.footer} on ${route} at ${width}`).toBeLessThanOrEqual(1);
   if(m.card!==null)expect(Math.abs(m.card-spine),`card text left edge ${m.card} on ${route} at ${width}`).toBeLessThanOrEqual(1);
  }
 }
});

test('Late web fonts do not shift layout: CLS below 0.1',async({page})=>{
 // QA research 2026-11-01: /mechanism.html at 390 measured 0.1165 before v13. Fonts are held back 300ms.
 await page.route('**/*.woff2',async r=>{await new Promise(x=>setTimeout(x,300));await r.continue();});
 for(const [route,width] of [['/mechanism.html',390],['/mechanism.html',1440],['/concepts/governed-logic/',390],['/concepts/governed-logic/',1440]]){
  await page.setViewportSize({width,height:width<500?844:900});
  await page.addInitScript(()=>{window.__cls=0;new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)window.__cls+=e.value;}).observe({type:'layout-shift',buffered:true});});
  await page.goto(route,{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(800);
  const cls=await page.evaluate(()=>window.__cls);
  expect(cls,`CLS on ${route} at ${width}`).toBeLessThan(0.1);
 }
});

test('Machine layer matches the visible text (terms.jsonld, dfn, llms.txt)',async({page,request})=>{
 test.setTimeout(120_000);
 const set=await (await request.get('/terms.jsonld')).json();
 expect(set['@type']).toBe('DefinedTermSet');expect(set.hasDefinedTerm.length).toBe(12);
 for(const t of set.hasDefinedTerm){
  const u=new URL(t['@id']);await page.goto(u.pathname,{waitUntil:'domcontentloaded'});
  const m=await page.evaluate(([frag,code])=>{const target=document.getElementById(frag);const d=frag==='concept'?document.getElementById('concept'):target&&target.querySelector('dfn');
   return {target:!!target,dfn:d?d.tagName:null,dfnText:d?d.textContent:'',style:d?getComputedStyle(d).fontStyle===getComputedStyle(d.parentElement).fontStyle:false,text:document.body.innerText};},[u.hash.slice(1),t.termCode]);
  expect(m.target,`fragment ${t['@id']}`).toBe(true);
  expect(m.dfn,`dfn for ${t.name}`).toBe('DFN');
  expect(m.style,`dfn renders like its text for ${t.name}`).toBe(true);
  expect(norm(m.text).includes(norm(t.description)),`visible definition of ${t.name}`).toBe(true);
 }
 const llms=await (await request.get('/llms.txt')).text();
 for(const [,label,url,text] of llms.matchAll(/^- \[(.+?)\]\((\S+?)\)(?:: (.*))?$/gm)){
  const u=new URL(url);const r=await request.get(u.pathname);expect(r.ok(),`llms.txt link ${url}`).toBeTruthy();
  if(!/\.html$|\/$/.test(u.pathname))continue;
  await page.goto(u.pathname,{waitUntil:'domcontentloaded'});const body=norm(await page.evaluate(()=>document.body.innerText));
  if(text)expect(body.includes(norm(text)),`llms.txt text on ${u.pathname}`).toBe(true);
 }
});

test('Link coverage: every page and the seven principle pages reachable by ordinary links, every link resolves, nothing unpublished linked',async({page,request})=>{
 test.setTimeout(180_000);
 const seen=new Set(['/']);const queue=['/'];const bad=[];const checked=new Map();
 while(queue.length){
  const route=queue.shift();await page.goto(route,{waitUntil:'domcontentloaded'});
  const hrefs=await page.evaluate(()=>[...document.querySelectorAll('a[href]')].map(a=>a.href));
  for(const h of hrefs){const u=new URL(h);if(u.origin!==new URL(page.url()).origin)continue;
   if(/^\/principles\//.test(u.pathname)&&!(u.pathname in principles))bad.push(`${route} links unpublished ${u.pathname}`);
   if(!checked.has(u.pathname))checked.set(u.pathname,(await request.get(u.pathname)).status());
   if(checked.get(u.pathname)!==200)bad.push(`${route} -> ${u.pathname} ${checked.get(u.pathname)}`);
   const p=u.pathname.replace(/\/index\.html$/,'/');
   if((routes.includes(p)||p in principles)&&!seen.has(p)){seen.add(p);queue.push(p);}}
 }
 expect(bad).toEqual([]);
 expect([...seen].sort()).toEqual([...routes,...Object.keys(principles)].sort());
 for(const p of Object.keys(principles))expect((await request.get(p)).status(),`${p} served`).toBe(200);
 for(const p of withheldPrinciples){expect((await request.get(p)).status(),`${p} not published`).toBe(404);expect((await request.get(p+'index.html')).status()).toBe(404);}
 const sitemap=await (await request.get('/sitemap.xml')).text();
 for(const p of Object.keys(principles))expect(sitemap.includes(`<loc>https://governedlogic.com${p}</loc>`),`${p} in sitemap`).toBe(true);
 for(const p of withheldPrinciples)expect(sitemap.includes(p),`${p} absent from sitemap`).toBe(false);
 expect(sitemap.includes('<lastmod>'),'no page dates (Paul 4:50 PM ET Nov 1)').toBe(false);
});

// GL QA F1 on 0ee4a0f (v13 regression): the hero chain label "INTELLIGENCE" was clipped from 920 to 1200px (24px at
// 1024). Every width from 900 to 1280, 1px apart, plus 1024 named: no chain label may overflow its box, a clipping
// ancestor or the viewport.
test('Homepage hero chain labels are never clipped, 900 to 1280px',async({page})=>{
 test.setTimeout(120_000);
 await page.setViewportSize({width:1024,height:900});await page.goto('/',{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
 for(let width=900;width<=1280;width++){
  await page.setViewportSize({width,height:900});
  // The text itself (a Range over the label), not the label's box: a block box may be wider than its words.
  const bad=await page.evaluate(()=>{const out=[];const rg=document.createRange();for(const e of document.querySelectorAll('.gl-chain li > *')){rg.selectNodeContents(e);const r=rg.getBoundingClientRect();
   if(e.scrollWidth>e.clientWidth+1)out.push(`${e.textContent.trim()} overflows its box`);
   if(r.right>innerWidth+0.5)out.push(`${e.textContent.trim()} ends at ${r.right.toFixed(1)} past the viewport`);
   for(let a=e.parentElement;a;a=a.parentElement){const cs=getComputedStyle(a);if(cs.overflowX!=='visible'){const ar=a.getBoundingClientRect();
    if(r.right>ar.right+0.5||r.left<ar.left-0.5)out.push(`${e.textContent.trim()} clipped by ${a.tagName}.${a.className} (${(r.right-ar.right).toFixed(1)}px)`);}}}
   return out;});
  expect(bad,`chain labels at ${width}px`).toEqual([]);
 }
});

// Governor's 2:16 PM ET ruling (Nov 1 2026): Paul loved the homepage sizing, so the homepage keeps the 187fdb4 type
// scale (computed sizes pinned from the 187fdb4 build); the /sources/ card titles keep their 187fdb4 size; the seven-step
// scale (12, 14, 16, 20, 24, 40, 64 at 1440) applies to the other inner pages only.
test('Type: homepage and Sources card titles at 187fdb4 sizes; inner pages on the seven-step scale',async({page})=>{
 test.setTimeout(120_000);
 const home={
  1440:{'#gl-home-bar nav a':'15.5px','.gl-hero-title':'81px','.gl-hero-lede':'20.8px','.gl-chain strong':'17.5px','.gl-core h2':'51.5px','.gl-core-copy>p:not(.gl-eyebrow)':'20.5px','.gl-principles h3':'21px','.gl-problem h2':'52px','.gl-ptitle':'21px','.gl-card-kind':'13px','.gl-card h3':'24.5px','.site-footer .footer-name':'22px'},
  1024:{'#gl-home-bar nav a':'13.5px','.gl-hero-title':'57.6px','.gl-hero-lede':'15px','.gl-chain strong':'12.4444px','.gl-core h2':'36.6222px','.gl-core-copy>p:not(.gl-eyebrow)':'15px','.gl-principles h3':'16px','.gl-problem h2':'36.9778px','.gl-ptitle':'16px','.gl-card-kind':'12px','.gl-card h3':'17.4222px','.site-footer .footer-name':'22px'},
  390:{'#gl-home-bar nav a':'13px','.gl-hero-title':'40.56px','.gl-hero-lede':'16px','.gl-chain strong':'12px','.gl-core h2':'32.76px','.gl-core-copy>p:not(.gl-eyebrow)':'16px','.gl-principles h3':'17px','.gl-problem h2':'32.76px','.gl-ptitle':'17px','.gl-card-kind':'12px','.gl-card h3':'20px','.site-footer .footer-name':'22px'}};
 for(const [width,pins] of Object.entries(home)){
  await page.setViewportSize({width:+width,height:900});await page.goto('/',{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
  const got=await page.evaluate(s=>Object.fromEntries(s.map(x=>[x,(e=>e?getComputedStyle(e).fontSize:null)(document.querySelector('body.gl-home-page '+x))])),Object.keys(pins));
  expect(got,`homepage type at ${width}px`).toEqual(pins);
  // Problem-band card titles wrap as they did at 187fdb4 (2 of 4 on two lines at 1440).
  if(width==='1440'){const lines=await page.evaluate(()=>[...document.querySelectorAll('.gl-ptitle')].map(e=>Math.round(e.getBoundingClientRect().height/parseFloat(getComputedStyle(e).lineHeight))));
   expect(lines,'Problem-band card title lines at 1440').toEqual([1,2,2,1]);}
 }
 await page.setViewportSize({width:1440,height:900});
 const scale=new Set(['12px','14px','16px','20px','24px','40px','64px']);
 for(const route of routes.filter(r=>r!=='/'&&r!=='/page-two/')){
  await page.goto(route,{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
  const off=await page.evaluate(()=>{const o=[];for(const e of document.querySelectorAll('main *')){if(![...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))continue;
   if(!e.getBoundingClientRect().width||e.closest('.source-entry')&&e.tagName==='H2')continue;o.push([e.tagName,getComputedStyle(e).fontSize]);}return o;});
  const bad=off.filter(([,f])=>!scale.has(f));
  expect(bad,`sizes off the seven-step scale on ${route}`).toEqual([]);
 }
 await page.goto('/sources/',{waitUntil:'load'});
 const titles=await page.evaluate(()=>[...document.querySelectorAll('main .source-entry h2')].map(e=>getComputedStyle(e).fontSize));
 expect(titles.length).toBeGreaterThan(0);expect(new Set(titles),'Sources card titles at 1440 (187fdb4: 56px)').toEqual(new Set(['56px']));
});

// Paul 4:48 PM ET Nov 1, set B, publish as written (via Governor, verified): each principle page has exactly one h1, its
// name, as its title, no page date, and no text in main or the footer clipped or past the viewport at 1440, 1024, 390 and
// 320. (The shared header's nav is a sideways-scrolling strip below 1024px on every page, by design; it is not checked here.)
test('Principle pages: one h1 (the name), no page date, nothing clipped at 1440/1024/390/320',async({page})=>{
 test.setTimeout(180_000);
 for(const width of [1440,1024,390,320]){
  await page.setViewportSize({width,height:900});
  for(const [route,name] of Object.entries(principles)){
   await page.goto(route,{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
   const m=await page.evaluate(()=>{const out=[];const rg=document.createRange();
    for(const e of document.querySelectorAll('main :is(h1,h2,h3,p,a,li,span), footer :is(a,p)')){
     if(!e.textContent.trim())continue;rg.selectNodeContents(e);const r=rg.getBoundingClientRect();if(!r.width)continue;
     const label=e.tagName+' '+e.textContent.trim().slice(0,40);
     if(e.scrollWidth>e.clientWidth+1&&getComputedStyle(e).overflowX!=='visible')out.push(`${label} overflows its box`);
     if(r.right>innerWidth+0.5||r.left<-0.5)out.push(`${label} outside the viewport (${r.left.toFixed(1)}..${r.right.toFixed(1)})`);
     for(let a=e.parentElement;a;a=a.parentElement){const cs=getComputedStyle(a);if(cs.overflowX!=='visible'||cs.overflowY!=='visible'){const ar=a.getBoundingClientRect();
      if(r.right>ar.right+0.5||r.left<ar.left-0.5||r.bottom>ar.bottom+0.5&&cs.overflowY!=='visible')out.push(`${label} clipped by ${a.tagName}.${a.className}`);}}}
    if(document.documentElement.scrollWidth>innerWidth)out.push(`page scrolls sideways (${document.documentElement.scrollWidth}px)`);
    return {h1:[...document.querySelectorAll('h1')].map(h=>h.textContent.trim()),title:document.title,text:document.body.innerText,out};});
   expect(m.h1,`h1 on ${route} at ${width}`).toEqual([name]);
   expect(m.title,`title on ${route}`).toBe(`${name} | Governed Logic`);
   expect(/Published\s*\/\s*modified/i.test(m.text),`page date on ${route}`).toBe(false);
   expect(m.out,`clipping on ${route} at ${width}px`).toEqual([]);
  }
 }
});
