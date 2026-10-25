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
  const links=page.getByRole('navigation',{name:'Primary',exact:true}).getByRole('link');
  for(const link of await links.all()){const box=await link.boundingBox();expect(box.height).toBeGreaterThanOrEqual(43);expect(box.x).toBeGreaterThanOrEqual(0);expect(box.x+box.width).toBeLessThanOrEqual(page.viewportSize().width+1);}
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
 await page.getByRole('navigation',{name:'Primary',exact:true}).getByRole('link',{name:'Architecture',exact:true}).click();
 await expect(page.locator('h1')).toHaveText('Governed Logic');await context.close();
});
test('Opening completes and leaves content usable',async({page})=>{
 test.setTimeout(45000);await page.emulateMedia({reducedMotion:'no-preference'});await page.goto('/');
 await expect(page.locator('#glIntro')).toHaveCount(0,{timeout:20000});
 const invite=page.locator('a.scroll-invite');
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
  {at:1200,name:'02-point',label:'A point of light',stage:'point'},
  {at:2200,name:'03-star',label:'Light gathers',stage:'star'},
  {at:3000,name:'04-release',label:'Expansion',stage:'release'},
  {at:4350,name:'05-orbits',label:'Orbital order',stage:'orbits'},
  {at:6500,name:'06-spirograph',label:'Coherent structure',stage:'spirograph'},
  {at:7600,name:'07-green',label:'Green emergence',stage:'green'},
  {at:9700,name:'08-globe',label:'Particles describe Earth',stage:'globe'},
  {at:10900,name:'09-material',label:'Earth resolves',stage:'material'},
  {at:12500,name:'10-horizon',label:'Horizon and depth',stage:'horizon'},
  {at:14800,name:'11-identity',label:'Company identity arrives',stage:'identity'},
  {at:16500,name:'12-complete',label:'Completed company identity'}
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
