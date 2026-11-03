const fs=require('node:fs'),http=require('node:http');
const E=require('../vendor/engine.cjs');
exports.create=ctx=>{
 let active=null,engine=null,environment=null;
 const saved=()=>fs.existsSync(ctx.file('mock.json'))?JSON.parse(fs.readFileSync(ctx.file('mock.json'),'utf8')):null;
 const demo=()=>({name:'商品目录联调',routes:[{method:'get',path:'/api/products',status:200,body:{items:[{id:1,name:'机械键盘',price:299},{id:2,name:'桌面音箱',price:459}],total:2}},{method:'get',path:'/api/products/:id',status:200,body:{id:1,name:'机械键盘',stock:12}},{method:'post',path:'/api/orders',status:201,body:{orderId:'DEMO-2026',message:'订单已创建'}}]});
 function validate(spec){
  if(!spec||!Array.isArray(spec.routes)||!spec.routes.length||spec.routes.length>50)throw Error('需要1至50条接口定义');
  for(const r of spec.routes){
   if(!['get','post','put','patch','delete','options','head'].includes(r.method))throw Error('HTTP方法不受支持');
   if(typeof r.path!=='string'||!/^\/[a-zA-Z0-9_/:.-]*$/.test(r.path)||r.path.length>200)throw Error('接口路径无效');
   if(!Number.isInteger(r.status)||r.status<200||r.status>599)throw Error('状态码需为200至599的整数');
   if(JSON.stringify(r.body).length>524288)throw Error('单条响应超过512 KiB');
  }
  return spec;
 }
 function makeEnv(spec,scenario){
  const env=E.BuildEnvironment({hasDefaultRoute:false,hasContentTypeHeader:true,hasCorsHeaders:true,port:0});
  env.name=String(spec.name||'接口联调').slice(0,80);env.proxyMode=false;env.proxyHost='';env.callbacks=[];env.data=[];env.hostname='127.0.0.1';
  env.routes=spec.routes.map(r=>{const x=E.BuildHTTPRoute(true,{endpoint:r.path.slice(1),body:JSON.stringify(scenario==='error'?{error:'模拟服务异常',code:'DEMO_ERROR'}:r.body)});x.method=r.method;x.responses[0].statusCode=scenario==='error'?503:r.status;x.responses[0].latency=scenario==='slow'?350:0;x.responses[0].disableTemplating=true;x.responses[0].callbacks=[];x.responses[0].headers=[{key:'Content-Type',value:'application/json; charset=utf-8'}];return x;});
  env.rootChildren=env.routes.map(r=>({type:'route',uuid:r.uuid}));return env;
 }
 async function stop(){if(active){await new Promise(resolve=>{active.close(resolve);active.closeAllConnections();});active=null;}engine=null;}
 return {
  state:async()=>({running:!!active,mockUrl:active?'http://127.0.0.1:'+active.address().port:null,spec:saved(),history:ctx.report}),
  close:stop,
  download:name=>name==='mock-project.json'&&fs.existsSync(ctx.file('mock.json'))?fs.readFileSync(ctx.file('mock.json')):null,
  async operate(p){
   if(p.op==='demo'){const spec=demo();ctx.atomic('mock.json',JSON.stringify(spec,null,2));return{spec,message:'示例接口已保存；尚未启动服务'};}
   if(p.op==='save'){const spec=validate(p.spec);ctx.atomic('mock.json',JSON.stringify(spec,null,2));return{spec,message:'接口定义已保存'};}
   if(p.op==='import-openapi'){
    if(typeof p.source!=='string'||p.source.length>1048576)throw Error('接口规范需为不超过1 MiB的文本');
    const original=E.parseYaml(p.source);let count=0;const seen=new WeakSet();
    function checkRefs(x,depth=0){if(!x||typeof x!=='object')return;if(seen.has(x))return;seen.add(x);if(++count>10000||depth>60)throw Error('接口规范嵌套或对象数量超出限制');for(const [key,v]of Object.entries(x)){if(key==='$ref'&&(typeof v!=='string'||!v.startsWith('#')))throw Error('禁止外部引用：请将所需定义内嵌到当前规范');checkRefs(v,depth+1);}}
    checkRefs(original);
    const env=await new E.OpenApiConverter().convertFromOpenAPI(p.source,0,{disableExternalRefs:true});
    if(!env)throw Error('无法识别规范；首版支持 Swagger 2.0 / OpenAPI 3.0，禁用外部引用');
    const spec=validate({name:env.name,routes:env.routes.filter(r=>r.type==='http').map(r=>{const reply=r.responses[0];let b;try{b=JSON.parse(reply.body||'{}');}catch{b={message:reply.body||''};}
     const sourcePath=Object.keys(original.paths||{}).find(s=>s.replace(/\{([^}]+)\}/g,(_,n)=>':'+n.replace(/-/g,''))==='/'+r.endpoint);
     const response=original.paths?.[sourcePath]?.[r.method]?.responses?.[String(reply.statusCode)];
     const media=response?.content?.['application/json'];
     if(media&&Object.hasOwn(media,'example'))b=media.example;
     else if(media?.examples){const first=Object.values(media.examples)[0];if(first&&Object.hasOwn(first,'value'))b=first.value;}
     return{method:r.method,path:'/'+r.endpoint,status:reply.statusCode,body:b};})});
    ctx.atomic('mock.json',JSON.stringify(spec,null,2));return{spec,message:'已导入首个响应；动态模板、回调、代理、外部文件及其规则不执行'};
   }
   if(p.op==='start'){
    const spec=validate(p.spec||saved());if(!['normal','slow','error'].includes(p.scenario||'normal'))throw Error('场景无效');
    await stop();environment=makeEnv(spec,p.scenario||'normal');engine=new E.MockoonServer(environment,{enableAdminApi:false,environmentDirectory:ctx.dataDir,envVarsPrefix:'DEV_FIVE_NO_ENV_'});
    engine.on('error',(_,error)=>ctx.report.push({error:String(error||_)}));active=http.createServer(engine.createRequestListener());
    await new Promise((resolve,reject)=>{active.once('error',reject);active.listen(0,'127.0.0.1',resolve);});ctx.atomic('mock.json',JSON.stringify(spec,null,2));
    return{mockUrl:'http://127.0.0.1:'+active.address().port,routes:spec.routes.length,scenario:p.scenario||'normal',message:'真实 Mockoon 接口服务已启动'};
   }
   if(p.op==='stop'){await stop();return{message:'接口服务已停止；定义保留'};}
   if(p.op==='probe'){
    if(!active)throw Error('请先启动接口服务');const route=String(p.path||'/api/products');if(!/^\/[a-zA-Z0-9_/?=&:.-]*$/.test(route)||route.startsWith('//'))throw Error('请求路径无效');
    const method=p.method||'GET';if(!['GET','POST','PUT','PATCH','DELETE','HEAD'].includes(method))throw Error('请求方法无效');
    const start=performance.now(),response=await fetch('http://127.0.0.1:'+active.address().port+route,{method,redirect:'error',signal:AbortSignal.timeout(5000)}),text=await response.text();
    const result={status:response.status,elapsedMs:Math.round(performance.now()-start),body:text.slice(0,1048576),path:route,method};ctx.report.push({at:new Date().toISOString(),...result});return result;
   }
   throw Error('操作不受支持');
  }
 };
};
