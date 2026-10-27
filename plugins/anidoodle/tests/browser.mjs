// Headless functional tests only; no authenticated browser or external pages.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const { chromium } = await import(process.env.ANIDOODLE_PLAYWRIGHT_URL || 'playwright-core');
const output = resolve(process.argv[2]);
const evidence = resolve(process.argv[3]); mkdirSync(evidence,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.ANIDOODLE_BROWSER || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',headless:true});
const results=[];
try {
  for (const scene of ['mascot','form','scroll']) {
    const page=await browser.newPage({viewport:{width:1280,height:900},deviceScaleFactor:1});
    const errors=[],external=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('request',r=>{if(!/^(file|data|blob):/.test(r.url()))external.push(r.url());});
    await page.addInitScript(()=>{window.__ANI_RASTER__='cpu';});
    await page.goto(pathToFileURL(resolve(output,scene+'.html')).href);
    await page.waitForFunction(()=>window.__artController,{timeout:30000});
    await page.evaluate(()=>window.__artController.ready);
    const replay=await page.evaluate(()=>{const c=window.__artController;c.pause();const l=c.log();c.render(0,l);const a=c.hash();c.render(37,l);const b=c.hash();c.render(0,l);const a2=c.hash();c.play();return {a,b,a2};});
    assert.equal(replay.a,replay.a2,'same renderer and input reproduces frame');
    if(scene==='mascot') {
      assert.notEqual(replay.a,replay.b,'idle animation changes');
      await page.mouse.move(100,150);await page.mouse.move(950,400);
      await page.getByRole('button',{name:'一起欢呼',exact:true}).click();
      await page.waitForFunction(()=>window.__artController.log().some(x=>x.type==='up'&&x.target==='start'));
      await page.getByRole('button',{name:'向我挥手',exact:true}).focus();await page.keyboard.press('Enter');
      await page.waitForFunction(()=>window.__artController.log().some(x=>x.type==='up'&&x.target==='tour'));
    }
    if(scene==='form') {
      await page.getByRole('button',{name:'完成演示'}).click();
      await page.waitForFunction(()=>window.__artController.log().some(x=>x.type==='state'&&x.value==='error'));
      await page.locator('#name').fill('小明');await page.locator('#password').fill('demo-only');
      await page.waitForFunction(()=>window.__artController.log().some(x=>x.type==='focus'&&x.target==='password'));
      assert(!JSON.stringify(await page.evaluate(()=>window.__artController.log())).includes('demo-only'),'input text is not in event log');
      await page.locator('#reveal').check();
      await page.waitForFunction(()=>window.__artController.log().some(x=>x.type==='state'&&x.value==='peek'));
      await page.getByRole('button',{name:'完成演示'}).click();
      await page.waitForFunction(()=>document.getElementById('status').textContent.includes('没有注册账号'));
    }
    if(scene==='scroll') {
      await page.evaluate(()=>window.scrollTo(0,document.body.scrollHeight));
      await page.waitForFunction(()=>window.__artController.log().some(x=>x.type==='scroll'&&Number(x.value)>.8));
      await page.evaluate(()=>window.scrollTo(0,800));
      await page.waitForFunction(()=>window.__artController.log().filter(x=>x.type==='scroll').length>1);
    }
    const png=page.waitForEvent('download');
    await page.getByRole('button',{name:'保存当前画面 PNG'}).click();
    const dl=await png;assert.equal(dl.suggestedFilename(),'手绘作品.png');await dl.saveAs(resolve(evidence,scene+'.png'));
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:resolve(evidence,scene+'-page.png')});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'desktop has no horizontal overflow');
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'mobile has no horizontal overflow');
    await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await page.waitForFunction(()=>window.__artController);await page.evaluate(()=>window.__artController.ready);
    const reduced=await page.evaluate(()=>{const c=window.__artController;c.pause();const log=c.log();c.render(0,log);const a=c.hash();c.render(37,log);return a===c.hash();});
    assert(reduced,'reduced-motion idle is static');
    assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
    results.push({scene,replay,reduced,errors,external,passed:true});
    await page.close();
  }
  writeFileSync(resolve(evidence,'browser-results.json'),JSON.stringify(results,null,2));
  console.log(JSON.stringify(results));
} finally {await browser.close();}
