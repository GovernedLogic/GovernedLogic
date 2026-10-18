import {test,expect} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
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
 await page.getByRole('link',{name:'Explore ↓',exact:true}).click();await expect(page.locator('#explore')).toBeInViewport();
});