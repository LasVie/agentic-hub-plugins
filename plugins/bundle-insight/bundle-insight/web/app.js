import{$,api,action,display,table,download,init,message,metric,fileBytes}from'./common.js';
let current=null;
async function refresh(){const s=await(await fetch('/api/state')).json();for(const sel of [$('#before'),$('#after')]){const old=sel.value;sel.replaceChildren();for(const name of s.snapshots){const o=document.createElement('option');o.value=o.textContent=name;sel.append(o);}if(s.snapshots.includes(old))sel.value=old;}if(s.snapshots.length>1)$('#after').value=s.snapshots.at(-1);}
function show(r,name){current=name;$('#metrics').replaceChildren(metric('实际模块数',r.summary.modules),metric('构建模块体积',r.summary.renderedLength+' B'),metric('gzip模块合计',r.summary.gzipLength+' B'));table($('#modules'),r.modules.map(m=>({模块:m.module,构建字节:m.renderedLength,gzip字节:m.gzipLength})),['模块','构建字节','gzip字节']);$('#graph').src='/preview/'+r.report;message((r.message||'统计已载入')+'。'+r.summary.note);}
$('#build').onclick=()=>action(async()=>{const name=$('#name').value;const r=await api('build-demo',{name,large:$('#large').checked});show(r,name);await refresh();});
$('#import').onclick=()=>action(async()=>{const bytes=await fileBytes($('#stats-file'));const name=$('#name').value;const r=await api('import',{name,data:JSON.parse(new TextDecoder().decode(bytes))});show(r,name);await refresh();});
$('#load').onclick=()=>action(async()=>{const n=$('#after').value;if(!n)throw Error('请先构建或导入统计');show(await api('load',{name:n}),n);});
$('#compare').onclick=()=>action(async()=>{const r=await api('compare',{before:$('#before').value,after:$('#after').value});table($('#changes'),r.changes.map(x=>({模块:x.module,之前字节:x.before,之后字节:x.after,变化字节:x.delta})),['模块','之前字节','之后字节','变化字节']);message('比较完成；以同一统计口径的实际模块数据计算变化');});
$('#export').onclick=()=>{if(!current)return message('请先载入统计',true);download('report-'+current+'.html');};
await init();await refresh();
