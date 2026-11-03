const fs=require('node:fs');
exports.create=ctx=>{
 const engine=()=>import('../vendor/engine.mjs');
 const stored=()=>fs.existsSync(ctx.file('model-report.json'))?JSON.parse(fs.readFileSync(ctx.file('model-report.json'))):{};
 async function saveOriginal(bytes){const e=await engine(),before=await e.inspect(bytes);ctx.atomic('original.glb',bytes);ctx.atomic('model-report.json',JSON.stringify({before}));return{before,original:bytes.toString('base64')};}
 return{
  state:async()=>stored(),
  download:name=>['original.glb','optimized.glb','model-report.json'].includes(name)&&fs.existsSync(ctx.file(name))?fs.readFileSync(ctx.file(name)):null,
  async operate(p){
   if(p.op==='demo')return saveOriginal(Buffer.from(await(await engine()).fixture()));
   if(p.op==='import'){if(typeof p.data!=='string'||p.data.length>36*1024*1024)throw Error('模型数据无效');return saveOriginal(Buffer.from(p.data,'base64'));}
   if(p.op==='save-textures'){
    if(!fs.existsSync(ctx.file('original.glb'))||typeof p.data!=='string'||p.data.length>36*1024*1024)throw Error('请先导入模型，且处理结果不得超过25 MiB');
    const e=await engine(),bytes=Buffer.from(p.data,'base64'),before=await e.inspect(fs.readFileSync(ctx.file('original.glb'))),after=await e.inspect(bytes);if(before.nodes!==after.nodes||before.animations!==after.animations)throw Error('贴图处理改变了节点或动画数量，拒绝保存');
    const report={before,after,savedBytes:before.bytes-after.bytes,note:'用户明确选择缩放彩色贴图；这是有损的分辨率调整，原始文件保留'};ctx.atomic('optimized.glb',bytes);ctx.atomic('model-report.json',JSON.stringify(report,null,2));return{...report,optimized:bytes.toString('base64')};
   }
   if(p.op==='optimize'){
    if(!fs.existsSync(ctx.file('original.glb')))throw Error('请先导入模型');const r=await(await engine()).optimize(fs.readFileSync(ctx.file('original.glb')));ctx.atomic('optimized.glb',Buffer.from(r.bytes));const report={before:r.before,after:r.after,savedBytes:r.before.bytes-r.after.bytes,note:'采用去重、焊接与清理；不承诺所有模型都减小，也不承诺任意扩展均兼容'};ctx.atomic('model-report.json',JSON.stringify(report,null,2));return{...report,optimized:Buffer.from(r.bytes).toString('base64')};
   }
   if(p.op==='load')return{...stored(),...(fs.existsSync(ctx.file('original.glb'))?{original:fs.readFileSync(ctx.file('original.glb')).toString('base64')}:{}),...(fs.existsSync(ctx.file('optimized.glb'))?{optimized:fs.readFileSync(ctx.file('optimized.glb')).toString('base64')}: {})};
   throw Error('操作不受支持');
  }
 };
};
