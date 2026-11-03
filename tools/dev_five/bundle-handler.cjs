const fs=require('node:fs'),path=require('node:path');
exports.create=ctx=>{
 const engine=()=>import('../vendor/visualizer/plugin/render-template/engine.mjs');
 const snapshots=()=>fs.readdirSync(ctx.dataDir).filter(s=>s.startsWith('snapshot-')&&s.endsWith('.json')).map(s=>s.slice(9,-5));
 function validate(d){
  if(!d||!d.tree||!d.nodeParts||!d.nodeMetas||typeof d.version!=='number'||JSON.stringify(d).length>10*1024*1024)throw Error('需要Rollup Visualizer的raw-data统计JSON，且不超过10 MiB');
  if(Object.keys(d.nodeParts).length>5000||Object.keys(d.nodeMetas).length>5000)throw Error('模块数量超过5000');
  for(const p of Object.values(d.nodeParts))for(const k of ['renderedLength','gzipLength','brotliLength'])if(!Number.isFinite(p[k])||p[k]<0)throw Error('模块大小必须是非负有限数');
  return d;
 }
 function modules(d){return Object.entries(d.nodeParts).map(([uid,p])=>({module:d.nodeMetas[p.metaUid]?.id||uid,renderedLength:p.renderedLength,gzipLength:p.gzipLength,brotliLength:p.brotliLength})).sort((a,b)=>b.renderedLength-a.renderedLength);}
 function summary(d){const m=modules(d);return{modules:m.length,renderedLength:m.reduce((n,x)=>n+x.renderedLength,0),gzipLength:m.reduce((n,x)=>n+x.gzipLength,0),brotliLength:m.reduce((n,x)=>n+x.brotliLength,0),note:'压缩值是逐模块独立计算之和，不等同于整个HTTP响应的压缩传输大小'};}
 async function save(name,data){ctx.allowed(name);validate(data);ctx.atomic('snapshot-'+name+'.json',JSON.stringify(data));const html=await(await engine()).render(data);ctx.atomic('report-'+name+'.html',html);return{name,summary:summary(data),modules:modules(data),report:'report-'+name+'.html',message:'真实统计与交互报告已保存'};}
 return{
  state:async()=>({snapshots:snapshots()}),
  download:name=>/^(report-[a-zA-Z0-9_-]+\.html|snapshot-[a-zA-Z0-9_-]+\.json)$/.test(name)&&fs.existsSync(ctx.file(name))?fs.readFileSync(ctx.file(name)):null,
  async operate(p){
   if(p.op==='build-demo'){const name=ctx.allowed(p.name||'baseline');return save(name,await(await engine()).buildFixture(path.join(ctx.dataDir,'build-'+name),p.large===true));}
   if(p.op==='import'){let data=p.data;if(typeof data==='string')data=JSON.parse(data);return save(ctx.allowed(p.name),data);}
   if(p.op==='load'){const name=ctx.allowed(p.name);return{summary:summary(validate(JSON.parse(fs.readFileSync(ctx.file('snapshot-'+name+'.json'))))),modules:modules(JSON.parse(fs.readFileSync(ctx.file('snapshot-'+name+'.json')))),report:'report-'+name+'.html'};}
   if(p.op==='compare'){
    const a=ctx.allowed(p.before),b=ctx.allowed(p.after),left=validate(JSON.parse(fs.readFileSync(ctx.file('snapshot-'+a+'.json')))),right=validate(JSON.parse(fs.readFileSync(ctx.file('snapshot-'+b+'.json'))));
    const merged=new Map();for(const m of modules(left)){const row=merged.get(m.module)||{module:m.module,before:0,after:0};row.before+=m.renderedLength;merged.set(m.module,row);}for(const m of modules(right)){const row=merged.get(m.module)||{module:m.module,before:0,after:0};row.after+=m.renderedLength;merged.set(m.module,row);}
    const changes=[...merged.values()].map(x=>({...x,delta:x.after-x.before})).sort((a,b)=>Math.abs(b.delta)-Math.abs(a.delta));const result={before:summary(left),after:summary(right),changes};ctx.atomic('comparison.json',JSON.stringify(result,null,2));return result;
   }
   throw Error('操作不受支持');
  }
 };
};
