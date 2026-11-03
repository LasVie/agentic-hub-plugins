import{$,api,action,display,table,download,init,message,metric}from'./common.js';
function results(r){const d=r.result;$('#metrics').replaceChildren(metric('当前数据库',r.project),metric('实际返回行数',d.totalReturned??0),metric('耗时',r.elapsedMs+' ms'));if(d.rows){table($('#rows'),d.rows,d.fields.map(f=>f.name));display($('#details'),{字段:d.fields,受影响行数:d.affectedRows,显示已截断:d.truncated});}message(d.truncated?'结果已限制显示前300行；完整SQL仍在独立数据库内执行':'PostgreSQL实际执行完成，数据已持久化');}
$('#sample').onclick=()=>action(async()=>results(await api('sample',{project:$('#project').value})));
$('#run').onclick=()=>action(async()=>results(await api('query',{project:$('#project').value,sql:$('#sql').value})));
$('#schema').onclick=()=>action(async()=>results(await api('schema',{project:$('#project').value})));
$('#export').onclick=()=>action(async()=>{const r=await api('export',{project:$('#project').value});download(r.result.filename);message('数据库实际快照已生成：'+r.result.filename);});
const s=await init();$('#project').value=s.project||'demo';if(s.history?.length)display($('#details'),s.history.slice(-5));
