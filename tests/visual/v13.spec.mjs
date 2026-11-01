// v13 (Paul's v13 approval, Nov 1 2026, 12:30 PM ET; QA research 2026-11-01): one spine, CLS, the machine layer under
// Paul's parity rule, and link coverage (C1 reversed, Paul 12:31 PM ET). Each test sets its own viewports, so it runs
// once (desktop-1440 project).
import {test,expect} from '@playwright/test';
const routes=['/','/challenge/','/company/','/research/','/about/','/faq/','/concepts/','/concepts/governed-logic/','/concepts/governed-intelligence/','/concepts/ultimate-grounding/','/concepts/alpha-and-omega-reasoning/','/concepts/governing-referent/','/concepts/sufficient-grounding/','/mechanism.html','/sources/','/articles/why-anything/','/articles/integrity-in-artificial-intelligence/','/page-two/','/library/','/publication/'];
const norm=s=>s.replace(/[\u2018\u2019]/g,"'").replace(/[\u201c\u201d]/g,'"').replace(/[\u2013\u2014]/g,'-').replace(/\s+/g,' ').trim();
test.beforeEach(({},info)=>{test.skip(info.project.name!=='desktop-1440','sets its own viewports');});

test('Inner pages start title, cards and footer on one spine (73px at 1440, 22px at 390)',async({page})=>{
 test.setTimeout(120_000);
 // /page-two/ is Paul's previous homepage and keeps its own layout; / is the homepage hero.
 for(const [width,spine] of [[1440,73],[390,22]]){
  await page.setViewportSize({width,height:900});
  for(const route of routes.filter(r=>r!=='/'&&r!=='/page-two/')){
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

test('Link coverage: every page reachable by ordinary links, every link resolves, nothing unpublished linked',async({page,request})=>{
 test.setTimeout(180_000);
 const seen=new Set(['/']);const queue=['/'];const bad=[];const checked=new Map();
 while(queue.length){
  const route=queue.shift();await page.goto(route,{waitUntil:'domcontentloaded'});
  const hrefs=await page.evaluate(()=>[...document.querySelectorAll('a[href]')].map(a=>a.href));
  for(const h of hrefs){const u=new URL(h);if(u.origin!==new URL(page.url()).origin)continue;
   if(/^\/principles\//.test(u.pathname))bad.push(`${route} links unpublished ${u.pathname}`);
   if(!checked.has(u.pathname))checked.set(u.pathname,(await request.get(u.pathname)).status());
   if(checked.get(u.pathname)!==200)bad.push(`${route} -> ${u.pathname} ${checked.get(u.pathname)}`);
   const p=u.pathname.replace(/\/index\.html$/,'/');
   if(routes.includes(p)&&!seen.has(p)){seen.add(p);queue.push(p);}}
 }
 expect(bad).toEqual([]);
 expect([...seen].sort()).toEqual([...routes].sort());
 expect((await request.get('/principles/being/')).status(),'principle pages unpublished').toBe(404);
});
