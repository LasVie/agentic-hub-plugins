const fs=require('node:fs'),path=require('node:path'),{fork}=require('node:child_process');
exports.create=ctx=>{
 const projectFile=ctx.file('current-project.json');let project=fs.existsSync(projectFile)?JSON.parse(fs.readFileSync(projectFile)).project:'demo';
 function worker(p){return new Promise((resolve,reject)=>{const child=fork(path.join(__dirname,'pg-worker.cjs'),[],{stdio:['ignore','ignore','pipe','ipc'],execArgv:['--max-old-space-size=512']});let done=false;
  const timer=setTimeout(()=>{done=true;child.kill('SIGKILL');reject(Error('数据库操作超过15秒，已中止专用子进程；请重新查询核对状态'));},15000);
  child.on('message',r=>{if(done)return;done=true;clearTimeout(timer);r.ok?resolve(r):reject(Error(r.error));});
  child.on('error',e=>{if(!done){done=true;clearTimeout(timer);reject(e);}});child.on('exit',code=>{if(!done){done=true;clearTimeout(timer);reject(Error('数据库子进程提前退出：'+code));}});child.send({...p,dataDir:ctx.dataDir,project});
 });}
 return{
  state:async()=>({project,projects:fs.readdirSync(ctx.dataDir).filter(s=>s.startsWith('db-')).map(s=>s.slice(3)),history:fs.existsSync(ctx.file('query-history.json'))?JSON.parse(fs.readFileSync(ctx.file('query-history.json'))):[]}),
  download:name=>/^database-[a-zA-Z0-9_-]+\.tar\.gz$/.test(name)&&fs.existsSync(ctx.file(name))?fs.readFileSync(ctx.file(name)):null,
  async operate(p){
   if(p.project){project=ctx.allowed(p.project);ctx.atomic('current-project.json',JSON.stringify({project}));}
   if(!['sample','query','schema','export'].includes(p.op))throw Error('操作不受支持');
   const start=performance.now(),result=await worker(p);result.elapsedMs=Math.round(performance.now()-start);result.project=project;
   if(p.op==='query'||p.op==='sample'){const h=fs.existsSync(ctx.file('query-history.json'))?JSON.parse(fs.readFileSync(ctx.file('query-history.json'))):[];h.push({at:new Date().toISOString(),project,sql:p.op==='sample'?'载入示例数据':p.sql,totalReturned:result.result.totalReturned});ctx.atomic('query-history.json',JSON.stringify(h.slice(-50)));}
   return result;
  }
 };
};
