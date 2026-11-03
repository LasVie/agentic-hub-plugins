const fs=require('node:fs');
exports.create=ctx=>({
 state:async()=>({hasProject:fs.existsSync(ctx.file('site.json'))}),
 download:name=>({'website.html':'website.html','website.css':'website.css','page-project.json':'site.json'}[name]&&fs.existsSync(ctx.file({'page-project.json':'site.json'}[name]||name)))?fs.readFileSync(ctx.file({'page-project.json':'site.json'}[name]||name)):null,
 async operate(p){
  if(p.op==='load'){if(!fs.existsSync(ctx.file('site.json')))return{project:null};return{project:JSON.parse(fs.readFileSync(ctx.file('site.json'),'utf8')),summary:JSON.parse(fs.readFileSync(ctx.file('site-summary.json'),'utf8'))};}
  if(p.op==='save'){
   if(!p.project||!Array.isArray(p.project.pages)||JSON.stringify(p.project).length>4*1024*1024)throw Error('无效的GrapesJS工程，或超过4 MiB');
   if(typeof p.html!=='string'||typeof p.css!=='string'||p.html.length+p.css.length>4*1024*1024)throw Error('HTML/CSS无效或超过限制');
   const summary={pages:p.project.pages.length,htmlBytes:Buffer.byteLength(p.html),cssBytes:Buffer.byteLength(p.css),savedAt:new Date().toISOString()};
   ctx.atomic('site.json',JSON.stringify(p.project,null,2));ctx.atomic('site-summary.json',JSON.stringify(summary));
   ctx.atomic('website.css',p.css);ctx.atomic('website.html','<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>网页搭建台导出</title><style>'+p.css+'</style><body>'+p.html+'</body></html>');
   return{summary,message:'可继续编辑的工程与HTML/CSS已保存；导出文件在当前项目中'};
  }
  throw Error('操作不受支持');
 }
});
