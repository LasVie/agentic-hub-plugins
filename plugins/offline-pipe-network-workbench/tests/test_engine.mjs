import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parseModel,validateModel} from '../offline-pipe-network-workbench/web/network.js';
import {solveNetwork} from '../offline-pipe-network-workbench/web/hydraulics.js';
import {networkSVG,resultsCSV} from '../offline-pipe-network-workbench/web/presentation.js';
const base=new URL('../offline-pipe-network-workbench/web/',import.meta.url);
const wasmBinary=readFileSync(new URL('vendor/epanet/EpanetEngine.wasm',base));
const fixture=n=>parseModel(readFileSync(new URL(n+'.json',base),'utf8'));
const solve=m=>solveNetwork(m,{wasmBinary});
const near=(a,b,tolerance)=>assert.ok(Math.abs(a-b)<=tolerance,`${a} != ${b}`);
test('analytical H-W pipe, diameter law, units and reservoir-first input',async()=>{
 const m=fixture('one-pipe'),r=await solve(m);
 const h=10.67*100*.001**1.852/(100**1.852*.1**4.871);
 near(r.pipes[0].flow_lps,1,1e-7);near(r.pipes[0].headloss_m,h,h*.001);
 near(r.nodes.find(n=>n.id==='J').pressure_m,100-h,.0001);
 near(r.nodes.find(n=>n.id==='R').head_m,100,1e-8);
 assert.equal(r.analysis_complete,true);assert.deepEqual(r.warnings,[]);
 m.pipes[0].diameter_mm=200;const wider=await solve(m);
 near(wider.pipes[0].headloss_m,r.pipes[0].headloss_m/2**4.871,.000001);
 assert.ok(wider.nodes[1].pressure_m>r.nodes[1].pressure_m);
});
test('branch continuity and symmetric parallel paths; demand changes',async()=>{
 const m=fixture('one-pipe');m.nodes.push({id:'K',type:'junction',elevation_m:0,demand_lps:1,x:100,y:100});
 m.pipes.push({...m.pipes[0],id:'Q',to:'K'});const r=await solve(m);
 near(r.pipes[0].flow_lps,r.pipes[1].flow_lps,1e-8);near(r.nodes[0].demand_lps,-2,1e-7);
 m.nodes[1].demand_lps=2;const changed=await solve(m);near(changed.pipes[0].flow_lps,2,1e-7);near(changed.pipes[1].flow_lps,1,1e-7);
});
test('two-loop solution, continuity, energy balance and sensitivity',async()=>{
 const m=fixture('loop'),r=await solve(m);assert.equal(r.analysis_complete,true);
 assert.ok(r.max_continuity_residual_lps<1e-6);near(r.nodes[0].demand_lps,-16,1e-6);
 const flow=id=>r.pipes.find(p=>p.id===id).flow_lps;
 near(flow('P1'),flow('P2'),1e-6);near(flow('P5'),flow('P6'),1e-6);near(flow('P7'),0,1e-6);
 const signedLoss=p=>Math.sign(p.flow_lps)*p.headloss_m;
 const find=id=>r.pipes.find(p=>p.id===id);
 near(signedLoss(find('P1'))+signedLoss(find('P3'))-signedLoss(find('P4'))-signedLoss(find('P2')),0,1e-8);
 m.pipes.find(p=>p.id==='P1').diameter_mm=200;const changed=await solve(m);
 assert.ok(changed.pipes.find(p=>p.id==='P1').flow_lps>flow('P1'));
 assert.ok(changed.max_continuity_residual_lps<1e-6);
});
test('negative pressure is surfaced as actual engine warning, never called healthy',async()=>{
 const m=fixture('one-pipe');m.nodes[1].elevation_m=101;
 const r=await solve(m);assert.ok(r.nodes[1].pressure_m<0);assert.ok(r.warnings.some(w=>w.code===6&&w.message.includes('负压力')));
 assert.ok(resultsCSV(r).includes('负压力'));assert.equal(r.engine_version,'2.3.5');
});
test('actual engine non-convergence rejects the result, then a valid model recovers',async()=>{
 const m=fixture('loop');for(const n of m.nodes)if(n.type==='junction')n.demand_lps=1000;
 m.pipes.forEach((p,i)=>{p.diameter_mm=i%2?3000:10;p.length_m=i%2?.1:100000;p.roughness=10;});
 await assert.rejects(solve(m),e=>e.code==='epanet_110'&&e.message.includes('未收敛'));
 assert.equal((await solve(fixture('one-pipe'))).analysis_complete,true);
});
test('input limits, duplicate keys, unsupported fields, IDs and disconnection',()=>{
 const m=fixture('one-pipe');
 for(const text of ['{"x":1,"x":2}','{"x":1,"\\u0078":2}'])assert.throws(()=>parseModel(text),e=>e.code==='duplicate_json_key');
 for(const text of ['{"a":}', '[1,]', '{', '{}garbage'])assert.throws(()=>parseModel(text));
 assert.throws(()=>parseModel(' '.repeat(65537)),e=>e.code==='input_limit');
 let x=structuredClone(m);x.nodes[1].extra=true;assert.throws(()=>validateModel(x));
 x=structuredClone(m);x.nodes[1].id='=bad';assert.throws(()=>validateModel(x));
 x=structuredClone(m);x.nodes.push({id:'K',type:'junction',elevation_m:0,demand_lps:1,x:0,y:0});assert.throws(()=>validateModel(x),e=>e.code==='disconnected_model');
 x=structuredClone(m);x.pipes[0].diameter_mm=0;assert.throws(()=>validateModel(x));
 x=structuredClone(m);x.nodes[1].demand_lps=Infinity;assert.throws(()=>validateModel(x));
 x=structuredClone(m);x.pipes[0].length_m='100';assert.throws(()=>validateModel(x));
});
test('exports preserve full precision/model and escape text safely',async()=>{
 const m=fixture('one-pipe');m.name='=公开示例 <script>alert(1)</script> & "引用"';const r=await solve(m);
 const copy=JSON.parse(JSON.stringify(r));assert.deepEqual(copy.model,JSON.parse(JSON.stringify(m)));
 assert.equal(copy.pipes[0].flow_lps,r.pipes[0].flow_lps);
 const svg=networkSVG(r);assert.ok(svg.includes('&lt;script&gt;'));assert.ok(!svg.includes('<script>'));assert.ok(svg.includes('1.0.0'));
 const csv=resultsCSV(r);assert.ok(csv.includes("'=公开示例"));assert.ok(csv.includes(String(r.pipes[0].flow_lps)));
});
