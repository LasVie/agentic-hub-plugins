/* Actual upstream browser bundle exercised in a VM; browser worker tested separately. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.join(__dirname,'geojson-simplification-lab');
const ctx={console,setTimeout,clearTimeout,TextEncoder,TextDecoder,ArrayBuffer,Uint8Array};ctx.window=ctx;ctx.document={};vm.createContext(ctx);
for(const f of ['geometry.js','vendor/modules.js','vendor/mapshaper.js'])vm.runInContext(fs.readFileSync(path.join(root,'web',f),'utf8'),ctx);
const G=ctx.GeoLab;const plain=x=>JSON.parse(JSON.stringify(x));const tests=[];
async function test(name,fn){await fn();tests.push(name);}
function edges(r){return r.slice(1).map((p,i)=>[JSON.stringify(r[i]),JSON.stringify(p)].sort().join('|'));}
function area(r){return Math.abs(r.slice(1).reduce((s,p,i)=>s+r[i][0]*p[1]-p[0]*r[i][1],0)/2);}
(async()=>{
const raw=fs.readFileSync(path.join(root,'examples/adjacent-regions.geojson'),'utf8');let r;
await test('actual shared-boundary simplification, reduced vertices, equal shared arcs and area union',async()=>{
 r=await G.simplify(raw,20,ctx.mapshaper);assert(r.after.vertices<r.before.vertices);assert.equal(r.after.features,2);
 const a=r.result.features[0].geometry.coordinates[0],b=r.result.features[1].geometry.coordinates[0];
 const shared=a.slice(1).map((p,i)=>[a[i],p]).filter(e=>e.every(p=>p[0]>.5&&p[0]<1.5));const be=new Set(edges(b));assert(shared.length>1);for(const edge of shared)assert(be.has(edge.map(JSON.stringify).sort().join('|')));
 assert(Math.abs(area(a)+area(b)-2)<1e-9);assert.equal(r.version,'1.0.1');assert.equal(r.engine_version,'0.7.101');
});
await test('original immutable; IDs, FID and all Chinese properties preserved',()=>{const original=JSON.parse(raw);assert.deepEqual(plain(r.original),original);r.result.features.forEach((f,i)=>{assert.deepEqual(plain(f.properties),original.features[i].properties);assert.equal(f.id,original.features[i].id);});});
await test('GeoJSON export re-import and safe SVG geometry-only style',()=>{assert.deepEqual(plain(G.read(JSON.stringify(r.result))),plain(r.result));const svg=G.svg(r.result);assert(svg.includes('<svg'));assert(!svg.includes('invalid.example'));assert(!svg.includes('<script'));assert(!svg.includes('FID'));assert(!svg.includes('url('));});
await test('100 percent keeps original geometry vertices',async()=>{const x=await G.simplify(raw,100,ctx.mapshaper);assert.equal(x.after.vertices,x.before.vertices);});
await test('small island/hole losses are reported',async()=>{
 const ring=(cx,cy,rad,n)=>Array.from({length:n+1},(_,i)=>i===n?[cx+rad,cy]:[cx+rad*Math.cos(2*Math.PI*i/n),cy+rad*Math.sin(2*Math.PI*i/n)]);
 const x={type:'FeatureCollection',features:[{type:'Feature',id:'带孔多部件',properties:null,geometry:{type:'MultiPolygon',coordinates:[[ring(0,0,1,120),ring(.5,0,.001,20).reverse()],[ring(2,0,.001,20)]]}}]};const y=await G.simplify(JSON.stringify(x),1,ctx.mapshaper);assert(y.losses.length>0);assert.equal(y.result.features[0].geometry.type,'MultiPolygon');assert.equal(y.result.features[0].properties,null);
});
for(const [name,text,code] of [
 ['duplicate key','{"type":"FeatureCollection","type":"FeatureCollection","features":[]}','duplicate_key'],
 ['unsafe integer','{"x":9007199254740993}','unsafe_number'],['nonfinite','{"x":1e999}','unsafe_number'],['malformed','{"x":','invalid_json'],['empty collection','{"type":"FeatureCollection","features":[]}','unsupported_collection'],
 ['non-JSON whitespace','\u00a0{}','invalid_json'],
 ['input limit',' '.repeat(G.LIMITS.bytes+1),'input_limit'],['depth limit','['.repeat(30)+'0'+']'.repeat(30),'input_limit']])await test(name,()=>assert.throws(()=>G.read(text),e=>e.code===code));
for(const [name,mutate,code] of [
 ['unsupported point',x=>x.features[0].geometry={type:'Point',coordinates:[0,0]},'unsupported_geometry'],
 ['CRS extension',x=>x.crs={type:'name'},'unsupported_field'],
 ['open ring',x=>x.features[0].geometry.coordinates[0].pop(),'invalid_ring'],
 ['3D coordinate',x=>x.features[0].geometry.coordinates[0][0].push(9),'invalid_coordinate'],
 ['latitude range',x=>x.features[0].geometry.coordinates[0][0][1]=91,'invalid_coordinate'],
 ['duplicate ID',x=>x.features[1].id=x.features[0].id,'duplicate_id'],
 ['dateline',x=>x.features[0].geometry.coordinates[0][0][0]=-179.9,'dateline']])await test(name,()=>{const x=JSON.parse(raw);mutate(x);assert.throws(()=>G.read(JSON.stringify(x)),e=>e.code===code);});
await test('invalid percent never invokes engine',async()=>{for(const percent of [0,101,20.5,'20% -each evil'])await assert.rejects(G.simplify(raw,percent,{applyCommands(){throw Error('should not run')}}),e=>e.code==='invalid_percent');});
await test('engine failure blocks result',async()=>{await assert.rejects(G.simplify(raw,20,{applyCommands(){throw Error('failure')}}),e=>e.code==='engine_error');});
await test('feature loss is rejected',async()=>{await assert.rejects(G.simplify(raw,20,{applyCommands(){return {'output.geojson':'{"features":[]}'}}}),e=>e.code==='feature_loss');});
await test('prototype-like property is inert and retained',async()=>{const x=JSON.parse(raw);Object.defineProperty(x.features[0].properties,'__proto__',{value:{evil:true},enumerable:true});const y=await G.simplify(JSON.stringify(x),20,ctx.mapshaper);assert(y.result.features[0].properties.__proto__.evil);assert.equal({}.evil,undefined);});
console.log(JSON.stringify({passed:tests.length,tests,example:{before:plain(r.before),after:plain(r.after),losses:plain(r.losses)}} ,null,2));
})().catch(e=>{console.error(e);process.exit(1)});
