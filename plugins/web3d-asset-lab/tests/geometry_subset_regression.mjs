/** Actual GLB regression for the 1.0.5 source subset; no GUI or host acceptance claimed. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';

const [root,oldFile,output,deps]=process.argv.slice(2);
if(!deps)throw Error('Usage: node geometry_subset_regression.mjs PAYLOAD OLD_ENGINE OUTPUT BUILD_DEPS');
fs.mkdirSync(output,{recursive:true});
const current=await import(pathToFileURL(path.join(root,'vendor/engine.mjs')));
const old=await import(pathToFileURL(oldFile));
const core=await import(pathToFileURL(path.join(deps,'node_modules/@gltf-transform/core/dist/index.js')));
const validator=(await import(pathToFileURL(path.join(deps,'node_modules/gltf-validator/index.js')))).default;
const results=[];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function check(name,condition,detail={}){results.push({name,passed:!!condition,...detail});assert.ok(condition,name);}
const native=new core.NodeIO();
const fixture=await current.fixture();
check('self-generated fixture remains byte identical',sha(fixture)===sha(await old.fixture()),{bytes:fixture.length,sha256:sha(fixture)});
const doc=await native.readBinary(fixture);
const buf=doc.getRoot().listBuffers()[0];
const node=doc.getRoot().listNodes()[0];
const time=doc.createAccessor('timeline').setType('SCALAR').setArray(new Float32Array([0,1])).setBuffer(buf);
const translation=doc.createAccessor('translation').setType('VEC3').setArray(new Float32Array([0,0,0,1,0,0])).setBuffer(buf);
const sampler=doc.createAnimationSampler().setInput(time).setOutput(translation).setInterpolation('LINEAR');
const channel=doc.createAnimationChannel().setTargetNode(node).setTargetPath('translation').setSampler(sampler);
doc.createAnimation('movement').addSampler(sampler).addChannel(channel);
const animated=await native.writeBinary(doc);
const fixtures=[['demo',fixture],['animated',animated]];
for(const [name,bytes]of fixtures){
 const before=await current.inspect(bytes);assert.deepEqual(before,await old.inspect(bytes));
 check(name+' inspection equals original engine',true,{before});
 const actual=await current.optimize(bytes),expected=await old.optimize(bytes);
 assert.deepEqual(actual.before,expected.before);assert.deepEqual(actual.after,expected.after);
 check(name+' optimization byte-identical to original',sha(actual.bytes)===sha(expected.bytes),{before_bytes:bytes.length,after_bytes:actual.bytes.length,sha256:sha(actual.bytes)});
 check(name+' preserves scene nodes and animations',actual.before.nodes===actual.after.nodes&&actual.before.animations===actual.after.animations,{nodes:actual.after.nodes,animations:actual.after.animations});
 const again=await current.optimize(actual.bytes),oldAgain=await old.optimize(expected.bytes);
 check(name+' second optimization matches original',sha(again.bytes)===sha(oldAgain.bytes));
 for(const [stage,data]of [['original',bytes],['optimized',actual.bytes]]){
  const result=await validator.validateBytes(new Uint8Array(data),{uri:name+'-'+stage+'.glb',maxIssues:100});
  fs.writeFileSync(path.join(output,name+'-'+stage+'-validator.json'),JSON.stringify(result,null,2)+'\n');
  check(name+' '+stage+' GLB validator has zero errors',result.issues.numErrors===0,{errors:result.issues.numErrors,warnings:result.issues.numWarnings,infos:result.issues.numInfos});
  fs.writeFileSync(path.join(output,name+'-'+stage+'.glb'),data);
 }
}
function changedJSON(fn){
 const b=Buffer.from(fixture),length=b.readUInt32LE(12),json=JSON.parse(b.subarray(20,20+length).toString('utf8'));fn(json);
 const text=Buffer.from(JSON.stringify(json)),pad=Buffer.alloc((4-text.length%4)%4,32),body=Buffer.concat([text,pad]);
 const header=Buffer.from(b.subarray(0,20));header.writeUInt32LE(20+body.length+b.length-20-length,8);header.writeUInt32LE(body.length,12);
 return Buffer.concat([header,body,b.subarray(20+length)]);
}
const altered=(offset,value)=>{const b=Buffer.from(fixture);b.writeUInt32LE(value,offset);return b;};
const invalid=[
 ['truncated header',new Uint8Array(12)],['wrong magic',altered(0,0)],['unsupported GLB version',altered(4,1)],
 ['incorrect total length',altered(8,fixture.length+4)],['oversized JSON chunk',altered(12,fixture.length)],['wrong JSON chunk type',altered(16,0)],
 ['malformed JSON',(()=>{const b=Buffer.from(fixture);b[20]=33;return b;})()],
 ['external buffer URI',changedJSON(j=>j.buffers[0].uri='https://example.invalid/model.bin')],
 ['external image URI',changedJSON(j=>j.images[0].uri='https://example.invalid/image.png')],
 ['required decoder extension',changedJSON(j=>j.extensionsRequired=['KHR_draco_mesh_compression'])],
 ['too many nodes',changedJSON(j=>j.nodes=Array.from({length:5001},()=>({})))],
 ['accessor count above bound',changedJSON(j=>j.accessors[0].count=1000001)],
 ['file above 25 MiB',new Uint8Array(25*1024*1024+1)]
];
for(const [name,bytes]of invalid){
 for(const method of ['inspect','optimize']){
  let a,b;try{await current[method](bytes);}catch(e){a=e.message;}try{await old[method](bytes);}catch(e){b=e.message;}
  check(name+' rejected identically by '+method,!!a&&a===b,{error:a});
 }
}
const probe="const e=await import(process.argv[1]); const b=await e.fixture(); const r=await e.optimize(b); if(!r.bytes.length)throw Error('empty output'); console.log(JSON.stringify({before:r.before,after:r.after}));";
const strict=spawnSync(process.execPath,['--disallow-code-generation-from-strings','--input-type=module','-e',probe,pathToFileURL(path.join(root,'vendor/engine.mjs')).href],{encoding:'utf8'});
check('actual new engine initializes and optimizes with Node string-code generation disabled',strict.status===0,{stdout:strict.stdout.trim(),stderr:strict.stderr.trim()});
for(const file of ['vendor/model-view.mjs','vendor/texture-resize.mjs']){
 const data=fs.readFileSync(path.join(root,file));check(file+' retained bytes recorded',true,{sha256:sha(data),bytes:data.length});
}
fs.writeFileSync(path.join(output,'engine-regression-results.json'),JSON.stringify({version:'1.0.5',type:'actual Node engine and validator, not GUI',checks:results.length,passed:results.filter(x=>x.passed).length,results,limitations:['New local WorkSwarm GUI import/prompt and browser Canvas/Three.js retest remain pending.','Fixture animation data is validated and preserved; playback is not claimed.','No arbitrary extension, OS or fixed compression-ratio guarantee.']},null,2)+'\n');
console.log(JSON.stringify({checks:results.length,passed:results.filter(x=>x.passed).length,output}));
