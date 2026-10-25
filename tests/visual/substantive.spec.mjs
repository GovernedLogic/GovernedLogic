import {test,expect} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
const routes=['/','/challenge/','/company/','/research/','/about/','/faq/','/concepts/','/concepts/governed-logic/','/concepts/governed-intelligence/','/concepts/ultimate-grounding/','/concepts/alpha-and-omega-reasoning/','/concepts/governing-referent/','/concepts/sufficient-grounding/','/mechanism.html','/sources/','/articles/why-anything/','/articles/integrity-in-artificial-intelligence/','/library/','/publication/'];
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
 await page.getByRole('button',{name:'Clear',exact:true}).click();await expect(page.locator('.library-item:visible')).toHaveCount(21);
});
test('FAQ answers open and match machine data',async({page})=>{
 await page.goto('/faq/');await page.getByText('What exists today?',{exact:true}).click();
 await expect(page.locator('details[open]')).toContainText('working instruction-level prototype');
});
test('Homepage and navigation work without JavaScript',async({browser})=>{
 const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});const page=await context.newPage();
 await page.goto((process.env.BASE_URL || 'http://127.0.0.1:4173')+'/');await expect(page.locator('main')).toContainText('Governed Intelligence');
 await page.getByRole('navigation',{name:'Primary',exact:true}).getByRole('button',{name:'Governed Logic',exact:true}).click();
 await expect(page.locator('h1')).toHaveText('Governed Logic');await context.close();
});
test('Opening completes and leaves content usable',async({page})=>{
 test.setTimeout(45000);await page.emulateMedia({reducedMotion:'no-preference'});await page.goto('/');
 await expect(page.locator('#glIntro')).toHaveCount(0,{timeout:20000});
 const invite=page.locator('.scroll-invite');
 await expect(invite).toHaveAccessibleName('See what we are building ↓');
 await invite.click();await expect(page.locator('#explore')).toBeInViewport();
});
test('Opening records its chronological visual sequence',async({page},info)=>{
 test.skip(info.project.name==='mobile-320','The opening filmstrip covers desktop and the 390-pixel mobile viewport.');
 test.setTimeout(90000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.emulateMedia({reducedMotion:'no-preference'});
 const startTime=new Date('2026-10-18T12:00:00Z');
 await page.clock.install({time:new Date(startTime.getTime()-1000)});await page.clock.pauseAt(startTime);
 await page.goto('/',{waitUntil:'load'});await page.evaluate(async()=>{await document.fonts.ready});
 await expect(page.locator('#glIntro')).toHaveCount(1);
 const frames=[
  {at:50,name:'01-black',label:'Black field',stage:'black'},
  {at:400,name:'02-trace',label:'Light starts',stage:'trace'},
  {at:800,name:'03-trace',label:'The band lengthens',stage:'trace'},
  {at:1200,name:'04-trace',label:'One path, mid circuit',stage:'trace'},
  {at:1500,name:'05-trace',label:'Crossings woven',stage:'trace'},
  {at:1800,name:'06-resolve',label:'Earth shows through',stage:'resolve'},
  {at:2200,name:'07-resolve',label:'The page returns',stage:'resolve'},
  {at:2500,name:'08-resolve',label:'Veil nearly gone',stage:'resolve'},
  {at:2800,name:'09-fade',label:'Overlay recedes',stage:'fade'},
  {at:3100,name:'10-fade',label:'Hero almost clear',stage:'fade'},
  {at:3300,name:'11-fade',label:'Last of the trace',stage:'fade'},
  {at:3700,name:'12-complete',label:'Page usable'}
 ];
 const directory=path.resolve('visual-qa/motion',info.project.name);await mkdir(directory,{recursive:true});
 const evidence=[];let elapsed=0;
 for(const frame of frames){
  const delta=frame.at-elapsed;
  // Jump to the next phase, then execute ordinary animation frames at that time.
  // Runtime code receives the same clock and animation callbacks as a normal visit.
  if(delta>34)await page.clock.fastForward(delta-34);
  await page.clock.runFor(Math.min(delta,34));elapsed=frame.at;
  if(frame.stage)await expect(page.locator('#glIntro')).toHaveAttribute('data-stage',frame.stage);
  if(frame.name==='01-black'){
   const samples=await page.locator('#glIntro .intro-canvas').evaluate(canvas=>{
    const context=canvas.getContext('2d');
    return [[.1,.1],[.5,.1],[.9,.1],[.1,.5],[.5,.5],[.9,.5],[.1,.9],[.5,.9],[.9,.9]]
     .map(([x,y])=>Array.from(context.getImageData(Math.floor(x*canvas.width),Math.floor(y*canvas.height),1,1).data));
   });
   expect(samples.every(([r,g,b,a])=>r===0&&g===0&&b===0&&a===255)).toBeTruthy();
  }
  const screenshot=await page.screenshot({path:path.join(directory,frame.name+'.png'),animations:'allow'});
  evidence.push({...frame,path:frame.name+'.png',sha256:createHash('sha256').update(screenshot).digest('hex'),overlayPresent:await page.locator('#glIntro').count()===1});
 }
 await expect(page.locator('#glIntro')).toHaveCount(0);
 await expect(page.locator('#site .identity')).toBeVisible();
 await expect(page.locator('#site .brand-sub')).toHaveText('Reasoning Systems');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
 expect(new Set(evidence.slice(0,-1).map(frame=>frame.sha256)).size).toBe(frames.length-1);
 await writeFile(path.join(directory,'frames.json'),JSON.stringify({project:info.project.name,viewport:page.viewportSize(),mode:'Normal motion; Playwright clock controls time without changing runtime behavior',frames:evidence},null,2)+'\n');
 expect(errors).toEqual([]);
});

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
   for(const node of document.querySelectorAll('#explore h2, #explore .lede, #explore .intro-description, #explore .section-meta, #explore .prototype-status, #explore .downstream')){
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
 expect(metrics.count).toBe(5);
 expect(metrics.overflow).toBe(false);
 expect(metrics.headerHeight).toBeLessThanOrEqual(64);
 expect(metrics.oneRow).toBe(true);
 for(const box of metrics.boxes){
  expect(box.h).toBeGreaterThanOrEqual(44);
  expect(box.w).toBeGreaterThanOrEqual(44);
 }
});

test('Intro skip is immediate and the first click still lands',async({page})=>{
 test.setTimeout(30000);
 await page.emulateMedia({reducedMotion:'no-preference'});
 const startTime=new Date('2026-10-18T12:00:00Z');
 await page.clock.install({time:new Date(startTime.getTime()-1000)});
 await page.clock.pauseAt(startTime);
 await page.goto('/',{waitUntil:'load'});
 await expect(page.locator('#glIntro')).toHaveCount(1);
 await expect(page.locator('.gl-intro-skip')).toHaveAccessibleName('Skip to content');
 await page.clock.runFor(500);
 await page.locator('.scroll-invite').click();
 await expect(page.locator('#glIntro')).toHaveCount(0);
 await expect(page.locator('#explore')).toBeInViewport();
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
