// Real Chromium + real local service + real worker. No existing browser profile.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const {chromium}=require('playwright');
const payload=path.resolve(process.env.MECHANICS_PAYLOAD||path.join(__dirname,'../offline-mechanics-lab'));
const work=fs.mkdtempSync('/private/tmp/mechanics-browser-');
const output=path.resolve(process.env.MECHANICS_BROWSER_REPORT||'dist/offline-mechanics-lab/1.0.0/browser-verification.json');
const python=process.env.MECHANICS_PYTHON||'/opt/anaconda3/bin/python';
function tool(action){return JSON.parse(execFileSync(python,['-B','-c',
  'import importlib.util,json,sys\ns=importlib.util.spec_from_file_location("lab",sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nprint(json.dumps(m.local_lab({"workspace":sys.argv[2],"action":sys.argv[3],"confirmed":True})))',path.join(payload,'runtime/lab.py'),work,action],{encoding:'utf8'}));}
(async()=>{let browser,live;const checks=[],errors=[],external=[];let failure;
  try{
    live=tool('start');assert.equal(live.ok,true,JSON.stringify(live));
    browser=await chromium.launch({channel:'chrome',headless:true});
    const context=await browser.newContext({viewport:{width:1500,height:1100},acceptDownloads:true});
    const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
    page.on('request',r=>{if(!r.url().startsWith(new URL(live.url).origin)&&!r.url().startsWith('blob:'))external.push(r.url());});
    await page.goto(live.url);assert.match(await page.title(),/离线力学实验室/);
    async function run(){await page.click('#run');await page.waitForFunction(()=>document.getElementById('result-badge').textContent==='计算完成');}
    await run();assert.equal(await page.textContent('#frame-count'),'241');checks.push('real-worker-freefall-241-frames');
    await page.click('#play');await page.waitForFunction(()=>Number(document.getElementById('frame').value)>5);await page.click('#play');
    const paused=await page.inputValue('#frame');await page.waitForTimeout(100);assert.equal(await page.inputValue('#frame'),paused);checks.push('play-pause-real-samples');
    await page.click('[data-example="collision"]');await run();
    await page.locator('#frame').fill('360');await page.locator('#frame').dispatchEvent('input');
    assert.equal(await page.textContent('#velocity'),'-100 / 0');checks.push('collision-browser-reference-velocity');
    const dl=page.waitForEvent('download');await page.click('#csv');const file=await dl;const csv=fs.readFileSync(await file.path(),'utf8');assert.equal(csv.trim().split('\r\n').length,723);checks.push('actual-csv-722-rows');
    await page.fill('#title','中文碰撞复现');await page.click('#save');await page.waitForFunction(()=>document.getElementById('message').textContent.includes('已保存'));
    await page.click('[data-example="pendulum"]');await page.click('#load');await page.waitForFunction(()=>document.getElementById('title').value==='中文碰撞复现');assert.equal(await page.isDisabled('#csv'),true);
    await page.reload();await page.click('#load');await page.waitForFunction(()=>document.getElementById('title').value==='中文碰撞复现');checks.push('persist-restart-load-Chinese-input-and-no-stale-result');
    await run();await page.fill('#gravity','101');assert.equal(await page.isDisabled('#csv'),true);assert.equal(await page.textContent('#position'),'—');checks.push('edit-clears-readings-and-disables-export');
    await page.fill('#duration','11');await page.click('#run');await page.waitForFunction(()=>document.getElementById('message').classList.contains('error'));assert.equal(await page.isDisabled('#csv'),true);checks.push('invalid-input-fails-closed-in-Chinese');
    await page.click('[data-example="pendulum"]');await run();assert.equal(await page.textContent('#frame-count'),'601');
    const download=page.waitForEvent('download');await page.click('#export');const exported=await download;const json=fs.readFileSync(await exported.path());
    await page.click('[data-example="fall"]');await page.locator('#file').setInputFiles({name:'中文单摆.json',mimeType:'application/json',buffer:json});await page.waitForFunction(()=>document.getElementById('title').value==='固定点单摆');await run();checks.push('JSON-roundtrip-and-recompute');
    await page.locator('#file').setInputFiles({name:'坏场景.json',mimeType:'application/json',buffer:Buffer.from('{"script":"bad"}')});await page.waitForFunction(()=>document.getElementById('message').textContent.includes('导入失败'));assert.equal(await page.isDisabled('#csv'),true);checks.push('invalid-import-clears-old-results');
    await page.click('[data-example="collision"]');await page.click('#edit');
    const box=await page.locator('#world').boundingBox();await page.mouse.move(box.x+320*box.width/1000,box.y+310*box.height/650);await page.mouse.down();await page.mouse.move(box.x+380*box.width/1000,box.y+270*box.height/650);await page.mouse.up();
    assert.ok(Math.abs(Number(await page.getByLabel('横坐标 X',{exact:true}).inputValue())-380)<=1);checks.push('pointer-drag-edits-real-initial-coordinates');
    // Delay a real worker resource to exercise cancel/freshness and timeout paths.
    await page.route('**/worker.js',route=>new Promise(resolve=>setTimeout(async()=>{try{await route.continue();}catch{}resolve();},9500)));
    await page.click('#run');await page.fill('#gravity','123');await page.waitForTimeout(200);assert.equal(await page.isDisabled('#csv'),true);checks.push('input-change-cancels-pending-worker');
    await page.click('#run');await page.waitForFunction(()=>document.getElementById('message').textContent.includes('超过8秒'),null,{timeout:11000});assert.equal(await page.isDisabled('#csv'),true);checks.push('worker-stall-timeout-no-results');
    await page.unroute('**/worker.js');
    // A late saved-scene response must not replace newer user edits.
    await page.route('**/api/saved',async route=>{await new Promise(r=>setTimeout(r,400));await route.continue();});
    await page.click('#load');await page.fill('#title','保留新编辑');await page.waitForFunction(()=>document.getElementById('message').textContent.includes('迟到'));assert.equal(await page.inputValue('#title'),'保留新编辑');checks.push('late-load-does-not-clobber-edits');
    await page.unroute('**/api/saved');
    await page.click('[data-example="pendulum"]');await run();await page.locator('#frame').fill('240');await page.locator('#frame').dispatchEvent('input');
    fs.mkdirSync(path.dirname(output),{recursive:true});await page.screenshot({path:path.resolve('dist/offline-mechanics-lab/1.0.0/browser-preview.png'),fullPage:true});
    assert.deepEqual(errors,[]);assert.deepEqual(external,[]);checks.push('no-page-errors-or-external-page-requests');
    await context.close();
  }catch(e){failure=e;}finally{if(browser)await browser.close();if(live?.ok){const stopped=tool('stop');assert.equal(stopped.ok,true,JSON.stringify(stopped));}fs.rmSync(work,{recursive:true,force:true});
    fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify({date:new Date().toISOString(),plugin:'offline-mechanics-lab',version:'1.0.0',scope:'Automated real browser/service/worker tests; not user manual testing or chat-worker invocation',checks,errors,external_request_count:external.length,passed:!failure,error:failure?.message},null,2)+'\n');}
  if(failure)throw failure;console.log(JSON.stringify({passed:true,checks},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
