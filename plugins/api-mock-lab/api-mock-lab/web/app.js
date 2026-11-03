import{$,api,action,display,table,download,init,message,metric}from'./common.js';
let history=[];
function edit(spec){$('#definition').value=JSON.stringify(spec,null,2);}
$('#demo').onclick=()=>action(async()=>{const r=await api('demo');edit(r.spec);message(r.message);});
$('#save').onclick=()=>action(async()=>{const r=await api('save',{spec:JSON.parse($('#definition').value)});message(r.message);});
$('#start').onclick=()=>action(async()=>{const r=await api('start',{spec:JSON.parse($('#definition').value),scenario:$('#scenario').value});$('#mock-url').textContent=r.mockUrl;$('#route-count').textContent=r.routes;message(r.message+' · '+r.scenario);});
$('#stop').onclick=()=>action(async()=>{const r=await api('stop');$('#mock-url').textContent='未启动';message(r.message);});
$('#probe').onclick=()=>action(async()=>{const r=await api('probe',{path:$('#request-path').value,method:$('#method').value});$('#metrics').replaceChildren(metric('实际HTTP状态',r.status),metric('实际耗时',r.elapsedMs+' ms'));display($('#response'),r.body);history.unshift({方法:r.method,路径:r.path,状态:r.status,耗时:r.elapsedMs+' ms'});table($('#history'),history.slice(0,12),['方法','路径','状态','耗时']);message('真实请求已完成；结果来自当前运行的Mockoon服务');});
$('#export').onclick=()=>download('mock-project.json');
$('#import-api').onclick=()=>action(async()=>{const r=await api('import-openapi',{source:$('#openapi').value});edit(r.spec);message(r.message);});
const s=await init();if(s.spec)edit(s.spec);if(s.mockUrl)$('#mock-url').textContent=s.mockUrl;
