// v13 (Paul's v13 approval, Nov 1 2026, 12:30 PM ET; QA research 2026-11-01): one spine, CLS, the machine layer under
// Paul's parity rule, and link coverage (C1 reversed, Paul 12:31 PM ET). Each test sets its own viewports, so it runs
// once (desktop-1440 project).
import {test,expect} from '@playwright/test';
import {createHash} from 'node:crypto';
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

// ---- v14 design rollout (Paul 2026-11-01 22:34 "Let's get this big push out."; 22:36 "It's not a company yet") ----
const v14Routes=[...routes.filter(r=>r!=='/page-two/'),...Object.keys(principles),'/articles/','/the-truth-with-paul/'];
const v14Articles={'/articles/why-anything/':'Why Anything?','/articles/integrity-in-artificial-intelligence/':'Integrity in Artificial Intelligence'};
test('v14: one header everywhere (page-two keeps its own), art above the fold, social tags equal the visible h1',async({page,request})=>{
 test.setTimeout(240_000);
 const bad=[];
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:900});
  for(const route of v14Routes){
   await page.goto(route,{waitUntil:'load'});
   const m=await page.evaluate(()=>{
    const bar=document.querySelector('header#gl-home-bar');const labels=[...document.querySelectorAll('header#gl-home-bar nav a')].map(a=>a.textContent.trim());
    // The homepage's art is the signature field (its Seed of Life img is removed): its aria-hidden svg, drawn and in view.
    const sig=document.querySelector('body.gl-home-page #explore .gl-hero-art > svg.gl-sig[aria-hidden="true"]');const sr=sig&&sig.getBoundingClientRect();
    const art=[...document.querySelectorAll('main img')].some(i=>{const r=i.getBoundingClientRect();return r.width>40&&r.height>40&&r.top<innerHeight&&r.bottom>0&&i.complete&&i.naturalWidth>0;})
     ||(!!sr&&sr.width>40&&sr.height>40&&sr.top<innerHeight&&sr.bottom>0&&sig.querySelectorAll('circle').length>0);
    const meta=k=>[...document.querySelectorAll(`meta[property="${k}"],meta[name="${k}"]`)].map(x=>x.content);
    const h1=document.querySelector('h1').textContent.replace(/\s+/g,' ').trim();
    return {labels,tools:!!bar.querySelector('.gl-bar-cta')&&!!bar.querySelector('.gl-search'),art,h1,ogTitle:meta('og:title'),card:meta('twitter:card'),img:meta('og:image'),url:meta('og:url'),tw:['title','description','image'].map(k=>JSON.stringify(meta('twitter:'+k))),og:['title','description','image'].map(k=>JSON.stringify(meta('og:'+k))),desc:meta('description'),canon:document.querySelector('link[rel=canonical]').href};
   });
   const want=['Home','The problem','Research','Governed Logic','About','Company','The Truth with Paul'];
   if(JSON.stringify(m.labels)!==JSON.stringify(want))bad.push(`${route}@${width} header ${m.labels}`);
   if(!m.tools)bad.push(`${route}@${width} header tools missing`);
   if(!m.art)bad.push(`${route}@${width} no art above the fold`);
   if(width===1440){
    const h1=route==='/'?'Governed Logic Reasoning Systems':m.h1;
    if(JSON.stringify(m.ogTitle)!==JSON.stringify([h1]))bad.push(`${route} og:title ${m.ogTitle} != ${h1}`);
    if(JSON.stringify(m.card)!=='["summary_large_image"]')bad.push(`${route} twitter:card ${m.card}`);
    if(m.url[0]!==m.canon)bad.push(`${route} og:url ${m.url} != canonical`);
    // v14.1 (Vera's nits b, c): twitter:title/description/image identical to og; og:description is the visible lede (meta description).
    if(JSON.stringify(m.tw)!==JSON.stringify(m.og))bad.push(`${route} twitter ${m.tw} != og ${m.og}`);
    if(m.og[1]!==JSON.stringify(m.desc))bad.push(`${route} og:description ${m.og[1]} != meta description`);
    for(const d of m.desc)if(!(await page.locator('body').innerText()).replace(/\s+/g,' ').toLowerCase().includes(d.toLowerCase()))bad.push(`${route} description not visible`); // CSS uppercase eyebrows
    if(m.img.length!==1||!m.img[0].startsWith('https://governedlogic.com/assets/og/'))bad.push(`${route} og:image ${m.img}`);
    else{const r=await request.get(m.img[0].replace('https://governedlogic.com',''));const b=await r.body();
     if(!r.ok()||b.readUInt32BE(16)!==1200||b.readUInt32BE(20)!==627)bad.push(`${route} og:image not a served 1200x627 PNG`);}
   }
  }
 }
 await page.setViewportSize({width:1440,height:900});await page.goto('/page-two/',{waitUntil:'load'});
 const two=await page.evaluate(()=>[...document.querySelectorAll('header nav a')].map(a=>a.textContent.trim()));
 if(JSON.stringify(two)!==JSON.stringify(['Governed Logic','Ultimate Grounding','Governed Intelligence','Company','Research']))bad.push('page-two header changed: '+two);
 // v14.1: /page-two/ is kept exactly as it was; its phone header keeps its v14 height (two 44px nav rows plus 4px at
 // 320-599 phones, one row plus 4px at 600-899) while the other pages tighten to 132px.
 for(const [w,hh] of [[320,136],[390,136],[600,92],[899,92]]){
  await page.setViewportSize({width:w,height:800});await page.goto('/page-two/',{waitUntil:'load'});
  const h=await page.evaluate(()=>Math.round(document.querySelector('header').getBoundingClientRect().height));
  if(h!==hh)bad.push(`page-two header ${h}px at ${w} (was ${hh})`);
 }
 expect(bad).toEqual([]);
});
test('v14.1: /articles/ is a featured card and one Latest snap rail; each live article is listed once',async({page})=>{
 await page.setViewportSize({width:1440,height:900});
 await page.goto('/articles/',{waitUntil:'load'});
 const m=await page.evaluate(()=>({h1:document.querySelector('h1').textContent,featured:document.querySelectorAll('.gl-featured .gl-card').length,
  grid:document.querySelectorAll('.gl-art-grid').length,
  titles:[...document.querySelectorAll('.gl-card h3')].map(h=>h.textContent.trim()),kinds:[...new Set([...document.querySelectorAll('.gl-card-kind')].map(k=>k.textContent))],
  snap:getComputedStyle(document.querySelector('.gl-rail')).scrollSnapType,rails:document.querySelectorAll('.gl-rail').length,
  hrefs:[...document.querySelectorAll('.gl-card a.gl-card-go')].map(a=>a.getAttribute('href'))}));
 expect(m.h1).toBe('Articles');expect(m.featured).toBe(1);expect(m.grid).toBe(0);expect(m.rails).toBe(1);
 expect(m.snap).toContain('x');expect(m.kinds).toEqual(['Article']);
 expect([...m.titles].sort()).toEqual(Object.values(v14Articles).sort());
 expect([...m.hrefs].sort()).toEqual(Object.keys(v14Articles).sort());
 for(const [route,h1] of Object.entries(v14Articles)){await page.goto(route);expect((await page.locator('h1').textContent()).trim()).toBe(h1);}
});
test('v14: article pages have a dark hero with art, a wide measure and a plain-link share row with Copy link',async({page,context})=>{
 await context.grantPermissions(['clipboard-read','clipboard-write']);
 for(const [route] of Object.entries(v14Articles)){
  await page.setViewportSize({width:1440,height:900});
  await page.goto(route,{waitUntil:'load'});
  const m=await page.evaluate(()=>{const share=document.querySelector('nav.gl-share');const p=document.querySelector('main article > p');
   return {labels:[...share.querySelectorAll('a,button')].map(a=>a.textContent.trim()),hrefs:[...share.querySelectorAll('a')].map(a=>a.getAttribute('href')),
    measure:p.getBoundingClientRect().width,third:[...document.scripts].filter(s=>s.src&&!s.src.startsWith(location.origin)).length,
    article:JSON.parse([...document.querySelectorAll('script[type="application/ld+json"]')].map(s=>s.textContent).find(t=>t.includes('"Article"'))),
    band:getComputedStyle(document.querySelector('.gl-intro'),'::before').backgroundImage};});
  expect(m.labels).toEqual(['LinkedIn','Reddit','X','Copy link']);
  const url=encodeURIComponent('https://governedlogic.com'+route);
  expect(m.hrefs[0]).toBe(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`);
  expect(m.hrefs[1].startsWith(`https://www.reddit.com/submit?url=${url}&title=`)).toBe(true);
  expect(m.hrefs[2].startsWith(`https://x.com/intent/post?url=${url}&text=`)).toBe(true);
  expect(m.measure).toBeGreaterThanOrEqual(700);expect(m.measure).toBeLessThanOrEqual(780);
  expect(m.third).toBe(0);
  expect(m.article.headline).toBe(v14Articles[route]);expect(Object.keys(m.article).some(k=>k.startsWith('date'))).toBe(false);
  await page.getByRole('button',{name:'Copy link'}).click();
  await expect(page.locator('.gl-share .gl-copied')).toHaveText('Copied');
  expect(await page.evaluate(()=>navigator.clipboard.readText())).toBe('https://governedlogic.com'+route);
 }
});
test('v14: treatises are micro-sites (masthead, sticky contents rail or drawer, reading progress, chapter pager)',async({page})=>{
 for(const route of ['/concepts/ultimate-grounding/','/concepts/governed-logic/']){
  await page.setViewportSize({width:1440,height:900});
  await page.goto(route,{waitUntil:'load'});
  const h2=await page.evaluate(()=>[...document.querySelectorAll('main section.business-section[id]')].map(s=>[s.id,s.querySelector('h2').textContent.replace(/\s+/g,' ').trim()]));
  const toc=await page.evaluate(()=>[...document.querySelectorAll('#gl-toc a')].map(a=>[a.getAttribute('href').slice(1),a.textContent.replace(/\s+/g,' ').trim()]));
  expect(toc).toEqual(h2);
  expect(await page.locator('.gl-pager').count()).toBe(h2.length);
  for(const href of await page.locator('.gl-pager a').evaluateAll(as=>as.map(a=>a.getAttribute('href'))))expect(h2.map(x=>'#'+x[0])).toContain(href);
  const p0=await page.evaluate(()=>+getComputedStyle(document.querySelector('.gl-progress>span')).getPropertyValue('--gl-read')||0);
  await page.evaluate(()=>window.scrollTo(0,document.body.scrollHeight/2));await page.waitForTimeout(150);
  const mid=await page.evaluate(()=>{const r=document.getElementById('gl-toc').getBoundingClientRect();const bar=document.querySelector('.gl-treatise-bar').getBoundingClientRect();
   return {read:+document.querySelector('.gl-progress>span').style.getPropertyValue('--gl-read'),toc:r.top>=0&&r.top<innerHeight,bar:bar.top>=0&&bar.top<200,current:document.querySelectorAll('#gl-toc a[aria-current="true"]').length};});
  expect(mid.read).toBeGreaterThan(p0);expect(mid.toc).toBe(true);expect(mid.bar).toBe(true);expect(mid.current).toBe(1);
  await page.setViewportSize({width:390,height:844});
  await page.goto(route,{waitUntil:'load'});
  await expect(page.locator('#gl-toc')).toBeHidden();
  await page.getByRole('button',{name:'Contents'}).click();
  await expect(page.locator('#gl-toc')).toBeVisible();
  await expect(page.getByRole('button',{name:'Contents'})).toHaveAttribute('aria-expanded','true');
  await page.locator('#gl-toc a').nth(1).click();
  await expect(page.locator('#gl-toc')).toBeHidden();
  expect(page.url()).toContain('#'+h2[1][0]);
 }
});
test('v14: principle and concept pages carry the enlarged principle tile and the related-principles band',async({page})=>{
 for(const route of [...Object.keys(principles),'/concepts/governing-referent/','/concepts/sufficient-grounding/','/concepts/governed-intelligence/','/concepts/alpha-and-omega-reasoning/']){
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:900});await page.goto(route,{waitUntil:'load'});
   const m=await page.evaluate(()=>{const t=document.querySelector('.gl-intro .gl-tile').getBoundingClientRect();
    return {tile:Math.round(t.width),inView:t.top<innerHeight,band:[...document.querySelectorAll('nav.principle-nav a')].map(a=>a.textContent.trim()),icons:document.querySelectorAll('nav.principle-nav .gl-rel-icon').length,
     overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};});
   expect(m.tile,`${route}@${width}`).toBeGreaterThanOrEqual(64);expect(m.inView).toBe(true);
   expect(m.band).toEqual(Object.values(principles));expect(m.icons).toBe(7);expect(m.overflow).toBe(false);
  }
 }
});
test('v14: The Truth with Paul is a coming-soon media page: three strings, one h1, a plain Subscribe link, motion only without reduced motion',async({page})=>{
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:900});await page.goto('/the-truth-with-paul/',{waitUntil:'load'});
  const m=await page.evaluate(()=>{const a=document.querySelector('main a');const hero=document.querySelector('.gl-twp-hero');
   return {text:document.querySelector('main').innerText.replace(/\s+/g,' ').trim(),h1:[...document.querySelectorAll('h1')].map(h=>h.textContent),href:a.getAttribute('href'),label:a.textContent.trim(),tag:a.tagName,
    bg:getComputedStyle(hero).backgroundImage,heroH:hero.getBoundingClientRect().height,btn:a.getBoundingClientRect(),anim:[getComputedStyle(document.querySelector('.gl-twp-seed')).animationName,getComputedStyle(document.querySelector('.gl-twp-soon')).animationName],
    imgs:[...document.querySelectorAll('main img')].map(i=>i.getAttribute('src')),overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,
    current:document.querySelector('header nav a[href="/the-truth-with-paul/"]').getAttribute('aria-current')};});
  expect(m.text.toLowerCase()).toBe('the truth with paul coming soon subscribe on youtube');
  expect(m.h1).toEqual(['The Truth with Paul']);
  expect(m.tag).toBe('A');expect(m.href).toBe('https://www.youtube.com/@TheTruthwithPaul');expect(m.label).toBe('Subscribe on YouTube');
  expect(m.bg).toContain('radial-gradient');expect(m.btn.height).toBeGreaterThanOrEqual(44);expect(m.btn.bottom).toBeLessThanOrEqual(900);
  expect(m.anim).toEqual(['none','none']);
  expect(m.imgs).toEqual(['/assets/provisional/hero-geometry.svg','/assets/provisional/seed-of-life.png']);
  expect(m.overflow).toBe(false);expect(m.current).toBe('page');
 }
 await page.emulateMedia({reducedMotion:'no-preference'});await page.goto('/the-truth-with-paul/');
 expect(await page.evaluate(()=>getComputedStyle(document.querySelector('.gl-twp-seed')).animationName)).toBe('gl-twp-turn');
});
test('v14: no page dates in any page, og/twitter tag or feed (source edition lines excepted); feed.xml is RSS 2.0',async({page,request})=>{
 const DATE=/\b\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b|\b20\d\d-\d\d-\d\d\b/;
 const editionPages=['/sources/','/library/','/publication/'];
 const bad=[];
 for(const route of v14Routes){
  await page.goto(route,{waitUntil:'domcontentloaded'});
  const m=await page.evaluate(()=>({metas:[...document.querySelectorAll('meta[property^="og:"],meta[name^="twitter:"]')].map(x=>x.content).join(' '),
   // The Sources and version box (aside.provenance) cites source editions by their edition date; it is kept as it was.
   lines:[...document.querySelectorAll('main p,main dd,main li,main span')].filter(e=>!e.closest('aside.provenance')).map(e=>e.textContent.replace(/\s+/g,' ').trim())}));
  if(DATE.test(m.metas))bad.push(`${route} date in og/twitter`);
  if(!editionPages.includes(route))for(const l of m.lines)if(DATE.test(l)&&!/Source edition|·\s*\d{1,2} \w+ \d{4}\s*·|September 2026 ·|Business strategy/.test(l))bad.push(`${route}: ${l.slice(0,80)}`);
 }
 const feed=await (await request.get('/feed.xml')).text();
 expect(feed.startsWith('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>')).toBe(true);
 expect(/<(pubDate|lastBuildDate|updated|dc:date)>/.test(feed)).toBe(false);
 expect(DATE.test(feed)).toBe(false);
 expect(bad).toEqual([]);
});
// v14.2 (Paul 2026-11-02 18:08 voice call; Vera's mockup apex-1440/390-video-spot): the homepage video band sits directly
// under the hero and before the core section, ready to play: controls, no autoplay, its own poster. v14.3 (Grace relay
// 8:42 AM Nov 3, Paul voice call): no captions; the video has no text tracks.
test('v14.2: homepage video band under the hero: centred 16:9 player, no autoplay, no text tracks, named by the h1, poster served',async({page,request})=>{
 const bad=[];
 for(const [width,reduce] of [[1440,'no-preference'],[390,'reduce'],[320,'no-preference']]){
  await page.emulateMedia({reducedMotion:reduce});
  await page.setViewportSize({width,height:900});
  await page.goto('/',{waitUntil:'load'});
  await page.waitForTimeout(800);
  await page.waitForFunction(()=>{const v=document.querySelector('section.gl-video video');return !v||v.readyState>=1;});
  const m=await page.evaluate(()=>{const band=document.querySelector('section.gl-video');const v=band&&band.querySelector('video');if(!v)return null;
   const r=v.getBoundingClientRect();
   return {prev:band.previousElementSibling&&band.previousElementSibling.className,next:band.nextElementSibling&&band.nextElementSibling.className,
    src:v.querySelector('source').getAttribute('src'),duration:v.duration,autoplay:v.autoplay,paused:v.paused,muted:v.muted,controls:v.controls,preload:v.getAttribute('preload'),playsinline:v.hasAttribute('playsinline'),poster:v.getAttribute('poster'),
    tracks:v.querySelectorAll('track').length,textTracks:v.textTracks.length,
    named:(v.getAttribute('aria-labelledby')||'').split(/\s+/).filter(Boolean).map(id=>{const e=document.getElementById(id);return e?e.textContent.trim():'#missing:'+id;}).join(' '),
    namedBy:(()=>{const e=document.getElementById(v.getAttribute('aria-labelledby')||'');return e&&e.tagName;})(),ariaLabel:v.hasAttribute('aria-label'),title:v.hasAttribute('title'),
    w:r.width,h:r.height,left:r.left,right:innerWidth-r.right,words:band.textContent.trim(),h1:document.querySelectorAll('h1').length,
    bg:getComputedStyle(band).backgroundImage!=='none'||getComputedStyle(band).backgroundColor};});
  if(!m){bad.push(`${width}: no video band`);continue;}
  if(m.prev!=='gl-hero'||m.next!=='gl-core')bad.push(`${width}: band not between hero and core (${m.prev} / ${m.next})`);
  if(m.autoplay||!m.paused||m.muted)bad.push(`${width}: autoplay ${m.autoplay} paused ${m.paused} muted ${m.muted}`);
  if(!m.controls||m.preload!=='metadata'||!m.playsinline)bad.push(`${width}: controls/preload/playsinline`);
  if(m.tracks!==0||m.textTracks!==0)bad.push(`${width}: video has ${m.tracks} <track> / ${m.textTracks} text tracks; expected none`);
  if(m.named!=='Governed Logic Reasoning Systems'||m.namedBy!=='H1'||m.ariaLabel||m.title)bad.push(`${width}: video name "${m.named}" via ${m.namedBy}`);
  if(m.words!=='')bad.push(`${width}: band adds words: ${m.words}`);
  if(m.h1!==1)bad.push(`${width}: h1 count ${m.h1}`);
  if(Math.abs(m.w/m.h-16/9)>0.02)bad.push(`${width}: player not 16:9 (${m.w}x${m.h})`);
  if(width===1440&&(m.w>960.5||Math.abs(m.left-m.right)>1))bad.push(`1440: player ${m.w}px wide, not centred at 960 max`);
  if(width<900&&Math.abs(m.w-width)>1)bad.push(`${width}: player ${m.w}px, not full width`);
  // v14.2.2 (Grace relay 7:23 PM Nov 2): media at cache-busted URLs path?v=<first 8 hex of the file's sha256>.
  // v14.2.3 (Grace relay 8:16 AM Nov 3): v3 voice media, 116.666667s by ffprobe.
  const want={[m.poster]:'/assets/video/gl-home-explainer-poster.webp',[m.src]:'/assets/video/gl-home-explainer.mp4'};
  for(const [u,path] of Object.entries(want)){
   if(!new RegExp('^'+path.replace(/\./g,'\\.')+'\\?v=[0-9a-f]{8}$').test(u))bad.push(`${width}: ${u} is not ${path}?v=<8 hex>`);
   const r=await request.get(u);if(!r.ok()){bad.push(`${u} ${r.status()}`);continue;}
   const hex=createHash('sha256').update(await r.body()).digest('hex').slice(0,8);if(!u.endsWith('?v='+hex))bad.push(`${width}: ${u} serves sha256 ${hex}`);}
  // Swap-ready: the expected duration is read from the served mp4's own mvhd box, so a later cut at the same path is
  // the file plus its new ?v= in content/home.html and nothing else.
  const mp4=await (await request.get(m.src)).body();const i=mp4.indexOf('mvhd');const ver=mp4[i+4];
  const mvhd=ver?Number(mp4.readBigUInt64BE(i+28))/mp4.readUInt32BE(i+24):mp4.readUInt32BE(i+20)/mp4.readUInt32BE(i+16);
  if(i<0||!(mvhd>0)||Math.abs(m.duration-mvhd)>0.05)bad.push(`${width}: video duration ${m.duration}, mp4 says ${mvhd}s`);
 }
 expect(bad).toEqual([]);
});

// Visual refresh, structural part (spec sections 4, 6 and 9): the hero Seed of Life and its preload are gone, the empty
// div.gl-hero-art keeps its size as the signature field, and the concept 3 signature plays once per session without
// reduced motion, adds exactly one aria-hidden SVG and no words, ends still, never covers the video and shifts nothing.
const SIG_DONE=4200;
const sigState=()=>{const art=document.querySelector('#explore .gl-hero-art');const svgs=art?art.querySelectorAll(':scope > svg'):[];
 // The signature's own animations: anything in the hero, plus body::after (the margin line). The Problem band and footer
 // watermarks are band styling, left for the next spec.
 const own=document.getAnimations().filter(a=>{const t=a.effect&&a.effect.target;return t&&(t===document.body||!!t.closest('#explore'));});
 const docAnims=own.filter(a=>!a.timeline||a.timeline.constructor.name==='DocumentTimeline');
 const ax=getComputedStyle(document.querySelector('.gl-chain'),'::before'),pt=getComputedStyle(document.querySelector('.gl-chain'),'::after');
 const r=art.getBoundingClientRect();
 return {run:document.body.classList.contains('gl-sig-run'),svgs:svgs.length,hidden:[...svgs].every(s=>s.getAttribute('aria-hidden')==='true'),
  artKids:art.children.length,artText:art.textContent,imgs:art.querySelectorAll('img').length,
  running:docAnims.filter(a=>a.playState==='running').length,infinite:own.filter(a=>a.effect&&a.effect.getTiming().iterations===Infinity).length,
  axis:ax.content!=='none'&&ax.display!=='none',point:pt.content!=='none'&&pt.display!=='none',
  lit:[...document.querySelectorAll('.gl-sig circle')].every(c=>+getComputedStyle(c).opacity>0.99),
  w:r.width,h:r.height,h1:document.querySelectorAll('h1').length,chime:document.querySelectorAll('.gl-chime').length,
  preload:!!document.querySelector('link[rel="preload"][href*="hero-geometry"]'),
  body:document.body.innerText.replace(/\s+/g,' ').trim()};};
test('Signature: hero Seed of Life gone, field keeps its size, plays once per session, ends still, one aria-hidden svg',async({page})=>{
 test.setTimeout(120_000);
 const want={1440:[706,629],390:[390,390*894/1004],320:[320,160]};
 const bad=[];
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:900});
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto('/',{waitUntil:'load'});
  const text0=await page.evaluate(()=>document.body.innerText.replace(/\s+/g,' ').trim());
  await page.evaluate(()=>sessionStorage.clear());
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.goto('/',{waitUntil:'load'});
  const first=await page.evaluate(sigState);
  const p=Math.min(1,width/1440),[ew,eh]=want[width];
  if(width===1440?(Math.abs(first.w-ew*p)>1||Math.abs(first.h-eh*p)>1):(Math.abs(first.w-ew)>1||Math.abs(first.h-eh)>1))bad.push(`${width}: field ${first.w}x${first.h}, expected ${ew}x${eh}`);
  if(!first.run)bad.push(`${width}: first load in a session did not play`);
  if(first.svgs!==1||!first.hidden||first.artKids!==1||first.artText!==''||first.imgs!==0)bad.push(`${width}: field holds ${first.artKids} children, ${first.svgs} svg, hidden ${first.hidden}, ${first.imgs} img`);
  if(first.preload||first.chime||first.h1!==1)bad.push(`${width}: preload ${first.preload} chime ${first.chime} h1 ${first.h1}`);
  if(first.body!==text0)bad.push(`${width}: visible text changed while the signature runs`);
  if(first.infinite)bad.push(`${width}: ${first.infinite} looping animations`);
  await page.waitForTimeout(SIG_DONE);
  const end=await page.evaluate(sigState);
  if(end.running)bad.push(`${width}: ${end.running} animations still running after ${SIG_DONE}ms`);
  if(!end.lit)bad.push(`${width}: network not fully lit at the end`);
  if(width>379&&(!end.axis||!end.point))bad.push(`${width}: axis or point missing at the end`);
  if(end.body!==text0)bad.push(`${width}: visible text changed after the signature`);
  await page.goto('/',{waitUntil:'load'});
  const again=await page.evaluate(sigState);
  if(again.run||again.running||again.svgs!==1||!again.lit)bad.push(`${width}: second load in the session moved (run ${again.run}, running ${again.running}, lit ${again.lit})`);
  await page.emulateMedia({reducedMotion:'reduce'});await page.evaluate(()=>sessionStorage.clear());
  await page.goto('/',{waitUntil:'load'});
  const still=await page.evaluate(sigState);
  if(still.run||still.running||still.svgs!==1||!still.lit||(width>379&&(!still.axis||!still.point)))bad.push(`${width}: reduced motion is not the end still (run ${still.run}, running ${still.running}, lit ${still.lit})`);
  if(await page.evaluate(()=>sessionStorage.getItem('gl-sig')))bad.push(`${width}: reduced motion used up the session play`);
 }
 expect(bad).toEqual([]);
});
test('Signature: plays once and carries on if sessionStorage throws, no JS still shows the hero complete',async({page,browser})=>{
 await page.addInitScript(()=>{Object.defineProperty(window,'sessionStorage',{get(){throw new Error('blocked');}});});
 await page.emulateMedia({reducedMotion:'no-preference'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/',{waitUntil:'load'});
 const m=await page.evaluate(sigState);
 expect(m.run).toBe(true);expect(m.svgs).toBe(1);expect(errors).toEqual([]);
 await page.waitForTimeout(SIG_DONE);
 expect((await page.evaluate(sigState)).running).toBe(0);
 const ctx=await browser.newContext({javaScriptEnabled:false,reducedMotion:'no-preference'});
 try{
  const q=await ctx.newPage();
  for(const width of [1440,390,320]){
   await q.setViewportSize({width,height:900});
   await q.goto(new URL('/',page.url()).href,{waitUntil:'load'});
   const n=await q.evaluate(()=>{const art=document.querySelector('#explore .gl-hero-art');const r=art.getBoundingClientRect();const c=document.querySelector('.gl-chain');
    return {kids:art.children.length,h:r.height,axis:getComputedStyle(c,'::before').content!=='none',point:getComputedStyle(c,'::after').content!=='none',words:[...c.querySelectorAll('strong')].map(s=>s.textContent),run:document.body.classList.contains('gl-sig-run')};});
   expect(n.kids,`${width}`).toBe(0);expect(n.h,`${width}`).toBeGreaterThan(100);expect(n.run).toBe(false);
   expect(n.words).toEqual(['Truth','Logic','Reasoning','Intelligence']);
   if(width>379){expect(n.axis,`${width} axis`).toBe(true);expect(n.point,`${width} point`).toBe(true);}
  }
 }finally{await ctx.close();}
});
test('Signature: nothing overlaps the video, paused or playing, at 1440, 390 and 320, and CLS stays 0',async({page})=>{
 test.setTimeout(120_000);
 const bad=[];
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:width<500?844:900});
  await page.addInitScript(()=>{window.__cls=0;new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)window.__cls+=e.value;}).observe({type:'layout-shift',buffered:true});});
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.goto('/',{waitUntil:'load'});await page.evaluate(()=>sessionStorage.clear());
  await page.goto('/',{waitUntil:'load'});
  await page.waitForTimeout(SIG_DONE);
  const cls=await page.evaluate(()=>window.__cls);
  if(cls!==0)bad.push(`${width}: CLS ${cls} during the signature`);
  for(const state of ['paused','playing']){
   await page.locator('section.gl-video video').scrollIntoViewIfNeeded();
   if(state==='playing'){await page.evaluate(async()=>{const v=document.querySelector('section.gl-video video');v.muted=true;await v.play();});await page.waitForTimeout(1200);}
   const m=await page.evaluate(()=>{const v=document.querySelector('section.gl-video video');const r=v.getBoundingClientRect();
    const art=document.querySelector('#explore .gl-hero-art').getBoundingClientRect(),sig=document.querySelector('.gl-sig');const s=sig?sig.getBoundingClientRect():null;
    const pts=[];for(const fx of [.1,.5,.9])for(const fy of [.1,.5,.9]){const x=r.left+r.width*fx,y=r.top+r.height*fy;if(y>0&&y<innerHeight)pts.push(document.elementFromPoint(x,y)===v);}
    return {paused:v.paused,t:v.currentTime,top:r.top,artBottom:art.bottom,sigBottom:s?s.bottom:null,hits:pts,gutter:getComputedStyle(document.body,'::after').content,
     overflow:document.documentElement.scrollWidth>innerWidth};});
   if(state==='playing'&&(m.paused||!(m.t>0)))bad.push(`${width}: video did not play (t ${m.t})`);
   if(m.artBottom>m.top+0.5||(m.sigBottom!==null&&m.sigBottom>m.top+0.5))bad.push(`${width} ${state}: signature field reaches into the video`);
   if(!m.hits.length||m.hits.some(h=>!h))bad.push(`${width} ${state}: something covers the video (${m.hits})`);
   if(width<=900&&m.gutter!=='none')bad.push(`${width}: margin line shown at or under 900px`);
   if(m.overflow)bad.push(`${width}: horizontal overflow`);
  }
  await page.evaluate(()=>document.querySelector('section.gl-video video').pause());
  const cls2=await page.evaluate(()=>window.__cls);
  if(cls2!==0)bad.push(`${width}: CLS ${cls2} after scroll and play`);
 }
 expect(bad).toEqual([]);
});
test('Signature: gl-cool on <html> swaps the four warm values, gold is the default',async({page})=>{
 await page.goto('/',{waitUntil:'load'});
 const read=()=>page.evaluate(()=>{const s=getComputedStyle(document.documentElement);return ['--gl-warm','--gl-warm-ink','--gl-warm-glow','--gl-warm-line'].map(k=>s.getPropertyValue(k).trim());});
 expect(await page.evaluate(()=>document.documentElement.classList.contains('gl-cool'))).toBe(false);
 expect(await read()).toEqual(['#d7b57e','#8a5f1f','rgba(255,226,170,.9)','rgba(215,181,126,.6)']);
 await page.evaluate(()=>document.documentElement.classList.add('gl-cool'));
 expect(await read()).toEqual(['#9cc8ff','#1657c2','rgba(200,225,255,.9)','rgba(111,178,255,.6)']);
 const glow=await page.evaluate(()=>getComputedStyle(document.querySelector('.gl-chain'),'::after').boxShadow);
 expect(glow).toContain('rgba(200, 225, 255, 0.9)');
});
const lineState=()=>{const a=getComputedStyle(document.body,'::after');const left=parseFloat(a.left),right=left+parseFloat(a.width);
   const hits=[];
   for(const e of document.querySelectorAll('main :is(h1,p,a,button,h2,li),footer :is(h1,p,a,button,h2,li),main video')){
    const cs=getComputedStyle(e);if(cs.visibility==='hidden'||cs.display==='none')continue;
    const r=e.getBoundingClientRect();if(r.width<1||r.height<1)continue;
    if(r.left<right&&r.right>left)hits.push(`${e.tagName.toLowerCase()}.${e.className} ${Math.round(r.left)}-${Math.round(r.right)}`);}
   const hdr=document.querySelector('header#gl-home-bar'),hz=+getComputedStyle(hdr).zIndex,lz=+a.zIndex;
   const b=getComputedStyle(document.body);const bodyContext=b.position!=='static'&&b.zIndex!=='auto'||b.isolation==='isolate'||b.transform!=='none'||+b.opacity<1;
   return {content:a.content,left,right,hits,hz,lz,bodyContext,hdrH:hdr.getBoundingClientRect().height};};
test('Signature: the margin line stays in the margin at 1440, 1920 and 2560, left of all text and the video, and under the header',async({page})=>{
 // QA pre-gate B1: the line sits half way between the frame edge and the spine and never crosses Paul's copy, the video
 // or the sticky header, at any desktop width.
 test.setTimeout(120_000);
 const bad=[];
 await page.emulateMedia({reducedMotion:'no-preference'});
 for(const width of [1440,1920,2560]){
  await page.setViewportSize({width,height:1000});
  await page.goto('/',{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
  const m=await page.evaluate(lineState);
  if(m.content==='none'){bad.push(`${width}: no margin line`);continue;}
  if(m.hits.length)bad.push(`${width}: line at ${m.left}-${m.right}px crosses ${m.hits.length}: ${m.hits.slice(0,6).join(', ')}`);
  if(!(m.lz<m.hz)||m.bodyContext)bad.push(`${width}: line z-index ${m.lz} is not under the header (${m.hz})`);
  // Pixels: the header with and without the line, scrolled to mid page so the line is drawn under the header's band.
  await page.evaluate(()=>scrollTo(0,document.documentElement.scrollHeight/2));await page.waitForTimeout(300);
  const clip={x:Math.max(0,Math.floor(m.left)-8),y:0,width:24,height:Math.ceil(m.hdrH)};
  const withLine=await page.screenshot({clip,animations:'disabled'});
  await page.addStyleTag({content:'body.gl-home-page::after{visibility:hidden!important}'});
  const without=await page.screenshot({clip,animations:'disabled'});
  if(!withLine.equals(without))bad.push(`${width}: the line draws over the header`);
 }
 // Planted fault: the old formula (--frame counted twice) must make this check fail at 1920.
 await page.setViewportSize({width:1920,height:1000});await page.goto('/',{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
 await page.addStyleTag({content:'body.gl-home-page::after{left:calc(var(--frame) + var(--spine) / 2)!important}'});
 const planted=await page.evaluate(lineState);
 expect(planted.hits.length,'old margin line formula must cross the copy at 1920').toBeGreaterThan(0);
 expect(bad).toEqual([]);
});
