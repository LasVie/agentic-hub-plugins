// Development-only Playwright verification. No browser/model tooling is bundled.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright-core');
const url=process.argv[2],output=process.argv[3];
if(!url||!output)throw Error('Usage: node browser.cjs <actual-tool-url> <owned-output-directory>');
fs.mkdirSync(output,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const context=await browser.newContext({acceptDownloads:true,viewport:{width:1440,height:1100}}),page=await context.newPage();const outside=[],errors=[],downloads={};
 context.on('request',r=>{if(new URL(r.url()).origin!==new URL(url).origin)outside.push(r.url());});page.on('pageerror',e=>errors.push(e.message));
 try{
 await page.goto(url);await page.waitForFunction(()=>document.querySelector('#source').value.includes('双环'));
 const run=async()=>{await page.click('#run');await page.waitForFunction(()=>!document.querySelector('#run').disabled);assert.match(await page.locator('#message').innerText(),/求解完成|计算完成/);};
 const download=async id=>{const event=page.waitForEvent('download');await page.click('#'+id);const file=await event,dest=path.join(output,file.suggestedFilename());await file.saveAs(dest);const b=fs.readFileSync(dest);downloads[id]={filename:file.suggestedFilename(),sha256:sha(b),bytes:b.length};return{path:dest,bytes:b};};
 await run();assert.equal(await page.locator('#nodes tr').count(),7);assert.equal(await page.locator('#pipes tr').count(),8);assert.equal(await page.locator('#warnings').innerText(),'');
 const model=await download('json'),reportFile=await download('report'),csv=await download('csv'),svg=await download('svg');const report=JSON.parse(reportFile.bytes);
 assert.equal(report.version,'1.0.0');assert.equal(report.engine_version,'2.3.5');assert.equal(report.analysis_complete,true);assert.equal(report.model.name,'双环街区供水示例（公开虚构）');
 assert.deepEqual(JSON.parse(model.bytes),report.model);assert.ok(report.max_continuity_residual_lps<1e-6);assert.ok(csv.bytes.toString().includes(String(report.pipes[0].flow_lps)));
 assert.ok(await page.evaluate(text=>new DOMParser().parseFromString(text,'image/svg+xml').querySelector('svg')!==null,svg.bytes.toString()));
 await page.locator('[data-pipe="P1"]').click();assert.equal(await page.inputValue('#pipe'),'P1');await page.locator('#diameter').fill('200');
 assert.equal(await page.locator('#diagram svg').count(),0);for(const id of['json','report','csv','svg'])assert.equal(await page.locator('#'+id).isDisabled(),true);await run();
 const changed=JSON.parse((await download('report')).bytes);assert.ok(changed.pipes.find(p=>p.id==='P1').flow_lps>report.pipes.find(p=>p.id==='P1').flow_lps);assert.match(await page.locator('#comparison').innerText(),/上一有效方案/);
 await page.setInputFiles('#file',model.path);assert.equal(await page.locator('#json').isDisabled(),true);await run();
 const restored=JSON.parse((await download('report')).bytes);assert.deepEqual(restored.model,report.model);assert.ok(Math.abs(restored.pipes[0].flow_lps-report.pipes[0].flow_lps)<1e-9);
 await page.locator('#source').fill('{"schema_version":1,"schema_version":2}');await page.click('#run');assert.match(await page.locator('#message').innerText(),/duplicate_json_key/);assert.equal(await page.locator('#json').isDisabled(),true);
 await page.locator('#restore').click();await run();
 const hard=structuredClone(report.model);for(const n of hard.nodes)if(n.type==='junction')n.demand_lps=1000;hard.pipes.forEach((p,i)=>{p.diameter_mm=i%2?3000:10;p.length_m=i%2?.1:100000;p.roughness=10;});
 await page.locator('#source').fill(JSON.stringify(hard));await page.click('#run');await page.waitForFunction(()=>!document.querySelector('#run').disabled);assert.match(await page.locator('#message').innerText(),/未收敛.*epanet_110/);assert.equal(await page.locator('#report').isDisabled(),true);
 // A delayed example response must not overwrite a newer manual edit.
 let release;const hold=new Promise(resolve=>release=resolve);await page.route('**/one-pipe.json',async route=>{await hold;await route.continue();});
 await page.locator('#single').click();await page.locator('#source').fill(JSON.stringify(report.model));release();await page.waitForTimeout(150);assert.deepEqual(JSON.parse(await page.inputValue('#source')),report.model);await page.unroute('**/one-pipe.json');
 await page.locator('#single').click();await page.waitForFunction(()=>document.querySelector('#source').value.includes('单管'));await run();
 const one=JSON.parse((await download('report')).bytes);assert.ok(Math.abs(one.pipes[0].headloss_m-.04356767852)<.00005);
 const low=structuredClone(one.model);low.nodes[1].elevation_m=101;await page.locator('#source').fill(JSON.stringify(low));await run();assert.match(await page.locator('#warnings').innerText(),/负压力/);
 await page.locator('#source').fill(JSON.stringify(one.model));await page.click('#run');await page.waitForFunction(()=>!document.querySelector('#run').disabled);assert.equal(await page.locator('#warnings').innerText(),'');
 // Edits and cancellation terminate the current worker, rather than accepting a late result.
 await page.locator('#run').click();await page.locator('#source').fill('{');await page.waitForTimeout(100);assert.equal(await page.locator('#diagram svg').count(),0);assert.equal(await page.locator('#json').isDisabled(),true);
 await page.locator('#source').fill(JSON.stringify(one.model));await run();await page.screenshot({path:path.join(output,'workbench.png'),fullPage:true});
 assert.deepEqual(errors,[]);assert.deepEqual(outside,[]);
 fs.writeFileSync(path.join(output,'verification.json'),JSON.stringify({passed:true,url,version:'1.0.0',engine_version:'2.3.5',actual_browser:'Chrome',model_calls:0,tests:['real WASM solve','diagram selection','numeric edits invalidate','changed hydraulics','four actual downloads','model reimport roundtrip','duplicate-key rejection','restore and error recovery','negative-pressure warning','actual non-convergence rejection','delayed-import freshness','edit-during-run cancellation'],outside_requests:outside,page_errors:errors,downloads},null,2));
 console.log(JSON.stringify({passed:true,output,downloads},null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
